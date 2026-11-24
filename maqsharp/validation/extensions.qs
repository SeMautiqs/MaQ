// Regression tests for the constructs of the extended subset. Each operation
// is compared with the Q# simulator by validate.py.
namespace Extensions {
    import Std.Diagnostics.*;
    import Std.Arrays.*;

    // tuples as values and types, use of a tuple of qubits, implicit return
    operation BellTuple() : (Result, Result) {
        use (a, b) = (Qubit(), Qubit());
        H(a);
        CNOT(a, b);
        Std.Diagnostics.DumpMachine();
        (MResetZ(a), MResetZ(b))
    }

    // let and for with tuple patterns, assignments without set, ternary
    operation TuplePatterns() : Int {
        let (x, y) = (3, 4);
        mutable s = 0;
        for (p, q) in [(1, 2), (x, y)] {
            s += p * q;
        }
        s = s > 10 ? s | 0;
        s
    }

    // empty arrays, concatenation, slices, integer division and remainder
    operation Arrays() : Int {
        mutable a = [];
        for i in 1..5 {
            a += [i];
        }
        let b = a[1...];
        let c = a[...1];
        let d = a[1..2];
        Length(b) * 1000 + c[1] * 100 + d[1] * 10 + (17 / 5) % 2
    }

    // MResetEachZ and ApplyToEach, Message and Fact ignored
    operation EachQubit() : Result[] {
        use qs = Qubit[3];
        ApplyToEach(H, qs);
        Fact(Length(qs) == 3, "three qubits");
        Message($"Prepared {Length(qs)} qubits");
        MResetEachZ(qs)
    }

    // an operation passed as an argument, applied with Controlled
    operation ApplyTwice(op : Qubit => Unit is Adj + Ctl, q : Qubit) : Unit is Adj + Ctl {
        op(q);
        op(q);
    }

    operation OperationArgument() : (Result, Result, Result) {
        use (c, a, b) = (Qubit(), Qubit(), Qubit());
        H(c);
        Controlled ApplyTwice([c], (X, a));
        X(a);
        Controlled SWAP([c], (a, b));
        (MResetZ(c), MResetZ(a), MResetZ(b))
    }

    // Pauli measurements of the prelude: parities of a Bell pair
    operation PauliParities() : (Result, Result, Result) {
        use (a, b) = (Qubit(), Qubit());
        H(a);
        CNOT(a, b);
        let zz = Measure([PauliZ, PauliZ], [a, b]);
        let xx = Measure([PauliX, PauliX], [a, b]);
        let x = Measure([PauliX], [a]);
        ResetAll([a, b]);
        (zz, xx, x)
    }

    // ApplyControlledOnInt and the array functions of the prelude
    operation ControlledOnInt() : Result[] {
        use qs = Qubit[3];
        H(Head(qs));
        ApplyControlledOnInt(1, X, Most(qs), Tail(qs));
        MResetEachZ(qs)
    }

    // fail is reported as a stuck execution; here it is never reached
    operation FailNotReached() : Int {
        use q = Qubit();
        if M(q) == One {
            fail "unreachable";
        }
        7
    }

    // shadowing: redeclaration in the same scope and in inner blocks; set
    // updates the innermost binding, and closing a block recovers the outer one
    operation Shadowing() : (Int, Int, Result) {
        let x = 1;
        let x = x + 1;
        mutable y = 10;
        for i in 0..1 {
            let x = i;
            mutable y = x;
            set y += 100;
        }
        if x == 2 {
            set y += 1;
            let y = 0;
        }
        use q = Qubit();
        H(q);
        let r = M(q);
        if r == One {
            let r = Zero;
            X(q);
        }
        (x, y, r)
    }
}
