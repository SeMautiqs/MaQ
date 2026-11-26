// Assertions with Fact: a false one ends the execution with the result
// assertionFailed, which check, dist, run, and mc (proposition failed) report.
namespace F {
  import Std.Diagnostics.*;
  operation BellFact() : Unit {
    use (a, b) = (Qubit(), Qubit());
    H(a); CNOT(a, b);
    let r1 = M(a); let r2 = M(b);
    Fact(r1 == r2, "correlated results");
    ResetAll([a, b]);
  }
  operation BellWrong() : Unit {
    use (a, b) = (Qubit(), Qubit());
    H(a); CNOT(a, b);
    Fact(M(a) == Zero, "always zero?");
    ResetAll([a, b]);
  }
  operation Biased() : Result {
    use q = Qubit();
    H(q); T(q); H(q);
    let r = M(q);
    Std.Diagnostics.Fact(r == Zero, "zero");
    Reset(q);
    return r;
  }
}
