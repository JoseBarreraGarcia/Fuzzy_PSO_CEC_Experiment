"""Visualiza las particiones I1 (input) y O1 (output) generadas parametricamente
para n_labels in {3, 5, 7, 9} con la configuracion default de config/fuzzy_partitions.json.
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

from FUZZY.fuzzy_controller_auto import make_partition_uniform, tri, _load_partitions

OUT_DIR = os.path.join(HERE, "plots")
os.makedirs(OUT_DIR, exist_ok=True)

cfg = _load_partitions()
n_values = [3, 5, 7, 9]
x = np.linspace(0, 1, 501)


def plot_partition(ax, mfs, labels, title):
    for (a, b, c), lab in zip(mfs, labels):
        y = np.array([tri(xi, a, b, c) for xi in x])
        ax.plot(x, y, label=lab, linewidth=1.6)
        ax.fill_between(x, y, alpha=0.10)
    sum_mu = np.zeros_like(x)
    for (a, b, c) in mfs:
        sum_mu += np.array([tri(xi, a, b, c) for xi in x])
    ax.plot(x, sum_mu, "k--", alpha=0.4, linewidth=0.8, label=r"$\sum \mu_i$")
    ax.set_title(title, fontsize=10)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.05, 1.15)
    ax.set_xlabel("x")
    ax.set_ylabel(r"$\mu(x)$")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="upper right", fontsize=7, ncol=2)


for part_name in ["I1", "O1"]:
    part_cfg = cfg["partitions"][part_name]
    overlap = part_cfg["overlap"]
    shoulders = part_cfg["shoulders"]
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    fig.suptitle(
        f"Particion {part_name} (overlap={overlap}, shoulders={shoulders}) - scheme: {part_cfg['scheme']}",
        fontsize=11,
    )
    for ax, n in zip(axes.flatten(), n_values):
        mfs = make_partition_uniform(n, overlap=overlap, shoulders=shoulders)
        labels = part_cfg["labels_by_n"][str(n)]
        plot_partition(ax, mfs, labels, f"n_labels = {n}")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_path = os.path.join(OUT_DIR, f"partition_{part_name}_overview.png")
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"  saved: {out_path}")

print("\nDone.")
