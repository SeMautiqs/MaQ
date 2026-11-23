namespace Demo {
    // Teletransporte: el estado de msg pasa a target
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
}
