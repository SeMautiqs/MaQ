"""Comparison of MaQ# with QRAT on the examples of QRAT's artifact.

QRAT (https://github.com/canhminhdo/qrat) must be built beforehand. The script
runs QRAT on teleport.qw, loop.qw, entangleswap.qw and grover-N.qw from its
artifact folder, and MaQ# on the same programs written in Q#: teleport.qs (with
a symbolic input state), perf/qrat/loop.qs, perf/qrat/entangleswap.qs, and
Grover programs translated gate by gate from grover-N.qw.

Usage:  python3 perf/compare_qrat.py QRAT_BINARY QRAT_ARTIFACT_DIR [time_limit] [grover sizes...]
Writes perf/qrat-results.md.
"""
import os, re, resource, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QRAT, ART = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
LIMIT = float(sys.argv[3]) if len(sys.argv) > 3 else 300.0
SIZES = [int(n) for n in sys.argv[4:]] or [5, 10, 15, 20]


def unlimited_stack():
    # raise the stack limit as far as the system allows (on macOS the hard limit
    # may be reported as unlimited but cannot be used as the soft limit)
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    for lim in (hard, 2**30, 2**28, 64 * 2**20 - 2**12):
        if lim == resource.RLIM_INFINITY or hard == resource.RLIM_INFINITY or lim <= hard:
            try:
                resource.setrlimit(resource.RLIMIT_STACK, (lim, hard))
                return
            except (ValueError, OSError):
                pass


def timed(cmd, inp, cwd):
    t0 = time.monotonic()
    try:
        out = subprocess.run(cmd, input=inp, capture_output=True, text=True, cwd=cwd,
                             timeout=LIMIT, preexec_fn=unlimited_stack,
                             env={**os.environ, "PWD": cwd}).stdout
    except subprocess.TimeoutExpired:
        return None, "timeout"
    return time.monotonic() - t0, re.sub(r"\x1b\[[0-9;]*m", "", out)


def qrat(name):
    t, out = timed([QRAT], f"load {name}.qw .\nquit .\n", ART)
    if t is None:
        return "timeout"
    st = re.search(r"states: (\d+)", out)
    res = re.findall(r"Result: (\S+)|Probability of basis state \S+ in state \d+ is (\S+)", out)
    vals = [a or b for a, b in res]
    return f"{t:.2f} s, {st.group(1) if st else '?'} states, {' / '.join(vals)}"


def maq(cmds, extra=()):
    t, out = timed(["maude", "-no-banner", "-no-advise", "-allow-files", *extra, "qsharp-io.maude"],
                   "\n".join(cmds + ["q"]) + "\n", ROOT)
    if t is None:
        return "timeout"
    out = re.sub(r"prob:\s*\n\s*", "prob: ", out)
    keep = [re.sub(r"\s+", " ", l.strip()) for l in out.splitlines()
            if re.match(r"\s*(holds|does NOT|reachable|unexplored|result:)", l)]
    return f"{t:.2f} s: " + "; ".join(keep)


def grover_qs(n):
    src = open(os.path.join(ART, f"grover-{n}.qw")).read()
    body = src[src.index("atomic {") + 8:src.index("};")]
    gates = []
    for line in body.splitlines():
        m = re.match(r"\s*(\w+)\[(.*)\];", line)
        if not m:
            continue
        g, args = m.group(1), [f"qs[{a.strip()[1:]}]" for a in m.group(2).split(",")]
        gates.append(f"Controlled Z([{', '.join(args[:-1])}], {args[-1]});" if g == "MCZ"
                     else f"CNOT({args[0]}, {args[1]});" if g == "CX" else f"{g}({args[0]});")
    meas = "\n".join(f"    if M(qs[{i}]) == One {{ set v += {2 ** i}; }}" for i in range(n))
    marked = re.search(r"basis '(\d+)'", src).group(1)
    code = sum(2 ** i for i, c in enumerate(marked) if c == "1")
    return (f"operation Grover() : Int {{\n    use qs = Qubit[{n}];\n    "
            + "\n    ".join(gates) + f"\n    mutable v = 0;\n{meas}\n    ResetAll(qs);\n    return v;\n}}\n"), code


def main():
    rows = []
    sym = ("Teleport (qb(0), qb(1)) in (q[0]: a . |0> + b . |1>) (q[1]: |0>)")
    rows.append(("teleport", qrat("teleport"),
                 maq(["open examples/teleport.qs", "module SYMBOLIC",
                      f"check {sym} ensures eqUpToPhase(qubitAt(QS:Qubit, 1), a . |0> + b . |1>)"],
                     ["examples/symbolic.maude"])))
    rows.append(("loop", qrat("loop"),
                 maq(["open perf/qrat/loop.qs", "dist Loop", "states Loop"])))
    rows.append(("entangleswap", qrat("entangleswap"),
                 maq(["open perf/qrat/entangleswap.qs",
                      "check EntangleSwap ensures RES:Value == (true).QBool",
                      "states EntangleSwap", "dist EntangleSwap"])))
    for n in SIZES:
        src, code = grover_qs(n)
        path = os.path.join(ROOT, f"tmpgrover{n}.qs")
        open(path, "w").write(src)
        try:
            out = maq([f"open tmpgrover{n}.qs", "dist Grover depth 1000000"])
            hit = re.search(rf"result: {code} prob: ([^;]+)", out)
            if hit:
                out = out.split(":")[0] + f": marked state with p = {hit.group(1).strip()}"
        finally:
            os.unlink(path)
        rows.append((f"grover-{n}", qrat(f"grover-{n}"), out))
        print(rows[-1], flush=True)
    with open(os.path.join(ROOT, "perf", "qrat-results.md"), "w") as f:
        f.write(f"Time limit per run: {LIMIT:.0f} s\n\n| Program | QRAT | MaQ# |\n| --- | --- | --- |\n")
        for r in rows:
            f.write("| " + " | ".join(r) + " |\n")
    print(open(os.path.join(ROOT, "perf", "qrat-results.md")).read())


if __name__ == "__main__":
    main()
