// QRAT's LOOP: q := |1>; H[q]; while M[q] = 1 do H[q]; od
operation Loop() : Result {
    use q = Qubit();
    X(q);
    H(q);
    mutable r = M(q);
    while r == One {
        H(q);
        set r = M(q);
    }
    Reset(q);
    return r;
}
