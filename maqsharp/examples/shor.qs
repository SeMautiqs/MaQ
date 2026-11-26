// Shor's nine-qubit code. ShorEncode, ShorDetectError, and their helpers are
// the reference solutions of the Quantum Katas (qec_shor), unchanged.
namespace Kata {
    operation ShorEncode (qs : Qubit[]) : Unit is Adj + Ctl {
        BitflipEncode(qs[0 .. 3 .. 8]);
        ApplyToEachCA(H, qs[0 .. 3 .. 8]);
        for i in 0 .. 2 {
            BitflipEncode(qs[3 * i .. 3 * i + 2]);
        }
    }

    operation BitflipEncode (qs : Qubit[]) : Unit is Adj + Ctl {
        CNOT(qs[0], qs[1]);
        CNOT(qs[0], qs[2]);
    }

    operation ShorDetectError (qs : Qubit[]) : (Int, Pauli) {
        // Detect X error first
        mutable x_ind = -1;
        for i in 0 .. 2 {
            let err_ind = BitflipDetectError(qs[3 * i .. 3 * i + 2]);
            if err_ind > -1 {
                set x_ind = 3 * i + err_ind;
            }
        }

        // Detect Z error
        mutable z_ind = -1;
        let m1 = Measure([PauliX, size = 6], qs[0 .. 5]);
        let m2 = Measure([PauliX, size = 6], qs[3 .. 8]);

        if m1 == Zero and m2 == Zero {
            set z_ind = -1;
        } elif m1 == One and m2 == Zero {
            set z_ind = 0;
        } elif m1 == One and m2 == One {
            set z_ind = 1;
        } elif m1 == Zero and m2 == One {
            set z_ind = 2;
        }

        // Combine both errors into return value
        if x_ind == -1 and z_ind == -1 {
            return (-1, PauliI);
        }
        if x_ind > -1 and z_ind > -1 {
            return (x_ind, PauliY);
        }
        if x_ind > -1 {
            return (x_ind, PauliX);
        }
        return (z_ind, PauliZ);
    }

    operation BitflipDetectError (qs : Qubit[]) : Int {
        let m1 = Measure([PauliZ, PauliZ], qs[0 .. 1]);
        let m2 = Measure([PauliZ, PauliZ], qs[1 .. 2]);

        if m1 == One and m2 == Zero {
            return 0;
        } elif m1 == One and m2 == One {
            return 1;
        } elif m1 == Zero and m2 == One {
            return 2;
        } else {
            return -1;
        }
    }

    // An error on qubit i: 1 = X, 2 = Y, 3 = Z, other = none.
    operation ApplyError (qs : Qubit[], i : Int, err : Int) : Unit {
        if err == 1 {
            X(qs[i]);
        } elif err == 2 {
            Y(qs[i]);
        } elif err == 3 {
            Z(qs[i]);
        }
    }

    // Undo the error reported by ShorDetectError. A Z error on a qubit of
    // block k is corrected by Z on the first qubit of the block.
    operation Correct (qs : Qubit[], ind : Int, p : Pauli) : Unit {
        if p == PauliX {
            X(qs[ind]);
        } elif p == PauliY {
            Y(qs[ind]);
        } elif p == PauliZ {
            Z(qs[3 * ind]);
        }
    }

    // Encode the state of data, apply the error err on qubit i, detect it,
    // correct it, and decode.
    operation ShorRoundTrip (data : Qubit, i : Int, err : Int) : Unit {
        use anc = Qubit[8];
        let qs = [data] + anc;
        ShorEncode(qs);
        ApplyError(qs, i, err);
        let (ind, p) = ShorDetectError(qs);
        Correct(qs, ind, p);
        Adjoint ShorEncode(qs);
    }

    // Two X errors in the same block: beyond what the code corrects.
    operation ShorTwoErrors (data : Qubit) : Unit {
        use anc = Qubit[8];
        let qs = [data] + anc;
        ShorEncode(qs);
        X(qs[0]);
        X(qs[1]);
        let (ind, p) = ShorDetectError(qs);
        Correct(qs, ind, p);
        Adjoint ShorEncode(qs);
    }

    // Every single-qubit error, on the state H T |0>, whose round trip is
    // checked by measuring after undoing the preparation (validation).
    operation ShorAllErrors () : Result[] {
        mutable rs = [];
        for i in 0 .. 8 {
            for err in 1 .. 3 {
                use data = Qubit();
                H(data);
                T(data);
                ShorRoundTrip(data, i, err);
                Adjoint T(data);
                H(data);
                set rs += [MResetZ(data)];
            }
        }
        return rs;
    }
}
