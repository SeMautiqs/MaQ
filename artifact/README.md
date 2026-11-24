# Artifact for "MaQ#: Executing and Verifying Q# Programs in Maude" (SPIN 2027)

DOI: [10.5281/zenodo.24466579](https://doi.org/10.5281/zenodo.24466579)

This artifact contains MaQ#, an executable semantics of a subset of Q# in Maude, together
with an interactive tool that reads Q# files and supports execution, exact outcome
distributions, assertion checking on final states and LTL model checking.
It reproduces the validation against the Microsoft Q# simulator (RQ1) and the performance
measurements (RQ4) reported in the paper.

## Contents

| Path | Contents |
|---|---|
| `maqsharp-image.tar.gz` | Docker image with Maude 3.5.1, the Python package `qdk` and the sources |
| `MaQ/` | Sources (the same as in the image and at https://github.com/ariesco/MaQ) |
| `MaQ/maqsharp/` | MaQ#: syntax, semantics, front end, tool, examples, tests, validation and performance scripts |
| `MaQ/common/` | smc4qc (symbolic qubit semantics by Canh Minh Do) |
| `MaQ/artifact/` | Dockerfile and the scripts below |
| `/opt/qsharp` (in the image) | Samples and Quantum Katas of the Q# repository (commit `0e58afc`), used in RQ2 |
| `License.txt` | Licenses of all components |

## Requirements

- An x86-64 machine with Docker or Podman. No network access is needed.
- 2 GB of free disk space and 4 GB of RAM.
- TODO: list the machines and systems on which the image has been tested (at least the TACAS 26 VM, Ubuntu 25.04).

## Loading the image

```
docker load -i maqsharp-image.tar.gz
docker run --rm -it --network none maqsharp:spin27
```

The container starts in `/MaQ/maqsharp`. With Podman, replace `docker` by `podman`.

## Smoke test (about 1 minute)

Inside the container:

```
../artifact/smoke-test.sh
```

It runs the object-level tests (`tests/run-all.sh`) and a session of the interactive tool
(`tests/run-tool.sh`, commands in `tests/tool-session.txt`), and compares the output with
`artifact/smoke-expected.txt`. The last line must be

```
SMOKE TEST PASSED
```

## Full reproduction (about 1 hour 15 minutes)

Inside the container:

```
../artifact/reproduce.sh
```

or each part separately:

| Claim in the paper | Command | Time |
|---|---|---|
| RQ1: the exact distributions computed by MaQ# agree with the Q# simulator on all 35 operations (Table 5, App. B) | `python3 validation/validate.py 4000` | < 1 min |
| RQ2: 30 of the 72 official Q# samples run; 26 of them are compared with the simulator and agree | `python3 validation/samples.py /opt/qsharp` | ~5 min |
| RQ2: 66 of the 79 testable Quantum Katas exercises agree with the simulator | `python3 validation/katas.py /opt/qsharp/katas/content 1000` | ~10 min |
| RQ3: the five seeded faults of Table 3 are detected | `maude -no-banner -allow-files examples/symbolic.maude qsharp-io.maude < validation/faults.txt` | < 1 min |
| RQ4: scalability on GHZ(n) and Grover(n) (TODO: table and figure numbers) | `python3 perf/run_perf.py 120 16` | ~1 h |
| Examples of Sect. 4 (Bell, teleportation with symbolic amplitudes, RUS, functors) | `./tests/run-tool.sh` | < 1 min |

`validate.py` prints, for each operation, the largest |z| statistic, the total variation
distance, whether the case passes, and the two distributions. Since the simulator is
sampled, the numbers vary between runs; every case must still pass (|z| ≤ 4), and the
last line must be `ALL CASES PASS`.

`run_perf.py` writes `perf/results.csv` and `perf/results.md`. The arguments are the time
limit per run in seconds and the largest n. Absolute times depend on the machine; the number
of rewrites, the number of reachable states, the number of results and the success
probability of Grover are deterministic and must coincide with the paper. To obtain a quick
partial reproduction (about 5 minutes), use `python3 perf/run_perf.py 20 8`.

## Using the tool on other programs

```
maude -allow-files qsharp-io.maude
Q#> open examples/bell.qs
Q#> dist Main
Q#> mc Main satisfies <> returns((true).QBool)
Q#> q
```

The commands are described in `MaQ/README.md` and the design in `MaQ/maqsharp/DESIGN.md`.
New Q# files can be written to a directory mounted in the container, e.g.
`docker run --rm -it --network none -v "$PWD":/work maqsharp:spin27`, and opened with
`open /work/file.qs`. The supported subset of Q# is listed in `MaQ/README.md`.

## Troubleshooting

- `Warning: ... file not found`: Maude must be started from `/MaQ/maqsharp`, and `MAUDE_LIB`
  must point to the directory of its prelude (set to `/opt/maude` in the image).
- `Error: syntax error at token ...` after `open`: the program uses a construct outside the
  supported subset (e.g. tuples, `Double`, rotations or callables as values).
- A performance run reported as `timeout` exceeded the time limit; larger sizes of that
  analysis are then skipped. Increase the limit (first argument) to explore further.
- Running without Docker: install Maude 3.5.1 (https://github.com/maude-lang/Maude/releases),
  put it in the `PATH`, set `MAUDE_LIB` to its directory and, for the validation only,
  `pip install qdk==1.34.0`.
