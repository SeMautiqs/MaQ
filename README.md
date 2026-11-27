# MaQ

Executable semantics and verification of quantum programming languages in [Maude](https://maude.cs.illinois.edu).

The first member of the family is **MaQ#**, for Microsoft's [Q#](https://learn.microsoft.com/azure/quantum/qsharp-overview).
MaQ# reads Q# source files and supports symbolic execution, exact outcome distributions and LTL model checking.

## Repository layout

| Path | Contents |
|---|---|
| `common/` | Quantum core shared by all languages: the exact complex numbers of [AS4QC](https://github.com/canhminhdo/as4qc) (git submodule) |
| `maqsharp/` | MaQ#: Q# syntax and semantics, front end, interactive tool, examples, tests and validation |

## Requirements

- Maude 3.5 or later
- For the validation against the Q# simulator only: Python 3 and `pip install qdk`

## Getting started

```
git clone --recurse-submodules https://github.com/SeMautiqs/MaQ.git
cd MaQ/maqsharp
maude -allow-files qsharp-io.maude
```

```
Q#> open examples/bell.qs
Q#> dist Main
  result: (true ).QBool   prob: 1
Q#> mc Main satisfies <> returns((true).QBool)
  holds
```

With a symbolic input state:

```
maude -allow-files examples/symbolic.maude qsharp-io.maude
Q#> open examples/teleport.qs
Q#> module SYMBOLIC
Q#> check Teleport (qb(0), qb(1)) in (q[0]: a . |0> + b . |1>) (q[1]: |0>) ensures eqUpToPhase(qubitAt(QS:Qubit, 1), a . |0> + b . |1>)
  holds in all final states
```

## Commands

| Command | Effect |
|---|---|
| `open f.qs` / `show` | load a Q# file / show the translation of its operations |
| `run Op` / `runnp Op` | final states, with or without path probabilities; if there are none, the statement where execution gets stuck |
| `dist Op` / `dist Op depth N` | exact distribution of the result, summing over all execution paths (up to 200 or N steps) |
| `check Op ensures cond` / `... depth N` | check `cond` on every final state (`QS:Qubit` = state, `RES:Value` = result); with `depth N`, on those reached in at most N steps |
| `mc Op satisfies F` / `... depth N` | LTL model checking (with `depth N`, on the paths cut after N steps); propositions `ended`, `returns(V)`, `qubit(N, V)`, `qubitPh(N, V)`, `entangled(N)`, `liveLE(K)` |
| `states Op` / `states Op depth N` | number of reachable states (in at most N steps) |
| `module M` | module used to parse arguments, states and conditions |
| `load f.txt` | run the commands of a file, one per line (blank lines and lines starting with `---` or `#` are skipped); a script can load other scripts |

Every command also accepts `Op (args) in state` to start from given arguments and a given quantum state.

`runnp`, `check`, `states` and `mc` explore the state graph without probabilities, which is finite
for most programs, also with RUS loops. A classical value that grows without bound, such as a
counter of the attempts of a RUS loop (`Attempts` in `examples/rus.qs`), makes it infinite: use
`depth N` with `check`, `states` and `mc`, which then say whether the exploration was cut, and `dist`,
which has a default depth. With `depth N`, `mc` wraps each state with the number of steps left, so
that a path ends after N steps in a state that loops with the rule `cut`; the proposition `cut`
holds in such a state unless it is final.

## Supported Q# subset

- Operations and functions with parameters and return values, including implicit returns;
  operations passed as arguments (`op : Qubit => Unit`).
- `use` with `Qubit()`, `Qubit[n]` and tuples of qubits; `let`, `mutable`, `set` and assignments
  without `set` (`x += e;`); tuple patterns in `let`, `for` and parameters; `if`/`elif`/`else`; `for` over ranges
  and arrays; `while`; `repeat`/`until`/`fixup`; `within`/`apply`; `fail`.
- Expressions on `Int`, `Bool`, `Result` and `Pauli`, including `/`, `%` and `c ? a | b`; `Double`
  expressions, kept exact as r + s pi (`PI()`, `IntAsDouble`, arithmetic); tuples; arrays with
  `Length`, concatenation, repetition (`[v, size = n]`) and slices (`a[i..j]`, `a[i..s..j]`,
  `a[i...]`, `a[...j]`).
- The `Adjoint` and `Controlled` functors on intrinsics and user-defined operations, including
  explicit specializations (`body`, `adjoint`, `controlled` and `controlled adjoint`, given as a
  block or as `self`, `auto`, `invert` or `distribute`).
- Intrinsics `I X Y Z H S T CNOT CY CZ SWAP CCNOT M Reset ResetAll MResetZ MResetEachZ MeasureEachZ
  ApplyToEach`; rotations `Rx Ry Rz R1 R` by multiples of pi/4 (pi/2 for `Rx` and `Ry`, and
  for `Rz` under `Controlled`), which are exact in the ring of AS4QC; and the library operations `Measure` (Pauli measurements, also joint),
  `ApplyControlledOnInt`, `ApplyControlledOnBitString`, `MResetX`, `Head`, `Tail`, `Rest` and `Most`, defined in Maude.
- Assertions with `Fact(c, msg)`: a false one ends the execution with the result `assertionFailed`,
  which `run`, `dist` and `check` report (any `check` fails on it) and which the LTL proposition
  `failed` observes (`examples/assertions.qs`).
- Diagnostics (`Message`, `DumpMachine`), attributes, `namespace` and `import` are ignored.

Not supported: rotations by other angles, `String` operations, `BigInt`, user-defined types, lambdas and
partial application, bitwise operators and copy-and-update expressions.

## Tests and validation

```
cd maqsharp
./tests/run-all.sh                  # object-level tests
./tests/run-tool.sh                 # a session of the interactive tool
python3 validation/validate.py      # comparison with the Microsoft QDK simulator
python3 perf/run_perf.py            # scalability on GHZ(n) and Grover(n)
python3 validation/samples.py QSHARP_REPO                  # coverage of the official Q# samples
python3 validation/katas.py QSHARP_REPO/katas/content      # differential testing on the Quantum Katas
```

The validation runs each operation on the QDK simulator and compares the observed frequencies with the exact
distribution computed by MaQ#. All 56 operations currently agree, including Deutsch–Jozsa,
Bernstein–Vazirani, Grover (2 and 3 qubits), superdense coding, entanglement swapping, the
rotations of `validation/rotations.qs` (with a three-qubit QFT), the explicit specializations of
`validation/specializations.qs`, Shor's nine-qubit code on all
single-qubit errors (`examples/shor.qs`) and the constructs of `validation/extensions.qs`. On the official Q# repository
([microsoft/qsharp](https://github.com/microsoft/qsharp), commit `0e58afc`), 31 of the 72 samples
run (27 of them can be compared with the simulator, and agree), and the reference solutions of 68 of the 79 automatically testable exercises of 17 Quantum Katas
agree with the simulator on all their inputs; the others use rotations by other angles or other
unsupported operations.

`examples/shor-checks.txt` proves with `check`, for a symbolic input state and for the basis states
(the symbolic constants are nonzero), that Shor's code corrects
each of the 27 single-qubit Pauli errors and releases its eight auxiliary qubits clean: start the
tool with `maude -allow-files examples/symbolic.maude qsharp-io.maude` and run
`load examples/shor-checks.txt`.

Design notes are in `maqsharp/DESIGN.md`.

## License

MaQ is released under the [MIT License](LICENSE). The `common/as4qc` submodule is a separate
project by Canh Minh Do, also released under the MIT License (see `common/as4qc/LICENSE`).
