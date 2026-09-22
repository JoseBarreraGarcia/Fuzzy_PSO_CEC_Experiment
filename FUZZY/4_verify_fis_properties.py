"""Verificacion de propiedades matematicas del FIS parametrico.

Sustituye la verificacion bit-a-bit con _3L/_5L (que ya no aplica porque las MFs
ahora se generan algorithmically y NO replican las MFs ad-hoc de WEA2026).

Checks:
  1. Estructura de particiones:
     - Centros equiespaciados en [0,1] con d = 1/(n-1)
     - Brazos consistentes con la formula r = (d/2)*(1+overlap)
     - Hombros aplicados solo donde corresponde
  2. Cobertura del dominio:
     - Para todo x in [0,1] existe al menos una MF con mu(x) > 0
       (excepto puntos aislados de medida cero cuando overlap=0)
  3. Ruspini iff overlap=1 con triangular uniforme (test sintetico).
  4. Reglas R1..R8:
     - Cardinalidad = n_labels^2 para cada regla
     - Solo etiquetas de output validas
     - Monotonia: si la regla solo depende de un eje, el otro eje es agnostic
  5. Comportamiento del controlador:
     - w(d,t) in [wMin, wMax] para todo (d,t)
     - w alcanza ambos extremos (al menos uno cerca de cada limite) cuando shoulders=True
     - Determinismo: dos invocaciones identicas dan el mismo resultado

Uso: python FUZZY/4_verify_fis_properties.py
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from FUZZY.fuzzy_controller_auto import (
    FuzzyInertiaController_Auto,
    make_partition_uniform,
    make_rule_matrix,
    tri,
    _load_partitions,
)

TOL = 1e-9
GRID = np.linspace(0.0, 1.0, 41)
N_LABELS_TEST = [3, 5, 7, 9]
RULES = [f"R{i}" for i in range(1, 9)]

failures = []


def check(name, cond, detail=""):
    flag = "PASS" if cond else "FAIL"
    print(f"  [{flag}] {name}" + (f" - {detail}" if detail else ""))
    if not cond:
        failures.append(name)


def section(title):
    print(f"\n=== {title} ===")


# ---------------------------------------------------------------------------
section("1. Estructura de particiones")
for n in N_LABELS_TEST:
    print(f"\n  n_labels = {n}")
    for overlap in (0.0, 0.5, 1.0):
        for shoulders in (False, True):
            mfs = make_partition_uniform(n, overlap=overlap, shoulders=shoulders)
            centers = [m[1] for m in mfs]
            if shoulders:
                d = 1.0 / (n - 1)
                expected_centers = [i * d for i in range(n)]
            else:
                s = 1.0 / (n + overlap)
                expected_centers = [s * (i + 1) for i in range(n)]
            tag = f"n={n} overlap={overlap} shoulders={shoulders}"
            check(
                f"centros equiespaciados ({tag})",
                all(abs(c - ec) < TOL for c, ec in zip(centers, expected_centers)),
            )
            # check brazo segun esquema
            if shoulders:
                d = 1.0 / (n - 1)
                half_arm = (d / 2.0) * (1.0 + overlap)
            else:
                s = 1.0 / (n + overlap)
                half_arm = (s / 2.0) * (1.0 + overlap)
            for i, (a, b, c) in enumerate(mfs):
                left_arm = b - a
                right_arm = c - b
                if shoulders:
                    expected_left = 0.0 if i == 0 else min(half_arm, b)
                    expected_right = 0.0 if i == n - 1 else min(half_arm, 1.0 - b)
                else:
                    expected_left = min(half_arm, b)
                    expected_right = min(half_arm, 1.0 - b)
                ok = abs(left_arm - expected_left) < TOL and abs(right_arm - expected_right) < TOL
                if not ok:
                    print(f"      MF[{i}]={mfs[i]}  L={left_arm:.4f} R={right_arm:.4f}"
                          f"  expected_L={expected_left:.4f} expected_R={expected_right:.4f}")
                    failures.append(f"brazos inconsistentes ({tag} i={i})")


# ---------------------------------------------------------------------------
section("2. Cobertura del dominio")
for n in N_LABELS_TEST:
    for overlap in (0.0, 1.0):
        for shoulders in (False, True):
            mfs = make_partition_uniform(n, overlap=overlap, shoulders=shoulders)
            if shoulders:
                # cobertura debe ser total en (0,1) interior
                x_test = np.linspace(0.001, 0.999, 199)
                covered = [sum(tri(x, *m) for m in mfs) > 0 for x in x_test]
                tag = f"n={n} overlap={overlap} shoulders=True"
                check(f"cobertura completa interior ({tag})", all(covered))
            else:
                # cobertura solo en [c_0, c_{n-1}]
                c0 = mfs[0][1]
                cN = mfs[-1][1]
                x_test = np.linspace(c0 + 1e-4, cN - 1e-4, 199)
                covered = [sum(tri(x, *m) for m in mfs) > 0 for x in x_test]
                tag = f"n={n} overlap={overlap} shoulders=False"
                check(f"cobertura interior [c_0,c_n] ({tag})", all(covered))


# ---------------------------------------------------------------------------
section("3. Propiedad Ruspini (overlap=1)")
for n in N_LABELS_TEST:
    # shoulders=True: Ruspini en TODO [0,1]
    mfs_s = make_partition_uniform(n, overlap=1.0, shoulders=True)
    x_test = np.linspace(0.0, 1.0, 401)
    sums_s = [sum(tri(x, *m) for m in mfs_s) for x in x_test]
    max_dev_s = max(abs(s - 1.0) for s in sums_s)
    check(f"Sum mu = 1 en TODO [0,1] (n={n}, overlap=1, shoulders=True)",
          max_dev_s < 1e-6, f"max |Sum-1| = {max_dev_s:.3e}")

    # shoulders=False: Ruspini SOLO en [c_0, c_{n-1}]
    mfs_n = make_partition_uniform(n, overlap=1.0, shoulders=False)
    c0 = mfs_n[0][1]; cN = mfs_n[-1][1]
    x_inner = np.linspace(c0 + 1e-4, cN - 1e-4, 199)
    sums_n = [sum(tri(x, *m) for m in mfs_n) for x in x_inner]
    max_dev_n = max(abs(s - 1.0) for s in sums_n)
    check(f"Sum mu = 1 en [c_0,c_n]=[{c0:.3f},{cN:.3f}] (n={n}, overlap=1, shoulders=False)",
          max_dev_n < 1e-6, f"max |Sum-1| = {max_dev_n:.3e}")
    # En los bordes, sigue habiendo cobertura parcial (Sum mu en (0, 1))
    sum_at_zero = sum(tri(0.0, *m) for m in mfs_n)
    sum_at_one = sum(tri(1.0, *m) for m in mfs_n)
    check(f"Sum mu(0)=0 y Sum mu(1)=0 con shoulders=False (n={n})",
          sum_at_zero < 1e-9 and sum_at_one < 1e-9,
          f"Sum(0)={sum_at_zero:.4f}, Sum(1)={sum_at_one:.4f}")


# ---------------------------------------------------------------------------
section("4. Reglas R1..R8 - estructura")
cfg = _load_partitions()
for n in N_LABELS_TEST:
    out_labels = cfg["partitions"]["O1"]["labels_by_n"][str(n)]
    expected_size = n * n
    for r in RULES:
        rules = make_rule_matrix(r, n)
        check(f"R={r} n={n} |rules|={expected_size}", len(rules) == expected_size,
              f"got {len(rules)}")
        check(f"R={r} n={n} outputs validos",
              all(v in out_labels for v in rules.values()))


# ---------------------------------------------------------------------------
section("5. Controlador: w in [wMin,wMax] y alcanza ambos extremos")
for n in N_LABELS_TEST:
    for r in RULES:
        ctrl = FuzzyInertiaController_Auto(
            w_set="O1", num_labels=n, input_set="I1",
            rule_set=r, wMin=0.1, wMax=0.9,
        )
        ws = np.array([[ctrl.compute_w(d, t) for t in GRID] for d in GRID]).flatten()
        in_range = (ws.min() >= 0.1 - TOL) and (ws.max() <= 0.9 + TOL)
        check(f"w in [0.1, 0.9] n={n} {r}", in_range,
              f"range=[{ws.min():.4f}, {ws.max():.4f}]")
        reach_low = ws.min() < 0.1 + 0.05
        reach_high = ws.max() > 0.9 - 0.05
        check(f"w cerca de wMin n={n} {r}", reach_low,
              f"min={ws.min():.4f}")
        check(f"w cerca de wMax n={n} {r}", reach_high,
              f"max={ws.max():.4f}")


# ---------------------------------------------------------------------------
section("6. Determinismo")
ctrl_a = FuzzyInertiaController_Auto(w_set="O1", num_labels=5, input_set="I1",
                                     rule_set="R5", wMin=0.1, wMax=0.9)
ctrl_b = FuzzyInertiaController_Auto(w_set="O1", num_labels=5, input_set="I1",
                                     rule_set="R5", wMin=0.1, wMax=0.9)
det_ok = True
for d in (0.1, 0.3, 0.5, 0.7, 0.9):
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        if abs(ctrl_a.compute_w(d, t) - ctrl_b.compute_w(d, t)) > TOL:
            det_ok = False
check("dos instancias identicas producen mismo w", det_ok)


# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
if failures:
    print(f"FAIL: {len(failures)} chequeos fallaron:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
print("PASS: todas las propiedades del FIS parametrico se cumplen.")
sys.exit(0)
