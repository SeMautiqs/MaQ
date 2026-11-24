# MaQ#: Q# in Maude — design notes

Executable operational semantics of a fragment of Q#, built on top of the
symbolic qubit semantics of smc4qc (Canh Minh Do, JAIST).

## Quick start

```
maude -allow-files qsharp-io.maude
Q#> open examples/bell.qs
Q#> run Main
Q#> check Main ensures RES:Value == (true).QBool
```

With symbolic amplitudes:

```
maude -allow-files examples/symbolic.maude qsharp-io.maude
Q#> open examples/teleport.qs
Q#> module SYMBOLIC
Q#> check Teleport (qb(0), qb(1)) in (q[0]: a . |0> + b . |1>) (q[1]: |0>) ensures eqUpToPhase(qubitAt(QS:Qubit, 1), a . |0> + b . |1>)
```

Commands (in all of them, `Op` also admits the form `Op (args) in state`):

| Command | Effect |
|---|---|
| `open f.qs` / `show` | load a program / show the translation of its operations (without the prelude) |
| `run Op` | distinct final states, with the probability of **one** path; if there are none, the statement where execution gets stuck |
| `runnp Op` | the same without probabilities: finite graph even with RUS loops |
| `dist Op` | **exact distribution** of the result: adds up all paths, up to 200 steps, and reports the unexplored and the stuck mass |
| `dist Op depth N` | the same, exploring paths of up to N steps |
| `check Op ensures cond` | `cond` in all final states; `QS:Qubit` is the state and `RES:Value` the result. A final state in which `cond` does not reduce to `true` is a counterexample |
| `mc Op satisfies F` | LTL model checking of `F` |
| `states Op` | number of reachable states (mode without probabilities) |
| `module M` | working module (must extend `QSHARP-PROPS`) |
| `load f.txt` | run the commands of a file, one per line; blank lines and lines starting with `---` or `#` are skipped. The commands are echoed after the prompt and run before the pending ones, so scripts can be nested |
| `q` / `quit` | exit |

LTL propositions: `ended`, `returns(V)`, `qubit(N, V)`, `qubitPh(N, V)` (up to phase),
`entangled(N)` and `liveLE(K)` (at most K live qubits).

## Files

| File | Contents |
|---|---|
| `qsharp-syntax.maude` | `QSHARP-SYNTAX`: syntax only; does not depend on smc4qc |
| `qsharp-semantics.maude` | `QSHARP-SEMANTICS`: configuration, equations and rules |
| `qsharp-props.maude` | `QSHARP-PROPS`: `eqUpToPhase` (phases ±1, ±i) |
| `qsharp-mc.maude` | `QSHARP-MC`: *stutter* rule and atomic propositions for the model checker |
| `../common/smc4qc/` | smc4qc, as a git submodule, unmodified |
| `qsharp-io.maude` | interactive tool: MUnit-style I/O loop |
| `frontend/qsharp-lexer.maude` | lexer on `String`, run before `tokenize` |
| `frontend/qsharp-surface.maude` | signature of the Q# surface syntax and of the commands, and grammars with bubbles built at the metalevel |
| `frontend/qsharp-translate.maude` | metalevel translation from the surface syntax into `QSHARP-SYNTAX` |
| `examples/` | `bell.qs`, `teleport.qs`, `ghz.qs`, `rus.qs`, `functors.qs`, `random.qs`, `errors.qs` and `symbolic.maude` |
| `tests/` | object-level tests (`run-all.sh`) and a session of the tool (`run-tool.sh`) |
| `frontend/qsharp-prelude.maude` | part of the Q# standard library, written in Q# |
| `validation/` | `validate.py` with `validation.qs`, `algorithms.qs` and `extensions.qs`: comparison with the official Q# simulator; `samples.py` and `katas.py`: coverage on the official samples and Quantum Katas |
| `perf/` | `run_perf.py`: scalability on GHZ(n) and Grover(n) |

## Supported subset

- Declarations `operation 'F (p : T, ...) : T { ... }`. Types are annotations only.
- Statements: `use 'q = Qubit() ;`, `let`, `mutable`, `set`, `set +=`, `if`/`else`,
  `for 'i in a .. b { }`, `for 'q in 'qs { }`, `while`, `repeat { } until c ;`,
  `repeat { } until c fixup { }` and `return`.
- Arrays: `[e1, e2]`, `'qs[i]`, `Length('qs)` and `use 'qs = Qubit[n] ;`.
- Pure expressions: `Int`, `true`/`false`, `Zero`/`One`, `+ - *` and the comparisons
  `eq neq lt le gt ge`, which correspond to `== != < <= > >=`; also `and`, `or` and `not`.
- Intrinsics: `I X Y Z H S T CNOT CY CZ SWAP CCNOT M Reset ResetAll`.
- Calls to user-defined operations with parameter passing and return values.
- Functors: `Adjoint` and `Controlled` on intrinsics and on user-defined operations,
  nested and combined (`Controlled Adjoint S`), and `within { } apply { }`.

The front end accepts a larger surface syntax and reduces it to this core (see below): tuples,
slices, assignments without `set`, implicit returns, operations as arguments and a prelude of
library operations written in Q#.

**Key restriction:** a call (`Call`) is not an expression. It can only appear at the
root of a statement: `'H('q) ;`, `let 'r = 'M('q) ;`, `set 'x = 'F(...) ;`
or `return 'F(...) ;`. Hence conditions are pure, and the grammar guarantees it.

## Front end: from Q# source to Maude

1. **Reading**: the file is read with `FILE` (`openFile`, `getLine`, `closeFile`).
2. **Lexer**: splits operators written together (`0..n-1`, `a==b`), removes `//` comments and keeps strings.
3. **Parsing**: `metaParse` in `QSHARP-GRAMMAR`. This grammar is the `QSHARP-SURFACE-SIGN` signature
   plus a `Bubble (1 1)` token for identifiers, with keywords excluded.
   The surface syntax is plain Q#: `==`, `<`, `elif`, `namespace`, `import`, `@EntryPoint()`, `is Adj + Ctl`.
4. **Translation** into `QSHARP-SYNTAX`. Besides renaming, it desugars:
   - Calls inside expressions: they are extracted into temporaries `$t0, $t1, ...`, from left to right.
     In `repeat-until`, the prologue of the condition is placed at the end of the body.
   - A call in the condition of a `while` is rejected, because the condition is re-evaluated in each iteration.
   - `elif` becomes `else { if }` and `set x -= e` becomes `set x = x - e`.
   - `function` becomes `operation`; `namespace`, `import`, `@EntryPoint()` and characteristics (`is Adj + Ctl`) are ignored.
   - Calls to `Message`, `DumpMachine`, `DumpRegister` and `Fact` are dropped; qualified names
     (`Std.Diagnostics.DumpMachine`) keep only their last component.
   - Assignments without `set` (`x = e;`, `x += e;`) become `set` statements, and a block that
     ends in an expression returns it.
   - `ApplyToEach(Op, qs)` becomes a `for` loop; tuple patterns in `let` and `for` become a
     temporary and projections; `use (a, b) = (Qubit(), Qubit());` becomes two `use`s.
   - Slices `a[i..j]`, `a[i...]` and `a[...j]` become `slice`, `sliceFrom` and `sliceTo`; `/` and
     `%` become `quo` and `rem`, and `c ? a | b` becomes `cond`.
   - Q#'s `+` becomes `plus`, which adds integers and concatenates arrays (Maude's `+` on `INT`
     is commutative and cannot be used for arrays).
6. **Lexer details.** Grouping parentheses with a comma at the top level are tuples: the lexer
   writes the keyword `tuple` in front of them, which avoids ambiguities with Maude's own
   parentheses. It also removes attributes (`@Test()`) and the `$` of interpolated strings.
7. **Prelude.** `frontend/qsharp-prelude.maude` contains part of the standard library written in
   Q# (`Measure`, `ApplyControlledOnInt`, `ApplyControlledOnBitString`, `MResetX`, `Head`, `Tail`,
   `Rest`, `Most`); it is appended to every program and executed by the same semantics. `Measure`
   uses an auxiliary qubit that collects the parity of the measured qubits after the basis changes.
   `MResetZ`, `MResetEachZ` and `MeasureEachZ` are defined by equations in `QSHARP-SYNTAX`.
5. **Execution**: `metaSearch` on `upModule(M)`, with `M = QSHARP-PROPS` or the module chosen with `module`.
   The arguments, the state and the condition of a command are bubbles parsed in `M`.

`QSHARP-SYNTAX` cannot share a module with `META-LEVEL`: since `Qid < Exp`, `_,_` and `_[_]`
clash with those of `META-TERM`. This is why the front end works only at the metalevel.

## Validation against the Q# simulator

`python3 validation/validate.py [shots]` (requires `pip install qdk` and `maude` in the PATH)
runs each operation in the official Q# simulator and compares it with the exact distribution
given by `dist`. For each result it computes z = (k − Np)/√(Np(1−p)). A case fails if some
|z| > 4, if a result with probability 0 shows up, or if one with probability 1 is missing.

With 4000 shots, **all 35 operations agree**. They include cases with
irrational probabilities, such as H T H, which yields One with (2−√2)/4, joint distributions,
Controlled S/T, teleportation of a prepared state, RUS, Deutsch–Jozsa, Bernstein–Vazirani,
Grover (2 and 3 qubits), superdense coding and entanglement swapping.

## Design of the semantics

- Configuration: `{(qstate: Q) (k: K) (env: Env) (decls: D) (next: N) (prob: P) (result: V) (isEnd: B)}`.
  `k:` is a continuation of statements.
- **Rules**: gates, `M` and `Reset`; each quantum step is a state. `M` branches
  into `M-Zero` and `M-One`, prunes the branches with probability 0 and multiplies `prob:`.
- **Equations**: the whole classical part (environments, blocks, calls, `return`).
- Q# allows shadowing, so environments are stacks of bindings: a declaration pushes a binding,
  and lookups and `set` use the innermost one. Scopes use `restore(Env)`, which pops the
  bindings pushed since the block was opened. Calls use `frame(Env)`.
- `use` inserts `release(N)` at the end of the block. If the qubit is separated and in |0⟩,
  it is removed from the state.
- `repeat` and `while` run one iteration at a time and place the loop again after the
  `restore`, so the continuation does not grow.
- When a qubit is released, `next:` becomes the first free index according to the live qubits.
  States are canonical, and a `use` inside a loop does not make the graph infinite.
- Two modes: `run`/`runWith` accumulate the path probability in `prob:`;
  `runNP`/`runWithNP` fix it to `untracked`. With repeat-until-success, the former yields an
  infinite state space (1/2, 1/4, ...) and the latter a finite one, suitable for model checking.
- **Functors**:
  - `Adjoint Op` runs `adj(body)`: reverse order, each call with `Adjoint`, and `for` loops
    traversed backwards. Classical bindings and initial `use`s are kept in front.
  - `Controlled Op(ctrls, args)` runs `ctl(body, ctrls)`: each call of the body receives
    the controls. Nested `Controlled`s join their control lists.
  - Normalization: `Adjoint Adjoint C = C` and `Adjoint Controlled C = Controlled Adjoint C`.
  - `within {A} apply {B}` runs as `A; B; adj(A)`, each part in its own scope.
- **Generic applier of controlled gates** `applyU(Q, ctrls, t, U)`: generalizes smc4qc's
  `CX = B0⊗I + B3⊗X` to k controls in arbitrary positions, with
  G(c·Cs) = P0_c⊗I + P1_c⊗G(Cs). It first joins the qubits involved into one block and then applies `simplify`.
  It is used for `Controlled` and for T, S† and T†. (Up to smc4qc v1.0.2, T used `1 + i` instead of
  `1 .+ i` and did not reduce; this and three other errors we reported were fixed upstream in
  commit 56d5bcc, which MaQ# requires.)
- **Exact distribution** (`dist`): the execution **tree** is traversed with `metaApply`, rule by
  rule, using the labels given by `getRls` on the flattened module. `search` is not enough because
  it merges identical configurations: in Bell, paths 00 and 11 end up equal and it would give 1/2
  instead of 1. Each leaf adds its `prob:` to its result (`.+` in the working module, so it
  works with symbolic amplitudes). Exploration stops after 200 steps (or N with `depth N`)
  and the rest is reported.
- **Model checking**: `QSHARP-MC` adds the *stutter* rule on final states and the
  propositions. The tool joins it at the metalevel with the working module and runs
  `modelCheck` in the mode without probabilities. This way `dist` uses the module without *stutter*.
- **Global phase of a separated qubit**: a single-qubit block `c . |k>` becomes `|k>`.
  Since the state is normalized, |c| = 1 and c is a global phase. Without this, after measuring states
  with T phases, smc4qc leaves c as an expression with roots that it cannot reduce to modulus 1, and
  the next measurement gets stuck.
- Entry points: `run(Decls, 'Main)`, or `runWith(Decls, 'Op, args, initialState, nextIndex)`
  to start from symbolic states.

Programs are written in modules that import **only** `QSHARP-SYNTAX`. smc4qc's
`NatList` juxtaposition `__` falls into the same kind as `Exp` and
would cause parsing ambiguities.

## Test results

- **Bell**: the result is always `true` (correlated measurements) and the qubits are released.
- **Teleportation** with symbolic `a|0⟩+b|1⟩`: the target receives the state in all
  branches. The branch m1=m2=One gives `-(a|0⟩+b|1⟩)`, i.e., a global phase.
- With `eqUpToPhase`, teleportation has no counterexamples.
- **Calls**: `CountOnes(3)` with random bits gives 0, 1, 2 or 3.
- **GHZ** with `Qubit[3]`: the state before measuring is (|000⟩+|111⟩)/√2 and the number of ones is always 0 or 3.
- **Functors** (`functors.qs`):
  - `Adjoint` undoes user-defined operations, also with loops.
  - `Controlled X` is CNOT and, with two controls, Toffoli.
  - `Controlled` works on user-defined operations.
  - `within {H} apply {Z}` gives X.
  - T⁴ = Z, and `Adjoint T`/`Adjoint S` undo T and S.
- **Exact distribution**:
  - Bell: `true` with probability 1.
  - Three random bits (`random.qs`): 0, 1, 2 and 3 ones with 1/8, 3/8, 3/8 and 1/8, whereas
    `run` shows each path with 1/8.
  - RUS: `One` with 1 − 2⁻⁶⁶ and 2⁻⁶⁶ unexplored.
  - Symbolic teleportation: 1, thanks to |a|²+|b|²=1.
- **LTL**:
  - Bell satisfies `<> returns(true)` and `[] liveLE(2)`, and does not satisfy `[] ~ entangled(0)`.
  - Teleportation satisfies `<> [] qubitPh(1, a|0⟩+b|1⟩)`.
  - In RUS, `<> ended` **fails** with the cycle `H M-Zero Reset-Zero`. It is a path with
    probability 0 that LTL without fairness does not discard, whereas `dist` gives 1. It is a good
    example of why both views are needed.
- **Loops**: `while` gives 3. RUS in `runNP` mode has 5 states and the result is always `One`.
  The `fixup` sees the body variables and the qubit is released.

## Known limitations and next steps

1. `eqUpToPhase` only covers the phases ±1 and ±i; T phases would need more.
2. `run` still shows the probability of a single path; `dist` gives the distribution.
   LTL without fairness: termination properties of RUS loops fail because of paths with
   probability 0. Fairness or a probabilistic logic is still missing.
3. Missing from the subset: `Double` and rotations, tuple parameters, lambdas and partial
   application, user-defined types. Inside a `Controlled`
   it is not checked that the body does not measure, which Q# forbids. Calls inside
   expressions are only supported through the front end, which extracts them into temporaries,
   and not in the condition of a `while`.
4. More informative LTL counterexamples: currently only the applied rules are shown.
5. More precise front-end error messages: currently the token is reported, not the rule.
6. smc4qc issues found (reported to the author): `q[nil]: nil` after measuring a whole
   block, `(i)^*` not reducing, the T gate defined with `1 + i`, and `Sqrt`/`./`/`.*`/`.+`
   declared only on `Complex`, so that measurement gets stuck when the probability
   contains a square root.
