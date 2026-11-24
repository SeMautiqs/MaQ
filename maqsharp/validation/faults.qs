// Seeded faults (RQ3): variants of the programs of the validation with one
// injected bug each. The commands that detect them are in validation/faults.txt.
namespace Faults {
    // F1: teleportation without the Z correction
    operation TeleportNoZ(msg : Qubit, target : Qubit) : Unit {
        use register = Qubit();
        H(register);
        CNOT(register, target);
        CNOT(msg, register);
        H(msg);
        if M(register) == One { X(target); }
        Reset(register);
    }

    // F2: teleportation with the two corrections swapped
    operation TeleportSwapped(msg : Qubit, target : Qubit) : Unit {
        use register = Qubit();
        H(register);
        CNOT(register, target);
        CNOT(msg, register);
        H(msg);
        if M(msg) == One { X(target); }
        if M(register) == One { Z(target); }
        Reset(register);
    }

    // F3: teleportation that does not reset the auxiliary qubit (qubit leak)
    operation TeleportLeak(msg : Qubit, target : Qubit) : Unit {
        use register = Qubit();
        H(register);
        CNOT(register, target);
        CNOT(msg, register);
        H(msg);
        if M(msg) == One { Z(target); }
        if M(register) == One { X(target); }
    }

    // F4: superdense coding whose decoder applies H before CNOT
    operation SuperdenseWrongDecoder() : Bool {
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
            H(a);
            CNOT(a, b);
            mutable decoded = 0;
            if M(a) == One { set decoded += 2; }
            if M(b) == One { set decoded += 1; }
            set ok = ok and decoded == msg;
            Reset(a);
            Reset(b);
        }
        return ok;
    }

    // F5: Grover's search on 3 qubits with one iteration too many
    operation GroverExtraIteration() : Int {
        use qs = Qubit[3];
        for q in qs { H(q); }
        for it in 1..3 {
            X(qs[1]);
            Controlled Z([qs[0], qs[1]], qs[2]);
            X(qs[1]);
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
}
