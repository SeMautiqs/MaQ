// Repeat-until-success: la llamada a M en la condición se evalúa al final del cuerpo
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
