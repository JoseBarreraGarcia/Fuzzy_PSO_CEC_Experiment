"""Compara la superficie w(d,t) para overlap=0 vs overlap=1.0 (Ruspini).
Muestra por que Ruspini produce una superficie suave y overlap=0 una escalonada.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from FUZZY.fuzzy_controller_auto import FuzzyInertiaController_Auto, make_partition_uniform, tri

OUT_DIR = os.path.join(HERE, "plots")
os.makedirs(OUT_DIR, exist_ok=True)

N_LABELS = 5
RULE = "R5"
GRID = np.linspace(0.001, 0.999, 51)
DD, TT = np.meshgrid(GRID, GRID)


def build_surface(overlap, shoulders_in, shoulders_out):
    # parchea config en memoria
    from FUZZY import fuzzy_controller_auto as fca
    fca._load_partitions.cache_clear()
    import json
    cfg_path = os.path.join(ROOT, "config", "fuzzy_partitions.json")
    cfg = json.load(open(cfg_path))
    cfg["partitions"]["I1"]["overlap"] = overlap
    cfg["partitions"]["I1"]["shoulders"] = shoulders_in
    cfg["partitions"]["O1"]["overlap"] = overlap
    cfg["partitions"]["O1"]["shoulders"] = shoulders_out
    tmp_path = os.path.join(ROOT, "config", "_tmp_overlap_test.json")
    json.dump(cfg, open(tmp_path, "w"), indent=2)
    ctrl = FuzzyInertiaController_Auto(
        w_set="O1", num_labels=N_LABELS, input_set="I1",
        rule_set=RULE, wMin=0.1, wMax=0.9,
        partitions_path=tmp_path,
    )
    W = np.zeros_like(DD)
    for i in range(DD.shape[0]):
        for j in range(DD.shape[1]):
            W[i, j] = ctrl.compute_w(DD[i, j], TT[i, j])
    os.remove(tmp_path)
    return W, ctrl


print("Computing surfaces...")
W_no, ctrl_no = build_surface(overlap=0.0, shoulders_in=False, shoulders_out=True)
W_rus, ctrl_rus = build_surface(overlap=1.0, shoulders_in=False, shoulders_out=True)

# Plot side-by-side
fig = plt.figure(figsize=(15, 6))

# Surface 1: overlap=0
ax1 = fig.add_subplot(1, 2, 1, projection="3d")
surf1 = ax1.plot_surface(DD, TT, W_no, cmap=cm.viridis, edgecolor="k", linewidth=0.2, alpha=0.9)
ax1.set_title(f"overlap=0  (sin solapamiento)\n n_labels={N_LABELS}, {RULE}", fontsize=10)
ax1.set_xlabel("diversity d"); ax1.set_ylabel("progress t"); ax1.set_zlabel("w")
ax1.set_zlim(0.1, 0.9)
fig.colorbar(surf1, ax=ax1, shrink=0.6)

# Surface 2: Ruspini
ax2 = fig.add_subplot(1, 2, 2, projection="3d")
surf2 = ax2.plot_surface(DD, TT, W_rus, cmap=cm.viridis, edgecolor="k", linewidth=0.2, alpha=0.9)
ax2.set_title(f"overlap=1.0 (Ruspini)\n n_labels={N_LABELS}, {RULE}", fontsize=10)
ax2.set_xlabel("diversity d"); ax2.set_ylabel("progress t"); ax2.set_zlabel("w")
ax2.set_zlim(0.1, 0.9)
fig.colorbar(surf2, ax=ax2, shrink=0.6)

fig.tight_layout()
out = os.path.join(OUT_DIR, f"compare_overlap_{RULE}_n{N_LABELS}_surfaces.png")
fig.savefig(out, dpi=140)
plt.close(fig)
print(f"  saved: {out}")

# Plot 2: particiones I1 lado a lado
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
x = np.linspace(0, 1, 501)
for ax, overlap, ttl in [
    (axes[0], 0.0, f"I1 overlap=0  (sin solapamiento)"),
    (axes[1], 1.0, f"I1 overlap=1.0 (Ruspini)"),
]:
    mfs = make_partition_uniform(N_LABELS, overlap=overlap, shoulders=False)
    labels = ["very_low", "low", "medium", "high", "very_high"]
    sum_mu = np.zeros_like(x)
    for (a, b, c), lab in zip(mfs, labels):
        y = np.array([tri(xi, a, b, c) for xi in x])
        ax.plot(x, y, label=lab, linewidth=1.6)
        ax.fill_between(x, y, alpha=0.10)
        sum_mu += y
    ax.plot(x, sum_mu, "k--", linewidth=1.0, label=r"$\sum \mu_i(x)$")
    ax.axhline(1.0, color="gray", linewidth=0.5, alpha=0.4)
    ax.set_title(ttl, fontsize=10)
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.05, 1.25)
    ax.set_xlabel("x"); ax.set_ylabel(r"$\mu(x)$")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=8, ncol=2)

fig.tight_layout()
out2 = os.path.join(OUT_DIR, f"compare_overlap_partitions_n{N_LABELS}.png")
fig.savefig(out2, dpi=140)
plt.close(fig)
print(f"  saved: {out2}")

# Diagnostico numerico
print("\nDiagnostico numerico:")
print(f"  overlap=0   : w range = [{W_no.min():.4f}, {W_no.max():.4f}]  std={W_no.std():.4f}")
print(f"  overlap=1.0 : w range = [{W_rus.min():.4f}, {W_rus.max():.4f}]  std={W_rus.std():.4f}")
# Discontinuidad: max gradiente local
def max_grad(W):
    gy, gx = np.gradient(W)
    return np.sqrt(gy**2 + gx**2).max()
print(f"  max |grad w| overlap=0   = {max_grad(W_no):.4f}  (mayor = mas escalonada)")
print(f"  max |grad w| overlap=1.0 = {max_grad(W_rus):.4f}")
