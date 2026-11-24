"""Validation of the Q#-in-Maude semantics against the official Q# simulator.

For each operation:
  - it is run N times in the Q# simulator (qdk package);
  - its EXACT distribution is computed in Maude with the dist command;
  - for each result, the observed frequency k/N is compared with the
    probability p by means of z = (k - N p) / sqrt(N p (1 - p)).
A case fails if some |z| > 4, if a result with p = 0 shows up, or if one with
p = 1 is missing.

Usage:  python3 validation/validate.py [shots]
Requires the maude binary in the PATH and MAUDE_LIB pointing to its prelude.
"""
import math, os, re, subprocess, sys, warnings
from fractions import Fraction

warnings.filterwarnings("ignore")
os.environ.setdefault("QSHARP_PYTHON_TELEMETRY", "none")
from qdk import qsharp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 4000

# (file, namespace prefix for Q#, operations)
CASES = [
    ("examples/bell.qs", "Demo.", ["Main"]),
    ("examples/ghz.qs", "", ["Main"]),
    ("examples/random.qs", "", ["CountOnes"]),
    ("examples/rus.qs", "", ["UntilOne", "Count"]),
    ("examples/functors.qs", "Functors.",
     ["AdjointUndo", "AdjointLoop", "CtlX", "Toffoli", "CtlUser", "WithinApply",
      "TPhase", "TAdjoint"]),
    ("validation/validation.qs", "Validation.",
     ["Biased", "Biased3", "TwoQubitPhase", "ControlledPhase", "TeleportCheck",
      "FirstAttempt"]),
    ("validation/algorithms.qs", "Algorithms.",
     ["DJConstant", "DJBalanced", "BernsteinVazirani", "Grover2", "Grover3",
      "SuperdenseAll", "EntanglementSwapping"]),
    ("validation/extensions.qs", "Extensions.",
     ["BellTuple", "TuplePatterns", "Arrays", "EachQubit", "OperationArgument",
      "PauliParities", "ControlledOnInt", "FailNotReached", "Shadowing"]),
]


def norm(v):
    """Normalizes a Maude or Python value into a common string."""
    s = str(v).strip()
    s = s.replace("(true ).QBool", "True").replace("(false ).QBool", "False")
    s = s.replace("Result.", "").replace("tup", "").replace("arr", "")
    s = s.replace("[", "(").replace("]", ")").replace(" ", "").replace("noE", "")
    s = re.sub(r"\btrue\b", "True", re.sub(r"\bfalse\b", "False", s))
    return {"unit": "()", "None": "()"}.get(s, s)


def num(expr):
    """Numerically evaluates a probability printed by Maude."""
    e = expr.replace(".+", "+").replace(".*", "*").replace("./", "/")
    e = e.replace("Sqrt", "math.sqrt")
    e = re.sub(r"(\d+)/(\d+)", r"(\1/\2)", e)
    return float(eval(e, {"math": math}))


def maude_dists():
    cmds = []
    for f, _, ops in CASES:
        cmds.append(f"open {f}")
        cmds += [f"dist {op}" for op in ops]
    cmds.append("q")
    out = subprocess.run(
        ["maude", "-no-banner", "-no-advise", "-allow-files", "qsharp-io.maude"],
        input="\n".join(cmds) + "\n", capture_output=True, text=True, cwd=ROOT,
        timeout=1800).stdout
    # each answer follows a prompt; lines split by Maude are joined
    blocks = out.split("Q#> ")[1:]
    res = []
    for b in blocks:
        b = re.sub(r"\n\s{4,}", " ", b)
        if "result:" not in b:
            continue
        d, rest = {}, Fraction(0)
        for line in b.splitlines():
            m = re.match(r"\s*result: (.*?)\s+prob: (.*)$", line)
            if m:
                d[norm(m.group(1))] = num(m.group(2))
            m = re.match(r"\s*unexplored.*: (.*)$", line)
            if m:
                rest = num(m.group(1))
            if "stuck" in line:
                d["<stuck>"] = num(line.split(":")[-1])
        res.append((d, float(rest)))
    return res


def main():
    dists = maude_dists()
    rows, i, all_ok = [], 0, True
    for f, ns, ops in CASES:
        qsharp.init()
        qsharp.eval(open(os.path.join(ROOT, f)).read())
        for op in ops:
            exact, rest = dists[i]
            i += 1
            shots = qsharp.run(f"{ns}{op}()", shots=SHOTS)
            counts = {}
            for r in shots:
                counts[norm(r)] = counts.get(norm(r), 0) + 1
            worst, ok = 0.0, "<stuck>" not in exact
            for v in set(exact) | set(counts):
                p, k = exact.get(v, 0.0), counts.get(v, 0)
                if p <= 1e-12 or p >= 1 - 1e-12:
                    if (p <= 1e-12 and k > 0) or (p >= 1 - 1e-12 and k < SHOTS):
                        ok = False
                    continue
                z = (k - SHOTS * p) / math.sqrt(SHOTS * p * (1 - p))
                worst = max(worst, abs(z))
            ok = ok and worst <= 4
            all_ok &= ok
            tv = 0.5 * sum(abs(exact.get(v, 0) - counts.get(v, 0) / SHOTS)
                           for v in set(exact) | set(counts))
            show = ", ".join(f"{v}: {exact[v]:.4f}" for v in sorted(exact))
            obs = ", ".join(f"{v}: {counts[v] / SHOTS:.4f}" for v in sorted(counts))
            rows.append((f"{os.path.basename(f)}:{op}", show, obs, worst, tv, rest, ok))
    w = max(len(r[0]) for r in rows)
    print(f"{'case':<{w}}  {'max|z|':>6}  {'TV':>6}  ok   Maude (exact)  |  Q# ({SHOTS} shots)")
    for name, show, obs, z, tv, rest, ok in rows:
        extra = f" (+{rest:.1e} unexplored)" if rest else ""
        print(f"{name:<{w}}  {z:6.2f}  {tv:6.4f}  {'yes' if ok else 'NO':<3}  {show}{extra}  |  {obs}")
    print("\nALL CASES PASS" if all_ok else "\nTHERE ARE DISCREPANCIES")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
