"""Compara las 3 opciones de esquema de particion para input + output a Ruspini overlap=1.0:
  A) Simetrico con shoulders (estandar academico): ambos inputs/outputs con hombros
  B) Simetrico triangular (sin shoulders): ambos con MFs completas dentro de [0,1]
  C) Asimetrico (actual): input sin shoulders, output con shoulders
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from FUZZY.fuzzy_controller_auto import make_partition_uniform, tri

OUT_DIR = os.path.join(HERE, "plots")
os.makedirs(OUT_DIR, exist_ok=True)

N = 5
LABELS = ["very_low", "low", "medium", "high", "very_high"]
x = np.linspace(0, 1, 1001)

# Tres configuraciones
configs = [
    ("A) Simetrico con shoulders (estandar)", True, True),
    ("B) Simetrico triangular (sin shoulders)", False, False),
    ("C) Asimetrico (actual)", False, True),
]

fig, axes = plt.subplots(3, 2, figsize=(13, 9))
for row, (title, sh_in, sh_out) in enumerate(configs):
    for col, (kind, shoulders, ylabel) in enumerate([
        ("I1 (input)", sh_in, r"$\mu(x)$"),
        ("O1 (output)", sh_out, r"$\mu(w)$"),
    ]):
        ax = axes[row, col]
        mfs = make_partition_uniform(N, overlap=1.0, shoulders=shoulders)
        sum_mu = np.zeros_like(x)
        for (a, b, c), lab in zip(mfs, LABELS):
            y = np.array([tri(xi, a, b, c) for xi in x])
            ax.plot(x, y, label=lab, linewidth=1.4)
            ax.fill_between(x, y, alpha=0.10)
            sum_mu += y
        ax.plot(x, sum_mu, "k--", linewidth=1.0, label=r"$\sum \mu_i$")
        ax.axhline(1.0, color="gray", linewidth=0.4, alpha=0.4)
        ax.set_title(f"{kind}  -  {title}", fontsize=9)
        ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.05, 1.25)
        ax.set_xlabel("x"); ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3)
        if col == 0 and row == 0:
            ax.legend(loc="upper right", fontsize=7, ncol=2)
        # destacar ausencia de cobertura
        if not shoulders:
            ax.axvspan(0, mfs[0][1], color="red", alpha=0.05)
            ax.axvspan(mfs[-1][1], 1, color="red", alpha=0.05)

fig.suptitle(f"Comparacion de esquemas de particion (n_labels={N}, overlap=1.0)\n"
             f"Zonas rojas: regiones donde Sum mu < 1 (cobertura parcial)", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.95])
out = os.path.join(OUT_DIR, "compare_3_schemes.png")
fig.savefig(out, dpi=140)
plt.close(fig)
print(f"  saved: {out}")
