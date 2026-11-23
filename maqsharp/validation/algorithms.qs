namespace Algorithms {

    // ---------- Deutsch–Jozsa with 3 input qubits ----------

    // constant f equal to 1
    operation ConstantOracle(xs : Qubit[], y : Qubit) : Unit {
        X(y);
    }

    // f(x) = x0 xor x1, balanced
    operation BalancedOracle(xs : Qubit[], y : Qubit) : Unit {
        CNOT(xs[0], y);
        CNOT(xs[1], y);
    }

    // returns true if the measured input is 000, i.e., f is constant
    operation DJConstant() : Bool {
        use xs = Qubit[3];
        use y = Qubit();
        X(y);
        H(y);
        for q in xs { H(q); }
        ConstantOracle(xs, y);
        for q in xs { H(q); }
        mutable zeros = true;
        for q in xs {
            if M(q) == One { set zeros = false; }
        }
        ResetAll(xs);
        Reset(y);
        return zeros;
    }

    operation DJBalanced() : Bool {
        use xs = Qubit[3];
        use y = Qubit();
        X(y);
        H(y);
        for q in xs { H(q); }
        BalancedOracle(xs, y);
        for q in xs { H(q); }
        mutable zeros = true;
        for q in xs {
            if M(q) == One { set zeros = false; }
        }
        ResetAll(xs);
        Reset(y);
        return zeros;
    }

    // ---------- Bernstein–Vazirani, secret 101 ----------

    operation BernsteinVazirani() : Int {
        use xs = Qubit[3];
        use y = Qubit();
        X(y);
        H(y);
        for q in xs { H(q); }
        CNOT(xs[0], y);
        CNOT(xs[2], y);
        for q in xs { H(q); }
        mutable s = 0;
        if M(xs[0]) == One { set s += 4; }
        if M(xs[1]) == One { set s += 2; }
        if M(xs[2]) == One { set s += 1; }
        ResetAll(xs);
        Reset(y);
        return s;
    }

    // ---------- Grover ----------

    // 2 qubits, marked element 11: one iteration finds it with probability 1
    operation Grover2() : Int {
        use a = Qubit();
        use b = Qubit();
        H(a);
        H(b);
        // oracle: phase -1 on |11>
        CZ(a, b);
        // diffusion
        H(a);
        H(b);
        X(a);
        X(b);
        CZ(a, b);
        X(a);
        X(b);
        H(a);
        H(b);
        mutable v = 0;
        if M(a) == One { set v += 2; }
        if M(b) == One { set v += 1; }
        Reset(a);
        Reset(b);
        return v;
    }

    // 3 qubits, marked element 101: two iterations, probability 121/128
    operation Grover3() : Int {
        use qs = Qubit[3];
        for q in qs { H(q); }
        for it in 1..2 {
            // oracle: phase -1 on |101>
            X(qs[1]);
            Controlled Z([qs[0], qs[1]], qs[2]);
            X(qs[1]);
            // diffusion
            for q in qs { H(q); }
            for q in qs { X(q); }
            Controlled Z([qs[0], qs[1]], qs[2]);
            for q in qs { X(q); }
            for q in qs { H(q); }
        }
        mutable v = 0;
        if M(qs[0]) == One { set v += 4; }
        if M(qs[1]) == One { set v += 2; }
        if M(qs[2]) == One { set v += 1; }
        ResetAll(qs);
        return v;
    }

    // ---------- Superdense coding: the four messages ----------

    operation SuperdenseAll() : Bool {
        mutable ok = true;
        for msg in 0..3 {
            use a = Qubit();
            use b = Qubit();
            H(a);
            CNOT(a, b);
            if msg == 1 {
                X(a);
            } elif msg == 2 {
                Z(a);
            } elif msg == 3 {
                X(a);
                Z(a);
            }
            CNOT(a, b);
            H(a);
            mutable decoded = 0;
            if M(a) == One { set decoded += 2; }
            if M(b) == One { set decoded += 1; }
            set ok = ok and decoded == msg;
            Reset(a);
            Reset(b);
        }
        return ok;
    }

    // ---------- Entanglement swapping ----------

    // two Bell pairs (a,b) and (c,d); Bell measurement on b and c with
    // corrections on d; at the end a and d form a Bell pair
    operation EntanglementSwapping() : Bool {
        use a = Qubit();
        use b = Qubit();
        use c = Qubit();
        use d = Qubit();
        H(a);
        CNOT(a, b);
        H(c);
        CNOT(c, d);
        CNOT(b, c);
        H(b);
        if M(c) == One { X(d); }
        if M(b) == One { Z(d); }
        // undo the Bell pair (a,d): |00> must remain
        CNOT(a, d);
        H(a);
        let ok = M(a) == Zero and M(d) == Zero;
        Reset(a);
        Reset(b);
        Reset(c);
        Reset(d);
        return ok;
    }
}
