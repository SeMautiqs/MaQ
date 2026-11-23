operation Main() : Bool {
    use qs = Qubit[3];
    H(qs[0]);
    for i in 1..Length(qs) - 1 {
        CNOT(qs[0], qs[i]);
    }
    mutable ones = 0;
    for q in qs {
        if M(q) == One { set ones += 1; }
    }
    ResetAll(qs);
    return ones == 0 or ones == 3;
}
