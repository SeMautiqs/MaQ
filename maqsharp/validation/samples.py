"""Coverage of MaQ# on the official Q# samples.

Each sample of https://github.com/microsoft/qsharp (folders samples/algorithms,
samples/language and samples/getting_started) is opened in MaQ# and, if it loads
and has a Main operation, run with `run Main`. Each sample is reported as
  runs                   a final state is reached
  loaded, STUCK          it loads, but the execution gets stuck (unsupported operation)
  loaded, run timeout    it loads, but the execution exceeds the time limit
  loaded (no Main)       it loads, but has no Main operation
  syntax: N: TOKEN       the parser stops at token N
  error: ...             the program is outside the supported subset

The samples that run are then compared with the Q# simulator, as in
validate.py: the exact distribution of the result of Main computed by `dist`
against the frequencies observed in the simulator. Each one is reported as
  agree                  all results pass the z-test
  DISAGREE               some result fails it
  not compared: ...      the simulator or dist cannot be used on the sample

Usage:  python3 validation/samples.py QSHARP_REPO_DIR [shots]
Requires the maude binary in the PATH, MAUDE_LIB pointing to its prelude, and qdk.
"""
import collections, glob, math, os, re, subprocess, sys, warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("QSHARP_PYTHON_TELEMETRY", "none")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLDERS = ["samples/algorithms", "samples/language", "samples/getting_started"]
TIMEOUT = 120


def maude(cmds):
    try:
        return subprocess.run(
            ["maude", "-no-banner", "-no-advise", "-allow-files", "qsharp-io.maude"],
            input=cmds, capture_output=True, text=True, cwd=ROOT, timeout=TIMEOUT,
            env={**os.environ, "PWD": ROOT}).stdout
    except subprocess.TimeoutExpired:
        return "TIMEOUT"


def classify(path):
    out = maude(f"open {path}\nq\n")
    if "Program loaded" not in out:
        if "syntax error at token" in out:
            return "syntax: " + out.split("syntax error at token")[1].split("\n")[0].strip()
        if "Error:" in out:
            return "error: " + out.split("Error:")[1].split("\n")[0].strip()
        return "other"
    if "Main" not in out.split("Operations:")[1].split("\n")[0].split():
        return "loaded (no Main)"
    out = maude(f"open {path}\nrun Main\nq\n")
    if out == "TIMEOUT":
        return "loaded, run timeout"
    body = out.split("Operations:")[1]
    if "result:" in body:
        return "runs"
    if "no final states" in body:
        return "loaded, STUCK"
    return "loaded, other"


def compare(path, shots):
    """Compares dist Main with the simulator on a sample that runs."""
    from qdk import qsharp
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from validate import norm, num, seeded_run
    out = maude(f"open {path}\ndist Main depth 100000\nq\n")
    if out == "TIMEOUT":
        return "not compared: dist timeout"
    out = re.sub(r"\n\s{4,}", " ", out.split("Operations:")[1])
    exact = {norm(m.group(1)): num(m.group(2))
             for m in re.finditer(r"result: (.*?)\s+prob: (.*)", out)}
    if not exact or "stuck" in out or "unexplored" in out:
        return "not compared: no exact distribution"
    src = open(path).read()
    ns = re.search(r"namespace\s+([\w.]+)", src)
    try:
        with open(os.devnull, "w") as null:      # samples print messages and dumps
            old = os.dup(1); os.dup2(null.fileno(), 1)
            try:
                qsharp.init()
                qsharp.eval(src)
                res = seeded_run((ns.group(1) + "." if ns else "") + "Main()", shots)
            finally:
                os.dup2(old, 1); os.close(old)
    except Exception as e:
        return "not compared: simulator (" + str(e).strip().splitlines()[0][:40] + ")"
    counts = collections.Counter(norm(r) for r in res)
    worst = 0.0
    for v in set(exact) | set(counts):
        p, k = exact.get(v, 0.0), counts.get(v, 0)
        if p <= 1e-12 or p >= 1 - 1e-12:
            if (p <= 1e-12 and k > 0) or (p >= 1 - 1e-12 and k < shots):
                return f"DISAGREE on {v}"
            continue
        worst = max(worst, abs(k - shots * p) / math.sqrt(shots * p * (1 - p)))
    return f"agree (max|z| {worst:.2f})" if worst <= 4 else f"DISAGREE (max|z| {worst:.2f})"


def main():
    repo = os.path.abspath(sys.argv[1])
    shots = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    files = sorted(f for d in FOLDERS for f in glob.glob(os.path.join(repo, d, "*.qs")))
    summary = collections.Counter()
    for f in files:
        r = classify(f)
        if r == "runs":
            c = compare(f, shots)
            summary["compared: " + c.split(" (")[0].split(":")[0].split(" on ")[0]] += 1
            r = "runs, " + c
        summary["syntax" if r.startswith("syntax") else "runs" if r.startswith("runs")
                else r.split(" (")[0] if r.startswith("error") else r] += 1
        print(f"{r[:60]:60}  {os.path.relpath(f, repo)}", flush=True)
    print()
    for k, v in summary.most_common():
        print(f"{v:3}  {k}")
    print(f"{summary['runs']}/{len(files)} samples run")


if __name__ == "__main__":
    main()
