// Number of ones in n random bits: binomial distribution
operation RandomBit() : Result {
    use q = Qubit();
    H(q);
    let r = M(q);
    Reset(q);
    return r;
}

operation CountOnes() : Int {
    mutable c = 0;
    for i in 1..3 {
        if RandomBit() == One { set c += 1; }
    }
    return c;
}
