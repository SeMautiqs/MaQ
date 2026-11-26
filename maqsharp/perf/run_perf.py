"""Performance of MaQ#: GHZ(n) and Grover(n) for increasing n.

For each family, size n and analysis (dist, states, mc), a separate Maude
process is launched with a time limit. A baseline that only loads the tool and
the program is subtracted from the time and the number of rewrites.
Once an analysis exceeds the limit, it is not tried for larger sizes.

Usage:  python3 perf/run_perf.py [limit_in_seconds] [max_n]
Writes perf/results.csv and perf/results.md.
"""
from fractions import Fraction
import csv, math, os, re, resource, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
NMAX = int(sys.argv[2]) if len(sys.argv) > 2 else 12


def ghz(n):
    cnots = "\n".join(f"        CNOT(qs[0], qs[{i}]);" for i in range(1, n))
    return f"""operation Main() : Bool {{
    use qs = Qubit[{n}];
    H(qs[0]);
{cnots}
    mutable ones = 0;
    for q in qs {{
        if M(q) == One {{ set ones += 1; }}
    }}
    ResetAll(qs);
    return ones == 0 or ones == {n};
}}
"""


def grover(n):
    k = max(1, math.floor(math.pi / 4 * math.sqrt(2 ** n)))
    ctrls = ", ".join(f"qs[{i}]" for i in range(n - 1))
    bits = "\n".join(f"    if M(qs[{i}]) == One {{ set v += {2 ** (n - 1 - i)}; }}"
                     for i in range(n))
    return f"""operation Main() : Int {{
    use qs = Qubit[{n}];
    for q in qs {{ H(q); }}
    for it in 1..{k} {{
        Controlled Z([{ctrls}], qs[{n - 1}]);
        for q in qs {{ H(q); }}
        for q in qs {{ X(q); }}
        Controlled Z([{ctrls}], qs[{n - 1}]);
        for q in qs {{ X(q); }}
        for q in qs {{ H(q); }}
    }}
    mutable v = 0;
{bits}
    ResetAll(qs);
    return v;
}}
"""


FAMILIES = {"GHZ": (ghz, 2), "Grover": (grover, 2)}
ANALYSES = {
    "dist": "dist Main depth 1000000",
    "states": "states Main",
    "mc": "mc Main satisfies <> ended",
}


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


def run_maude(qs_file, command):
    cmds = f"open {qs_file}\n" + (command + "\n" if command else "") + "q\n"
    t0 = time.monotonic()
    try:
        out = subprocess.run(
            ["maude", "-no-banner", "-no-advise", "-allow-files", "qsharp-io.maude"],
            input=cmds, capture_output=True, text=True, cwd=ROOT, timeout=LIMIT,
            preexec_fn=unlimited_stack).stdout
    except subprocess.TimeoutExpired:
        return None
    wall = time.monotonic() - t0
    m = re.search(r"rewrites: (\d+)", out)
    return wall, int(m.group(1)) if m else 0, out


def summary(analysis, out):
    if analysis == "states":
        m = re.search(r"reachable states[^:]*: (\d+)", out)
        return m.group(1) if m else "?"
    if analysis == "mc":
        return "holds" if "  holds" in out else "does not hold"
    # long fractions may be split across several lines
    body = re.sub(r"\s+", " ", out)
    found = re.findall(r"result: (.+?) prob: ([\d/ ]+?)(?= result:| unexplored| in stuck| Q#>)", body)
    if not found:
        return "?"
    probs = [(r, Fraction(p.replace(" ", ""))) for r, p in found]
    r, p = max(probs, key=lambda x: x[1])
    return f"{len(probs)} results; max. {r} with p = {float(p):.4f}"


def main():
    rows = []
    for fam, (gen, n0) in FAMILIES.items():
        alive = set(ANALYSES)
        for n in range(n0, NMAX + 1):
            if not alive:
                break
            with tempfile.NamedTemporaryFile("w", suffix=".qs", delete=False, dir=ROOT) as f:
                f.write(gen(n))
                qs = os.path.basename(f.name)
            try:
                base = run_maude(qs, None)
                if base is None:
                    break
                for an in sorted(alive):
                    r = run_maude(qs, ANALYSES[an])
                    if r is None:
                        rows.append((fam, n, an, "timeout", "", ""))
                        alive.discard(an)
                        print(f"{fam}({n}) {an}: timeout", flush=True)
                        continue
                    wall, rw, out = r
                    if "rewrites:" not in out:  # Maude aborted (e.g. stack overflow)
                        rows.append((fam, n, an, "error", "", ""))
                        alive.discard(an)
                        print(f"{fam}({n}) {an}: error (Maude aborted)", flush=True)
                        continue
                    t = max(0.0, wall - base[0])
                    rows.append((fam, n, an, f"{t:.2f}", rw - base[1], summary(an, out)))
                    print(f"{fam}({n}) {an}: {t:.2f}s {rw - base[1]} rewrites  {summary(an, out)}",
                          flush=True)
            finally:
                os.unlink(os.path.join(ROOT, qs))
    with open(os.path.join(ROOT, "perf", "results.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["family", "n", "analysis", "seconds", "rewrites", "result"])
        w.writerows(rows)
    with open(os.path.join(ROOT, "perf", "results.md"), "w") as f:
        f.write(f"Time limit per run: {LIMIT:.0f} s\n\n")
        f.write("| Family | n | Analysis | Seconds | Rewrites | Result |\n")
        f.write("| --- | --- | --- | --- | --- | --- |\n")
        for r in rows:
            f.write("| " + " | ".join(str(x) for x in r) + " |\n")


if __name__ == "__main__":
    main()
