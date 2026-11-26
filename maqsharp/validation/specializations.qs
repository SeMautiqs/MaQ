namespace Specializations {
  // explicit specializations whose bodies differ from the generated ones,
  // so that the result tells which one is used
  operation A(q : Qubit) : Unit is Adj + Ctl {
    body (...) { H(q); }
    adjoint (...) { X(q); }
  }
  operation C(q : Qubit) : Unit is Adj + Ctl {
    body (...) { X(q); }
    controlled (cs, ...) { Controlled Z(cs, q); }
  }
  operation CA(q : Qubit) : Unit is Adj + Ctl {
    body (...) { X(q); }
    adjoint (...) { X(q); }
    controlled (cs, ...) { Controlled Z(cs, q); }
    controlled adjoint (cs, ...) { Controlled X(cs, q); }
  }
  operation CS(q : Qubit) : Unit is Adj + Ctl {
    body (...) { X(q); }
    adjoint (...) { H(q); }
    controlled (cs, ...) { Controlled Z(cs, q); }
    controlled adjoint self;
  }
  operation CD(q : Qubit) : Unit is Adj + Ctl {
    body (...) { Y(q); }
    adjoint (...) { X(q); }
    controlled (cs, ...) { Controlled Z(cs, q); }
    controlled adjoint distribute;
  }
  operation AutoAll(q : Qubit) : Unit is Adj + Ctl {
    body (...) { X(q); }
    adjoint auto;
    controlled auto;
    controlled adjoint auto;
  }
  operation SelfAdj(q : Qubit) : Unit is Adj {
    body (...) { H(q); T(q); }
    adjoint self;
  }
  // H T H T on |0>: Adjoint SelfAdj applies the body again, not its inverse
  operation SelfAdjoint() : Result { use q = Qubit(); SelfAdj(q); Adjoint SelfAdj(q); H(q); return MResetZ(q); }
  // Adjoint A uses X -> One
  operation ExplicitAdjoint() : Result { use q = Qubit(); Adjoint A(q); return MResetZ(q); }
  // Controlled C uses CZ -> Zero
  operation ExplicitControlled() : Result { use (c, q) = (Qubit(), Qubit()); X(c); Controlled C([c], q); Reset(c); return MResetZ(q); }
  // Controlled Adjoint C inverts the controlled body (CZ) -> Zero
  operation InvertControlled() : Result { use (c, q) = (Qubit(), Qubit()); X(c); Controlled Adjoint C([c], q); Reset(c); return MResetZ(q); }
  // Controlled Adjoint A distributes the explicit adjoint (X) -> One
  operation DistributeAdjoint() : Result { use (c, q) = (Qubit(), Qubit()); X(c); Controlled Adjoint A([c], q); Reset(c); return MResetZ(q); }
  // explicit controlled adjoint (CX) -> One
  operation ExplicitControlledAdjoint() : Result { use (c, q) = (Qubit(), Qubit()); X(c); Controlled Adjoint CA([c], q); Reset(c); return MResetZ(q); }
  // controlled adjoint self = controlled (CZ) -> Zero
  operation ControlledAdjointSelf() : Result { use (c, q) = (Qubit(), Qubit()); X(c); Controlled Adjoint CS([c], q); Reset(c); return MResetZ(q); }
  // controlled adjoint distribute = controlled of the adjoint (X) -> One
  operation ControlledAdjointDistribute() : Result { use (c, q) = (Qubit(), Qubit()); X(c); Controlled Adjoint CD([c], q); Reset(c); return MResetZ(q); }
  // two controls, one off: nothing happens -> Zero
  operation TwoControls() : Result { use cs = Qubit[2]; use q = Qubit(); X(cs[0]); Controlled CA(cs, q); Controlled Adjoint CA(cs, q); ResetAll(cs); return MResetZ(q); }
  // generation directives only -> One
  operation GenerationDirectives() : Result { use (c, q) = (Qubit(), Qubit()); X(c); Controlled Adjoint AutoAll([c], q); Reset(c); return MResetZ(q); }
}
