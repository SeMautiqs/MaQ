# MaQ

Executable semantics and verification of quantum programming languages in [Maude](https://maude.cs.illinois.edu).

The first member of the family is **MaQ#**, for Microsoft's [Q#](https://learn.microsoft.com/azure/quantum/qsharp-overview).
MaQ# reads Q# source files and supports symbolic execution, exact outcome distributions and LTL model checking.

## Repository layout

| Path | Contents |
|---|---|
| `common/` | Quantum core shared by all languages: [smc4qc](https://github.com/canhminhdo/smc4qc) (git submodule) and a small patch module on top of it |
| `maqsharp/` | MaQ#: Q# syntax and semantics, front end, interactive tool, examples, tests and validation |

## Requirements

- Maude 3.5 or later
- For the validation against the Q# simulator only: Python 3 and `pip install qdk`

## Getting started

```
git clone --recurse-submodules https://github.com/ariesco/MaQ.git
cd MaQ/maqsharp
maude -allow-files qsharp-io.maude
```

```
Q#> open examples/bell.qs
Q#> dist Main
  resultado: (true ).QBool   prob: 1
Q#> mc Main satisfies <> returns((true).QBool)
  se cumple
```

With a symbolic input state:

```
maude -allow-files examples/symbolic.maude qsharp-io.maude
Q#> open examples/teleport.qs
Q#> module SYMBOLIC
Q#> check Teleport (qb(0), qb(1)) in (q[0]: a . |0> + b . |1>) (q[1]: |0>) ensures eqUpToPhase(qubitAt(QS:Qubit, 1), a . |0> + b . |1>)
  se cumple en todos los estados finales
```

## Commands

| Command | Effect |
|---|---|
| `open f.qs` / `show` | load a Q# file / show its translation |
| `run Op` / `runnp Op` | final states, with or without path probabilities |
| `dist Op` | exact distribution of the result, summing over all execution paths |
| `check Op ensures cond` | check `cond` on every final state (`QS:Qubit` = state, `RES:Value` = result) |
| `mc Op satisfies F` | LTL model checking; propositions `ended`, `returns(V)`, `qubit(N, V)`, `qubitPh(N, V)`, `entangled(N)`, `liveLE(K)` |
| `module M` | module used to parse arguments, states and conditions |

Every command also accepts `Op (args) in state` to start from given arguments and a given quantum state.

## Supported Q# subset

Operations and functions with parameters and return values; `use` with `Qubit()` and `Qubit[n]`;
`let`, `mutable`, `set`; `if`/`elif`/`else`; `for` over ranges and arrays; `while`; `repeat`/`until`/`fixup`;
arrays and `Length`; the `Adjoint` and `Controlled` functors; `within`/`apply`;
intrinsics `I X Y Z H S T CNOT CY CZ SWAP CCNOT M Reset ResetAll`.
Not yet supported: tuples, callables as values, `Double` and rotations.

## Tests and validation

```
cd maqsharp
./tests/run-all.sh                  # object-level tests
./tests/run-tool.sh                 # a session of the interactive tool
python3 validation/validate.py      # comparison with the Microsoft QDK simulator
```

The validation runs each operation on the QDK simulator and compares the observed frequencies with the exact
distribution computed by MaQ#. All 19 operations currently agree.

A detailed design note (in Spanish) is in `maqsharp/DESIGN.es.md`.

## License

MaQ is released under the [MIT License](LICENSE). The `common/smc4qc` submodule is a separate
project by Canh Minh Do and is not covered by this license.
