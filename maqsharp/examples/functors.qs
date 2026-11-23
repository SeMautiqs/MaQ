namespace Functors {

    operation Prep(q : Qubit) : Unit is Adj + Ctl {
        H(q);
        S(q);
    }

    operation Flip(q : Qubit) : Unit is Adj + Ctl {
        X(q);
    }

    operation Rot(qs : Qubit[]) : Unit is Adj {
        for i in 0..Length(qs) - 1 {
            H(qs[i]);
            T(qs[i]);
        }
    }

    // Adjoint undoes Prep: always Zero
    operation AdjointUndo() : Result {
        use q = Qubit();
        Prep(q);
        Adjoint Prep(q);
        return M(q);
    }

    // Adjoint of a body with a loop: all qubits return to |0>
    operation AdjointLoop() : Bool {
        use qs = Qubit[2];
        Rot(qs);
        Adjoint Rot(qs);
        return M(qs[0]) == Zero and M(qs[1]) == Zero;
    }

    // Controlled X is CNOT: correlated measurements
    operation CtlX() : Bool {
        use c = Qubit();
        use t = Qubit();
        H(c);
        Controlled X([c], t);
        let same = M(c) == M(t);
        ResetAll([c, t]);
        return same;
    }

    // Toffoli with two controls: always One
    operation Toffoli() : Result {
        use a = Qubit();
        use b = Qubit();
        use t = Qubit();
        X(a);
        X(b);
        Controlled X([a, b], t);
        let r = M(t);
        ResetAll([a, b, t]);
        return r;
    }

    // Controlled applied to a user-defined operation
    operation CtlUser() : Bool {
        use c = Qubit();
        use t = Qubit();
        H(c);
        Controlled Flip([c], t);
        let same = M(c) == M(t);
        ResetAll([c, t]);
        return same;
    }

    // within/apply: H Z H = X, always One
    operation WithinApply() : Result {
        use q = Qubit();
        within { H(q); } apply { Z(q); }
        let r = M(q);
        Reset(q);
        return r;
    }

    // T^4 = Z, hence H T T T T H = X: always One
    operation TPhase() : Result {
        use q = Qubit();
        H(q);
        for i in 1..4 { T(q); }
        H(q);
        let r = M(q);
        Reset(q);
        return r;
    }

    // Adjoint T undoes T and Adjoint S undoes S
    operation TAdjoint() : Result {
        use q = Qubit();
        H(q);
        T(q);
        S(q);
        Adjoint S(q);
        Adjoint T(q);
        H(q);
        return M(q);
    }
}
