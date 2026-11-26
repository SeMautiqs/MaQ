# Comparison with AutoQ 2.0

The six repeat-until-success programs of the AutoQ 2.0 benchmarks (TACAS 2025;
`benchmarks/TACAS25/RUS` of https://github.com/fmlab-iis/AutoQ, commit 7eed39a,
MIT license),
translated gate by gate into Q# by `qasm2qs.py` (`rus.qs`; `qb[0]` is `anc` and
`qb[1]` is `t`).

`checks.txt` checks, from the symbolic input `a|0> + b|1>` of the module
`SYMBOLIC`, that the target ends in the image of the input given by the
postconditions of AutoQ, up to a global factor. Figure10a and Figure10c are
checked twice: with the original postconditions, which AutoQ also rejects, and
with the corrected ones (`post_corrected.hsl`).

    maude -allow-files examples/symbolic.maude qsharp-io.maude < validation/autoq/checks.txt

The checks use `depth 500`. For Figure7 and Figure8 the whole state graph is
explored; for the others, each failed iteration multiplies the amplitudes by a
common factor, such as 1+2i, that the canonical form does not remove, so the
graph is infinite and only the paths of at most 500 steps are checked. These
paths carry all the probability but less than 10^-9, for every input state:
`dist` with `depth 500` reports the unexplored probability, which does not
depend on the input (e.g., from `a|0> + b|1>` in `SYMBOLIC`):

    dist Figure10c (qb(0), qb(1)) in (q[0]: |0>) (q[1]: a . |0> + b . |1>) depth 500

AutoQ is run as `autoq ver pre.hsl circuit.qasm post.hsl` in each directory.
