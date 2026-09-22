# -*- coding: utf-8 -*-
"""Fix professional labels and mojibake in plots 08 and 10 of wea_analysis.py."""

with open('FUZZY/3.-WEA2026/wea_analysis.py', encoding='utf-8') as f:
    content = f.read()

mojibake_minus = '\u00e2\u02c6\u2019'   # corrupted U+2212 (minus sign â€")

changes = 0

# =========================================================
# PLOT 08 – cbar label
# =========================================================
old = "cbar_kws={'label': '|fitness " + mojibake_minus + " optimum|'})"
new = "cbar_kws={'label': 'Average Gap to Optimum'})"
if old in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("  [08] cbar label fixed")
else:
    print("  [08] cbar label NOT found")

# =========================================================
# PLOT 08 – insert grp_display assignment + fix set_title
# =========================================================
old = (
    "        sns.heatmap(pivot, annot=True, fmt='.2e', cmap='RdYlGn_r', ax=ax,\n"
    "                    linewidths=0.5, linecolor='white',\n"
    "                    cbar_kws={'label': 'Average Gap to Optimum'})\n"
    "        ax.set_title(f'|fitness " + mojibake_minus + " optimum| \u2014 {grp_label}', fontsize=11)"
)
new = (
    "        grp_display = grp_label.replace('!= 0', '\u2260 0')\n"
    "        sns.heatmap(pivot, annot=True, fmt='.2e', cmap='RdYlGn_r', ax=ax,\n"
    "                    linewidths=0.5, linecolor='white',\n"
    "                    cbar_kws={'label': 'Average Gap to Optimum'})\n"
    "        ax.set_title(f'Average Gap to Optimum  ({grp_display})', fontsize=11)"
)
if old in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("  [08] title + grp_display fixed")
else:
    print("  [08] title block NOT found")

# =========================================================
# PLOT 08 – suptitle
# =========================================================
old = "plt.suptitle('Mean Absolute Gap to Optimum: Config \u00d7 Function', fontsize=13)"
new = "plt.suptitle('Mean Average Gap to Optimum per Configuration and Function', fontsize=13)"
if old in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("  [08] suptitle fixed")
else:
    print("  [08] suptitle NOT found")

# =========================================================
# PLOT 10 – cbar label  (two mojibake_minus instances)
# =========================================================
old = (
    "cbar_kws={'label': '(avg_gap_3L " + mojibake_minus + " avg_gap_5L) / avg_gap_3L\n"
    "(+) = 5L better, (" + mojibake_minus + ") = 3L better'})"
)
new = (
    "cbar_kws={'label': 'Relative Improvement\\n"
    "(Gap 3L - Gap 5L) / Gap 3L\\n"
    "(+) = 5L better,  (-) = 3L better'})"
)
if old in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("  [10] cbar label fixed")
else:
    print("  [10] cbar label NOT found")

# =========================================================
# PLOT 10 – insert grp_display assignment + fix set_title
# =========================================================
old = (
    "        sns.heatmap(matrix, annot=True, fmt='.2f', cmap='RdYlGn',\n"
    "                    center=0, vmin=-max_abs, vmax=max_abs,\n"
    "                    ax=ax, linewidths=0.5, linecolor='white',\n"
    "                    cbar_kws={'label': 'Relative Improvement\\n"
    "(Gap 3L - Gap 5L) / Gap 3L\\n"
    "(+) = 5L better,  (-) = 3L better'})\n"
    "        ax.set_title(f'Relative Improvement by Average Gap \u2014 {grp_label}', fontsize=10)"
)
new = (
    "        grp_display = grp_label.replace('!= 0', '\u2260 0')\n"
    "        sns.heatmap(matrix, annot=True, fmt='.2f', cmap='RdYlGn',\n"
    "                    center=0, vmin=-max_abs, vmax=max_abs,\n"
    "                    ax=ax, linewidths=0.5, linecolor='white',\n"
    "                    cbar_kws={'label': 'Relative Improvement\\n"
    "(Gap 3L - Gap 5L) / Gap 3L\\n"
    "(+) = 5L better,  (-) = 3L better'})\n"
    "        ax.set_title(f'3L vs. 5L Granularity Effect  ({grp_display})', fontsize=10)"
)
if old in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("  [10] title + grp_display fixed")
else:
    print("  [10] title block NOT found")

# =========================================================
# PLOT 10 – suptitle
# =========================================================
old = "plt.suptitle('Granularity Effect (3L vs 5L) Split by Optimum Group', fontsize=12)"
new = "plt.suptitle('Granularity Effect (3L vs. 5L): Relative Improvement by Average Gap to Optimum', fontsize=12)"
if old in content:
    content = content.replace(old, new, 1)
    changes += 1
    print("  [10] suptitle fixed")
else:
    print("  [10] suptitle NOT found")

# =========================================================
# Write back
# =========================================================
print(f"\nTotal changes: {changes}")
if changes > 0:
    with open('FUZZY/3.-WEA2026/wea_analysis.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("File saved OK")
else:
    print("Nothing changed – check search strings")
