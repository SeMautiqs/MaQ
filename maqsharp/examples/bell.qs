namespace Demo {
    import Std.Intrinsic.*;

    // Par de Bell: las dos medidas coinciden siempre
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
