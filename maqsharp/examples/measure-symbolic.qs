// Measuring a symbolic qubit: probabilities such as b * b ^* (SYMBOLIC module).
namespace S {
  operation MeasureMsg(q : Qubit) : Result { return M(q); }
  operation RotateThenMeasure(q : Qubit) : Result { H(q); return M(q); }
}
