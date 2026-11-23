operation Bad() : Unit {
    use q = Qubit();
    while M(q) == Zero { X(q); }
}
