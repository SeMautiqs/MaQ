"""Runs the seeded faults of validation/faults.qs on the QDK simulator.

The teleportation variants are tested as a simulator user would: the message is
prepared in a state, teleported, the preparation is undone on the target, and
the target is measured; any One is a failure. The script prints the percentage
of failing shots for each input, whether superdense coding returns false, and
the frequencies of Grover's search.

    python3 validation/faults_qdk.py
"""
import collections
import os
import warnings

warnings.filterwarnings("ignore")
os.environ.setdefault("QSHARP_PYTHON_TELEMETRY", "none")
from qdk import qsharp
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import seeded_run  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = 1000

HARNESS = '''
namespace Harness {
    open Faults;
    // input states: |0>, |1>, |+>, |->, S|+>, and a generic one
    operation Prep(k : Int, q : Qubit) : Unit is Adj {
        if k == 1 { X(q); }
        elif k == 2 { H(q); }
        elif k == 3 { X(q); H(q); }
        elif k == 4 { H(q); S(q); }
        elif k == 5 { Ry(1.0, q); Rz(0.7, q); }
    }
    operation Test(f : Int, k : Int) : Bool {
        use (m, t) = (Qubit(), Qubit());
        Prep(k, m);
        if f == 1 { TeleportNoZ(m, t); }
        elif f == 2 { TeleportSwapped(m, t); }
        else { TeleportLeak(m, t); }
        Adjoint Prep(k, t);
        let ok = M(t) == Zero;
        Reset(m);
        Reset(t);
        return ok;
    }
}
'''

INPUTS = ["|0>", "|1>", "|+>", "|->", "S|+>", "generic"]


def main():
    qsharp.init()
    qsharp.eval(open(os.path.join(HERE, "faults.qs")).read() + HARNESS)
    for f, name in [(1, "TeleportNoZ"), (2, "TeleportSwapped"), (3, "TeleportLeak")]:
        cells = []
        for k, inp in enumerate(INPUTS):
            try:
                res = seeded_run(f"Harness.Test({f}, {k})", SHOTS)
                fails = sum(1 for x in res if x is not True)
                cells.append(f"{inp}: {100 * fails / SHOTS:.0f}%")
            except Exception as e:  # e.g. a qubit released in a nonzero state
                cells.append(f"{inp}: error ({str(e).splitlines()[0]})")
        print(f"{name:16} " + "  ".join(cells))
    res = seeded_run("Faults.SuperdenseWrongDecoder()", SHOTS)
    print(f"SuperdenseWrongDecoder  false in {100 * sum(1 for x in res if x is False) / SHOTS:.1f}% of the shots")
    res = seeded_run("Faults.GroverExtraIteration()", 4 * SHOTS)
    freq = collections.Counter(res)
    print("GroverExtraIteration    " + "  ".join(f"{v}: {freq[v] / (4 * SHOTS):.3f}" for v in range(8)))


if __name__ == "__main__":
    main()
