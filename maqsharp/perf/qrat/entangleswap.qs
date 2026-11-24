// QRAT's ENTANGLE_SWAP; returns true iff q0 and q3 end in the Bell state |phi+>
operation EntangleSwap() : Bool {
    use (q0, q1, q2, q3) = (Qubit(), Qubit(), Qubit(), Qubit());
    H(q0); CNOT(q0, q1);
    H(q2); CNOT(q2, q3);
    CNOT(q1, q2); H(q1);
    if M(q2) == One { X(q3); }
    if M(q1) == One { Z(q3); }
    CNOT(q0, q3); H(q0);
    let ok = M(q0) == Zero and M(q3) == Zero;
    ResetAll([q0, q1, q2, q3]);
    return ok;
}
