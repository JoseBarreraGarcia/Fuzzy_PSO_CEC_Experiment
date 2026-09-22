"""Generate compact figure for Block B1: effective number of active rules
per (input_set, granularity), publication-ready (single column)."""
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CSV = "Resultados/clei2026_b1/rule_activation_summary.csv"
OUT_PDF = "FUZZY/2.-CLEI2026/figures/b1_rule_activation.pdf"
OUT_PNG = "FUZZY/2.-CLEI2026/figures/b1_rule_activation.png"
os.makedirs(os.path.dirname(OUT_PDF), exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 8,
    "axes.labelsize": 8,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
})

df = pd.read_csv(CSV)
inputs = ["I1", "I2", "I3", "I4"]
gran = ["3L", "5L"]
x = np.arange(len(inputs))
width = 0.38

fig, ax = plt.subplots(figsize=(3.2, 1.7))
for i, g in enumerate(gran):
    vals = [df[(df.granularity == g) & (df.input_set == s)].effective_active_rules.iloc[0]
            for s in inputs]
    bars = ax.bar(x + (i - 0.5) * width, vals, width, label=g,
                  edgecolor="black", linewidth=0.4,
                  color=("#4C72B0" if g == "3L" else "#DD8452"))
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.015, f"{v:.2f}",
                ha="center", va="bottom", fontsize=6)

ax.axhline(1.0, color="gray", linestyle=":", linewidth=0.6)
ax.set_xticks(x)
ax.set_xticklabels(["I1", "I2", "I3", "I4"])
ax.set_ylabel("$\\exp H$")
ax.set_ylim(0.92, 2.0)
ax.legend(title="Gran.", loc="upper left", frameon=False, handlelength=1.2,
          borderaxespad=0.2, labelspacing=0.2)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
plt.tight_layout(pad=0.2)
plt.savefig(OUT_PDF, bbox_inches="tight", pad_inches=0.02)
plt.savefig(OUT_PNG, bbox_inches="tight", dpi=300, pad_inches=0.02)
print("Saved compact figure")
