"""Validación de la semántica Q#-en-Maude frente al simulador oficial de Q#.

Para cada operación:
  - se ejecuta en el simulador de Q# (paquete qdk) N veces;
  - se calcula en Maude su distribución EXACTA con el comando dist;
  - para cada resultado se compara la frecuencia observada k/N con la
    probabilidad p mediante z = (k - N p) / sqrt(N p (1 - p)).
Un caso falla si algún |z| > 4, si aparece un resultado con p = 0 o si falta
uno con p = 1.

Uso:  python3 validation/validate.py [shots]
Requiere el binario maude en el PATH y MAUDE_LIB apuntando a su preludio.
"""
import math, os, re, subprocess, sys, warnings
from fractions import Fraction

warnings.filterwarnings("ignore")
os.environ.setdefault("QSHARP_PYTHON_TELEMETRY", "none")
from qdk import qsharp

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = int(sys.argv[1]) if len(sys.argv) > 1 else 4000

# (fichero, prefijo de espacio de nombres para Q#, operaciones)
CASES = [
    ("examples/bell.qs", "Demo.", ["Main"]),
    ("examples/ghz.qs", "", ["Main"]),
    ("examples/random.qs", "", ["CountOnes"]),
    ("examples/rus.qs", "", ["UntilOne", "Count"]),
    ("examples/functors.qs", "Functors.",
     ["AdjointUndo", "AdjointLoop", "CtlX", "Toffoli", "CtlUser", "WithinApply",
      "TPhase", "TAdjoint"]),
    ("validation/validation.qs", "Validation.",
     ["Biased", "Biased3", "TwoQubitPhase", "ControlledPhase", "TeleportCheck",
      "FirstAttempt"]),
    ("validation/algorithms.qs", "Algorithms.",
     ["DJConstant", "DJBalanced", "BernsteinVazirani", "Grover2", "Grover3",
      "SuperdenseAll", "EntanglementSwapping"]),
]


def norm(v):
    """Normaliza un valor de Maude o de Python a una cadena común."""
    s = str(v).strip()
    s = {"(true ).QBool": "True", "(false ).QBool": "False", "unit": "()",
         "Result.One": "One", "Result.Zero": "Zero"}.get(s, s)
    return s


def num(expr):
    """Evalúa numéricamente una probabilidad impresa por Maude."""
    e = expr.replace(".+", "+").replace(".*", "*").replace("./", "/")
    e = e.replace("Sqrt", "math.sqrt")
    e = re.sub(r"(\d+)/(\d+)", r"(\1/\2)", e)
    return float(eval(e, {"math": math}))


def maude_dists():
    cmds = []
    for f, _, ops in CASES:
        cmds.append(f"open {f}")
        cmds += [f"dist {op}" for op in ops]
    cmds.append("q")
    out = subprocess.run(
        ["maude", "-no-banner", "-no-advise", "-allow-files", "qsharp-io.maude"],
        input="\n".join(cmds) + "\n", capture_output=True, text=True, cwd=ROOT,
        timeout=1800).stdout
    # cada respuesta va tras un prompt; se unen las líneas partidas por Maude
    blocks = out.split("Q#> ")[1:]
    res = []
    for b in blocks:
        b = re.sub(r"\n\s{4,}", " ", b)
        if "resultado:" not in b:
            continue
        d, rest = {}, Fraction(0)
        for line in b.splitlines():
            m = re.match(r"\s*resultado: (.*?)\s+prob: (.*)$", line)
            if m:
                d[norm(m.group(1))] = num(m.group(2))
            m = re.match(r"\s*sin explorar.*: (.*)$", line)
            if m:
                rest = num(m.group(1))
            if "bloqueados" in line:
                d["<bloqueado>"] = num(line.split(":")[-1])
        res.append((d, float(rest)))
    return res


def main():
    dists = maude_dists()
    rows, i, all_ok = [], 0, True
    for f, ns, ops in CASES:
        qsharp.init()
        qsharp.eval(open(os.path.join(ROOT, f)).read())
        for op in ops:
            exact, rest = dists[i]
            i += 1
            shots = qsharp.run(f"{ns}{op}()", shots=SHOTS)
            counts = {}
            for r in shots:
                counts[norm(r)] = counts.get(norm(r), 0) + 1
            worst, ok = 0.0, "<bloqueado>" not in exact
            for v in set(exact) | set(counts):
                p, k = exact.get(v, 0.0), counts.get(v, 0)
                if p <= 1e-12 or p >= 1 - 1e-12:
                    if (p <= 1e-12 and k > 0) or (p >= 1 - 1e-12 and k < SHOTS):
                        ok = False
                    continue
                z = (k - SHOTS * p) / math.sqrt(SHOTS * p * (1 - p))
                worst = max(worst, abs(z))
            ok = ok and worst <= 4
            all_ok &= ok
            tv = 0.5 * sum(abs(exact.get(v, 0) - counts.get(v, 0) / SHOTS)
                           for v in set(exact) | set(counts))
            show = ", ".join(f"{v}: {exact[v]:.4f}" for v in sorted(exact))
            obs = ", ".join(f"{v}: {counts[v] / SHOTS:.4f}" for v in sorted(counts))
            rows.append((f"{os.path.basename(f)}:{op}", show, obs, worst, tv, rest, ok))
    w = max(len(r[0]) for r in rows)
    print(f"{'caso':<{w}}  {'max|z|':>6}  {'TV':>6}  ok   Maude (exacta)  |  Q# ({SHOTS} ejecuciones)")
    for name, show, obs, z, tv, rest, ok in rows:
        extra = f" (+{rest:.1e} sin explorar)" if rest else ""
        print(f"{name:<{w}}  {z:6.2f}  {tv:6.4f}  {'sí' if ok else 'NO':<3}  {show}{extra}  |  {obs}")
    print("\nTODOS LOS CASOS CORRECTOS" if all_ok else "\nHAY DISCREPANCIAS")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
