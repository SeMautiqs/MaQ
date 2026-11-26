// Repeat-until-success: the call to M in the condition is evaluated at the end of the body
operation UntilOne() : Result {
    use q = Qubit();
    repeat {
        H(q);
    } until M(q) == One
    fixup {
        Reset(q);
    }
    Reset(q);
    return One;
}

operation Count() : Int {
    mutable k = 0;
    while k < 3 {
        set k += 1;
    }
    return k;
}

// RUS loop that counts its attempts: the counter makes the state space infinite,
// so states, check and mc need a depth (dist explores 200 steps by default)
operation Attempts() : Int {
    use q = Qubit();
    mutable n = 0;
    repeat {
        H(q);
        set n += 1;
    } until M(q) == One
    fixup {
        Reset(q);
    }
    Reset(q);
    return n;
}
