"""Comparison of MaQ# with AutoQ 2.0 on the repeat-until-success programs of its
benchmarks (benchmarks/TACAS25/RUS of https://github.com/fmlab-iis/AutoQ).

AutoQ must be built beforehand. For each program, the script runs
`autoq ver pre.hsl circuit.qasm post.hsl` (and post_corrected.hsl when it
exists), and MaQ# on the corresponding check of validation/autoq/checks.txt,
each in its own Maude process. The MaQ# times include the start-up of Maude and
the loading of the tool and the program, which is also measured separately.

Usage:  python3 perf/compare_autoq.py AUTOQ_BINARY AUTOQ_RUS_DIR [repetitions]
Writes perf/autoq-results.md.
"""
import os, re, resource, statistics, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTOQ, RUS = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 5
LIMIT = 300.0
PROGRAMS = ["Figure7", "Figure8", "Figure9", "Figure10a", "Figure10b", "Figure10c"]


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


def timed(cmd, inp=None, cwd=ROOT):
    """Median wall time of REPS runs, and the output of the last one."""
    times, out = [], ""
    for _ in range(REPS):
        t0 = time.monotonic()
        try:
            out = subprocess.run(cmd, input=inp, capture_output=True, text=True, cwd=cwd,
                                 timeout=LIMIT, preexec_fn=unlimited_stack).stdout
        except subprocess.TimeoutExpired:
            return None, "timeout"
        times.append(time.monotonic() - t0)
    return statistics.median(times), re.sub(r"\x1b\[[0-9;]*m", "", out)


def autoq(prog, post):
    d = os.path.join(RUS, prog)
    t, out = timed([AUTOQ, "ver", "pre.hsl", "circuit.qasm", post], cwd=d)
    if t is None:
        return "timeout"
    verdict = "verified" if "[OK]" in out else \
              "failed" if "[ER]" in out or "fail" in out.lower() else out.strip()[-60:]
    return f"{t:.2f} s, {verdict}"


def maq(check):
    cmds = ["open validation/autoq/rus.qs", "module SYMBOLIC", check, "q"]
    t, out = timed(["maude", "-no-banner", "-no-advise", "-allow-files",
                    "examples/symbolic.maude", "qsharp-io.maude"], "\n".join(cmds) + "\n")
    if t is None:
        return "timeout"
    verdict = "holds" if "holds in all" in out else "fails" if "does NOT hold" in out else "?"
    full = " (whole graph)" if "whole state space" in out else \
           " (cut at 500 steps)" if "exploration cut" in out else ""
    return f"{t:.2f} s, {verdict}{full}"


def main():
    checks = [l for l in open(os.path.join(ROOT, "validation/autoq/checks.txt")).read().splitlines()
              if l.startswith("check ")]
    startup, _ = timed(["maude", "-no-banner", "-no-advise", "-allow-files",
                        "examples/symbolic.maude", "qsharp-io.maude"],
                       "open validation/autoq/rus.qs\nmodule SYMBOLIC\nq\n")
    rows = ["| Program | Postcondition | AutoQ | MaQ# |", "|---|---|---|---|"]
    for prog in PROGRAMS:
        mine = [c for c in checks if c.split()[1] == prog]
        posts = ["post.hsl"] + (["post_corrected.hsl"]
                                if os.path.exists(os.path.join(RUS, prog, "post_corrected.hsl")) else [])
        for post, check in zip(posts, mine):
            row = f"| {prog} | {post} | {autoq(prog, post)} | {maq(check)} |"
            print(row, flush=True)
            rows.append(row)
    text = (f"# MaQ# and AutoQ 2.0 on the RUS programs of AutoQ\n\n"
            f"Median of {REPS} runs. MaQ# times include the start-up of Maude and the loading "
            f"of the tool and the program, which alone take {startup:.2f} s.\n\n" + "\n".join(rows) + "\n")
    open(os.path.join(ROOT, "perf/autoq-results.md"), "w").write(text)
    print(text)


if __name__ == "__main__":
    main()
