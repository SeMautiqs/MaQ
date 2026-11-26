namespace AutoQRUS {
    // repeat-until-success programs of the AutoQ 2.0 benchmarks (TACAS 2025),
    // translated gate by gate; qb[0] is anc and qb[1] is t

    operation Figure7(anc : Qubit, t : Qubit) : Unit {
        H(anc);
        Adjoint T(anc);
        H(anc);
        CZ(anc, t);
        H(t);
        T(t);
        H(t);
        Adjoint T(t);
        H(t);
        CZ(anc, t);
        H(anc);
        Adjoint T(anc);
        H(anc);
        X(anc);
        mutable r = M(anc);
        while r == Zero {
            Z(t);
            H(anc);
            Adjoint T(anc);
            H(anc);
            CZ(anc, t);
            H(t);
            T(t);
            H(t);
            Adjoint T(t);
            H(t);
            CZ(anc, t);
            H(anc);
            Adjoint T(anc);
            H(anc);
            X(anc);
            set r = M(anc);
        }
        Reset(anc);
    }

    operation Figure8(anc : Qubit, t : Qubit) : Unit {
        H(anc);
        T(anc);
        CNOT(anc, t);
        H(anc);
        CNOT(anc, t);
        T(anc);
        H(anc);
        X(anc);
        mutable r = M(anc);
        while r == Zero {
            H(anc);
            T(anc);
            CNOT(anc, t);
            H(anc);
            CNOT(anc, t);
            T(anc);
            H(anc);
            X(anc);
            set r = M(anc);
        }
        Reset(anc);
    }

    operation Figure9(anc : Qubit, t : Qubit) : Unit {
        H(anc);
        T(anc);
        H(anc);
        CZ(anc, t);
        Adjoint T(anc);
        H(anc);
        T(anc);
        CZ(anc, t);
        Z(t);
        H(anc);
        T(anc);
        H(anc);
        X(anc);
        mutable r = M(anc);
        while r == Zero {
            H(anc);
            T(anc);
            H(anc);
            CZ(anc, t);
            Adjoint T(anc);
            H(anc);
            T(anc);
            CZ(anc, t);
            Z(t);
            H(anc);
            T(anc);
            H(anc);
            X(anc);
            set r = M(anc);
        }
        Reset(anc);
    }

    operation Figure10a(anc : Qubit, t : Qubit) : Unit {
        H(anc);
        T(anc);
        H(anc);
        Adjoint T(anc);
        H(anc);
        CZ(anc, t);
        S(anc);
        H(anc);
        T(anc);
        H(anc);
        Adjoint T(anc);
        H(anc);
        S(anc);
        CZ(anc, t);
        H(anc);
        T(anc);
        H(anc);
        Adjoint T(anc);
        H(anc);
        Z(t);
        X(anc);
        mutable r = M(anc);
        while r == Zero {
            H(anc);
            T(anc);
            H(anc);
            Adjoint T(anc);
            H(anc);
            CZ(anc, t);
            S(anc);
            H(anc);
            T(anc);
            H(anc);
            Adjoint T(anc);
            H(anc);
            S(anc);
            CZ(anc, t);
            H(anc);
            T(anc);
            H(anc);
            Adjoint T(anc);
            H(anc);
            Z(t);
            X(anc);
            set r = M(anc);
        }
        Reset(anc);
    }

    operation Figure10b(anc : Qubit, t : Qubit) : Unit {
        H(anc);
        S(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        Adjoint S(anc);
        H(anc);
        CZ(anc, t);
        H(anc);
        S(anc);
        H(anc);
        T(anc);
        H(anc);
        X(t);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        CZ(anc, t);
        H(anc);
        S(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        S(anc);
        H(anc);
        X(t);
        mutable r = M(anc);
        while r == Zero {
            Z(t);
            H(anc);
            S(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            Adjoint S(anc);
            H(anc);
            CZ(anc, t);
            H(anc);
            S(anc);
            H(anc);
            T(anc);
            H(anc);
            X(t);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            CZ(anc, t);
            H(anc);
            S(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            S(anc);
            H(anc);
            X(t);
            set r = M(anc);
        }
        Reset(anc);
    }

    operation Figure10c(anc : Qubit, t : Qubit) : Unit {
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        CZ(anc, t);
        H(anc);
        S(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        S(anc);
        H(anc);
        X(t);
        CZ(anc, t);
        H(anc);
        T(anc);
        H(anc);
        T(anc);
        H(anc);
        X(t);
        mutable r = M(anc);
        while r == Zero {
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            CZ(anc, t);
            H(anc);
            S(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            S(anc);
            H(anc);
            X(t);
            CZ(anc, t);
            H(anc);
            T(anc);
            H(anc);
            T(anc);
            H(anc);
            X(t);
            set r = M(anc);
        }
        Reset(anc);
    }

}
