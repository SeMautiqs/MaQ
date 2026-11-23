namespace Demo {
    import Std.Intrinsic.*;

    // Bell pair: both measurements always agree
    @EntryPoint()
    operation Main() : Bool {
        use a = Qubit();
        use b = Qubit();
        H(a);
        CNOT(a, b);
        let same = M(a) == M(b);
        Reset(a);
        Reset(b);
        return same;
    }
}
