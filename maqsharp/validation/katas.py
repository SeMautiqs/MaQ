"""Differential testing of MaQ# against the Q# simulator on the Quantum Katas.

For each exercise of the selected katas, the reference solution (Solution.qs) is
called by generated test operations: one for each computational basis state of
its input qubits, plus the same inputs in the Hadamard basis (H on every qubit
before and after the call), which also exposes relative phases. Each test
measures all the qubits and returns an Int that encodes the measurements and
the value returned by the exercise. The exact distribution computed by MaQ# is
compared with the frequencies observed in the simulator, as in validate.py.

Exercises whose parameters are not qubits or qubit arrays, or whose result is
not Unit, Bool, Result or Int, are skipped.

Usage:  python3 validation/katas.py KATAS_DIR [shots] [kata ...]
where KATAS_DIR is the katas/content folder of https://github.com/microsoft/qsharp.
Requires the maude binary in the PATH, MAUDE_LIB pointing to its prelude, and qdk.
"""
import math, os, re, subprocess, sys, warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("QSHARP_PYTHON_TELEMETRY", "none")
from qdk import qsharp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import num, seeded_run  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARRAY_LEN = 2      # length of qubit-array parameters
MAX_QUBITS = 4     # inputs are enumerated exhaustively up to this many qubits

SELECTED = ["single_qubit_gates", "multi_qubit_gates", "multi_qubit_systems",
            "preparing_states", "single_qubit_measurements", "multi_qubit_measurements",
            "teleportation", "superdense_coding", "random_numbers", "deutsch_algo",
            "deutsch_jozsa", "oracles", "marking_oracles", "grovers_search", "qec_shor",
            "nonlocal_games", "distinguishing_states"]

SIG = re.compile(r"(operation|function)\s+(\w+)\s*\(([^)]*)\)\s*:\s*(\([^)]*\)|[\w\[\]]+)")
SCALAR = {"Bool": "({} ? 1 | 0)", "Result": "({} == One ? 1 | 0)"}


def signature(placeholder, solution):
    """Name, parameter types and result type of the exercise."""
    m = SIG.search(open(placeholder).read())
    if not m:
        return None
    name = m.group(2)
    for m in SIG.finditer(solution):
        if m.group(2) == name:
            params = [p.split(":") for p in m.group(3).split(",") if p.strip()]
            return m.group(1), name, [t.strip() for _, t in params], m.group(4)
    return None


def rtypes(rtype):
    """Component types of the result, or None if it is not supported."""
    if rtype.startswith("("):
        comps = [c.strip() for c in rtype[1:-1].split(",")]
        return comps if all(c in SCALAR for c in comps) else None
    return [] if rtype == "Unit" else [rtype] if rtype in ("Bool", "Result", "Int") else None


def tests(name, ptypes, rtype, alen):
    """Q# source of the generated test operations, and their names."""
    regs, args, n = [], [], 0
    for i, t in enumerate(ptypes):
        if t == "Qubit":
            regs.append((f"q{i}", [f"q{i}"]))
            args.append(f"q{i}")
            n += 1
        else:
            regs.append((f"a{i}", [f"a{i}[{j}]" for j in range(alen)]))
            args.append(f"a{i}")
            n += alen
    qubits = [q for _, qs in regs for q in qs]
    comps = rtypes(rtype)
    src, names = [], []
    for probe in ("Z", "X"):
        for b in range(2 ** n):
            op = f"MaqTest{probe}{b}"
            names.append(op)
            body = []
            for v, qs in regs:
                body.append(f"use {v} = Qubit();" if len(qs) == 1 and qs[0] == v
                            else f"use {v} = Qubit[{alen}];")
            body += [f"X({q});" for k, q in enumerate(qubits) if b >> k & 1]
            if probe == "X":
                body += [f"H({q});" for q in qubits]
            call = f"Kata.{name}({', '.join(args)})"
            if len(comps) == 1:
                body.append(f"let r0 = {call};")
            elif comps:
                body.append(f"let ({', '.join(f'r{j}' for j in range(len(comps)))}) = {call};")
            else:
                body.append(f"{call};")
            if probe == "X":
                body += [f"H({q});" for q in qubits]
            body.append("mutable code = 0;")
            for k, q in enumerate(qubits):
                body.append(f"if M({q}) == One {{ set code += {2 ** k}; }}")
                body.append(f"Reset({q});")
            enc = " + ".join(f"{2 ** (n + j)} * " + SCALAR.get(c, "{}").format(f"r{j}")
                             for j, c in enumerate(comps))
            body.append(f"return code + {enc};" if comps else "return code;")
            src.append(f"operation {op}() : Int {{\n    " + "\n    ".join(body) + "\n}\n")
    return "\n".join(src), names


def maude_dists(path, ops):
    cmds = [f"open {path}"] + [f"dist {op} depth 100000" for op in ops] + ["q"]
    try:
        out = subprocess.run(
            ["maude", "-no-banner", "-no-advise", "-allow-files", "qsharp-io.maude"],
            input="\n".join(cmds) + "\n", capture_output=True, text=True, cwd=ROOT,
            timeout=600, env={**os.environ, "PWD": ROOT}).stdout
    except subprocess.TimeoutExpired:
        return "timeout"
    if "Program loaded" not in out:
        return "load: " + (out.split("Error:")[1].split("\n")[0].strip() if "Error:" in out else "?")
    blocks = out.split("Q#> ")[2:]
    res = []
    for b in blocks:
        b = re.sub(r"\n\s{4,}", " ", b)
        if "result:" not in b and "stuck" not in b:
            continue
        d = {}
        for line in b.splitlines():
            m = re.match(r"\s*result: (.*?)\s+prob: (.*)$", line)
            if m:
                d[m.group(1).strip()] = num(m.group(2))
            if "stuck" in line or "unexplored" in line:
                d["<stuck>"] = d.get("<stuck>", 0) + num(line.split(":")[-1])
        res.append(d)
    return res if len(res) == len(ops) else "incomplete output"


def agree(exact, counts, shots):
    if "<stuck>" in exact:
        return False, None
    worst = 0.0
    for v in set(exact) | set(counts):
        p, k = exact.get(v, 0.0), counts.get(v, 0)
        if p <= 1e-12 or p >= 1 - 1e-12:
            if (p <= 1e-12 and k > 0) or (p >= 1 - 1e-12 and k < shots):
                return False, math.inf
            continue
        worst = max(worst, abs(k - shots * p) / math.sqrt(shots * p * (1 - p)))
    return worst <= 4, worst


def check(sol_path, shots):
    exdir = os.path.dirname(sol_path)
    placeholder = os.path.join(exdir, "Placeholder.qs")
    solution = open(sol_path).read()
    sig = signature(placeholder, solution) if os.path.exists(placeholder) else None
    if not sig:
        return "skipped: no signature"
    kind, name, ptypes, rtype = sig
    if kind != "operation" or not ptypes or any(t not in ("Qubit", "Qubit[]") for t in ptypes) \
            or rtypes(rtype) is None:
        return "skipped: signature"
    for alen in (ARRAY_LEN, ARRAY_LEN + 1):
        res = check_len(solution, name, ptypes, rtype, alen, shots)
        if not res.startswith("skipped: simulator (Error: index out of range"):
            return res
    return res


def check_len(solution, name, ptypes, rtype, alen, shots):
    nq = sum(1 if t == "Qubit" else alen for t in ptypes)
    if nq > MAX_QUBITS + (alen - ARRAY_LEN):
        return "skipped: too many qubits"
    src, ops = tests(name, ptypes, rtype, alen)
    # Q# simulator first: exercises that need other input sizes are skipped
    try:
        qsharp.init()
        qsharp.eval(solution)
        qsharp.eval(src)
        observed = []
        for op in ops:
            counts = {}
            for r in seeded_run(f"{op}()", shots):
                counts[str(r)] = counts.get(str(r), 0) + 1
            observed.append(counts)
    except Exception as e:  # noqa: BLE001
        return "skipped: simulator (" + str(e).split("\n")[0][:40] + ")"
    path = os.path.join(ROOT, f"tmpkata_{os.getpid()}.qs")
    with open(path, "w") as f:
        f.write(solution + "\n" + src)
    try:
        dists = maude_dists(path, ops)
    finally:
        os.unlink(path)
    if isinstance(dists, str):
        return "MaQ# " + dists
    worst = 0.0
    for exact, counts in zip(dists, observed):
        ok, z = agree(exact, counts, shots)
        if z is None:
            return "MaQ# stuck (unsupported operation)"
        if not ok:
            return "DISAGREE"
        worst = max(worst, z)
    return f"agree ({len(ops)} tests, max|z| {worst:.2f})"


def main():
    kdir = sys.argv[1]
    shots = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    katas = sys.argv[3:] or SELECTED
    agreeing = testable = total = 0
    for k in katas:
        for ex in sorted(os.listdir(os.path.join(kdir, k))):
            sol = os.path.join(kdir, k, ex, "Solution.qs")
            if os.path.exists(sol):
                r = check(sol, shots)
                total += 1
                testable += not r.startswith("skipped")
                agreeing += r.startswith("agree")
                print(f"{k}/{ex:32} {r}", flush=True)
    print(f"\n{agreeing}/{testable} testable exercises agree with the simulator "
          f"({total - testable} of {total} skipped)")


if __name__ == "__main__":
    main()
