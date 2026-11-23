namespace Validation {

    // H T H |0>: P(One) = (2 - sqrt 2) / 4, unos 0,146
    operation Biased() : Result {
        use q = Qubit();
        H(q);
        T(q);
        H(q);
        let r = M(q);
        Reset(q);
        return r;
    }

    // H T T T H |0>: P(One) = (2 + sqrt 2) / 4, unos 0,854
    operation Biased3() : Result {
        use q = Qubit();
        H(q);
        for i in 1..3 { T(q); }
        H(q);
        let r = M(q);
        Reset(q);
        return r;
    }

    // dos qubits con fase relativa: distribución conjunta codificada como 2*ra + rb
    operation TwoQubitPhase() : Int {
        use a = Qubit();
        use b = Qubit();
        H(a);
        CNOT(a, b);
        T(a);
        H(a);
        H(b);
        mutable v = 0;
        if M(a) == One { set v += 2; }
        if M(b) == One { set v += 1; }
        ResetAll([a, b]);
        return v;
    }

    // Controlled S dos veces = CZ: interferencia en el objetivo
    operation ControlledPhase() : Int {
        use c = Qubit();
        use t = Qubit();
        H(c);
        H(t);
        Controlled S([c], t);
        Controlled T([c], t);
        H(t);
        mutable v = 0;
        if M(c) == One { set v += 2; }
        if M(t) == One { set v += 1; }
        ResetAll([c, t]);
        return v;
    }

    operation Prep(q : Qubit) : Unit is Adj + Ctl {
        H(q);
        T(q);
    }

    operation Teleport(msg : Qubit, target : Qubit) : Unit {
        use register = Qubit();
        H(register);
        CNOT(register, target);
        CNOT(msg, register);
        H(msg);
        if M(msg) == One { Z(target); }
        if M(register) == One { X(target); }
        Reset(register);
    }

    // se prepara un estado no trivial, se teletransporta y se deshace con
    // Adjoint Prep sobre el destino: siempre Zero
    operation TeleportCheck() : Result {
        use msg = Qubit();
        use target = Qubit();
        Prep(msg);
        Teleport(msg, target);
        Adjoint Prep(target);
        let r = M(target);
        Reset(msg);
        Reset(target);
        return r;
    }

    // RUS: repetir hasta One, y además contar con un bit extra cuántas
    // veces sale Zero en el primer intento (0 o 1)
    operation FirstAttempt() : Int {
        use q = Qubit();
        H(q);
        T(q);
        H(q);
        mutable first = 1;
        if M(q) == One { set first = 0; }
        Reset(q);
        repeat {
            H(q);
        } until M(q) == One
        fixup {
            Reset(q);
        }
        Reset(q);
        return first;
    }
}
