// Rotations by multiples of pi/4 (validation against the simulator).
namespace Rotations {
    import Std.Math.*;
    import Std.Convert.*;

    // Rz up to a global phase, inside an interference pattern.
    operation RzInterference() : Result {
        use q = Qubit();
        H(q);
        Rz(3.0 * PI() / 4.0, q);
        H(q);
        return MResetZ(q);
    }

    // Rx and Ry on two qubits, entangled afterwards.
    operation RxRyEntangled() : Result[] {
        use qs = Qubit[2];
        Rx(PI() / 2.0, qs[0]);
        Ry(-PI() / 2.0, qs[1]);
        CNOT(qs[0], qs[1]);
        Rx(3.0 * PI() / 2.0, qs[1]);
        return MResetEachZ(qs);
    }

    // Controlled rotations: the global phase of Rz becomes a relative phase.
    operation ControlledRz() : Result[] {
        use (c, t) = (Qubit(), Qubit());
        H(c);
        X(t);
        Controlled Rz([c], (PI() / 2.0, t));
        H(c);
        return [MResetZ(c), MResetZ(t)];
    }

    operation ControlledR1() : Result {
        use (c, t) = (Qubit(), Qubit());
        H(c);
        X(t);
        Controlled R1([t], (PI() / 4.0, c));
        Controlled R1([t], (PI() / 4.0, c));
        H(c);
        Reset(t);
        return MResetZ(c);
    }

    operation ControlledRxRy() : Result[] {
        use qs = Qubit[3];
        H(qs[0]);
        H(qs[1]);
        Controlled Rx([qs[0]], (PI() / 2.0, qs[2]));
        Controlled Ry(qs[0 .. 1], (PI(), qs[2]));
        H(qs[0]);
        return MResetEachZ(qs);
    }

    // Adjoint rotations, R with a Pauli argument, and angles computed in a loop.
    operation AdjointAndR() : Result[] {
        use qs = Qubit[2];
        H(qs[0]);
        R(PauliX, PI() / 2.0, qs[1]);
        Adjoint Rz(PI() / 2.0, qs[0]);
        Adjoint R(PauliY, -PI() / 2.0, qs[1]);
        H(qs[0]);
        return MResetEachZ(qs);
    }

    operation AngleLoop() : Result {
        use q = Qubit();
        H(q);
        for k in 1 .. 3 {
            R1(IntAsDouble(k) * PI() / 4.0, q);
        }
        H(q);
        return MResetZ(q);
    }

    // Quantum Fourier transform on three qubits: on |101> followed by H on
    // every qubit (which depends on the phases), and followed by its adjoint.
    operation ApplyQFT3(qs : Qubit[]) : Unit is Adj + Ctl {
        H(qs[0]);
        Controlled R1([qs[1]], (PI() / 2.0, qs[0]));
        Controlled R1([qs[2]], (PI() / 4.0, qs[0]));
        H(qs[1]);
        Controlled R1([qs[2]], (PI() / 2.0, qs[1]));
        H(qs[2]);
        SWAP(qs[0], qs[2]);
    }

    operation QFT3() : Result[] {
        use qs = Qubit[3];
        X(qs[0]);
        X(qs[2]);
        ApplyQFT3(qs);
        ApplyToEach(H, qs);
        return MResetEachZ(qs);
    }

    operation QFT3Inverse() : Result[] {
        use qs = Qubit[3];
        X(qs[0]);
        X(qs[2]);
        ApplyQFT3(qs);
        Adjoint ApplyQFT3(qs);
        return MResetEachZ(qs);
    }
}
