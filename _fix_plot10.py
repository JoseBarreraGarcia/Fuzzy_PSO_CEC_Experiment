# -*- coding: utf-8 -*-
"""Fix remaining labels in plot 10 of wea_analysis.py."""

with open('FUZZY/3.-WEA2026/wea_analysis.py', encoding='utf-8') as f:
    content = f.read()

mj = '\u00e2\u02c6\u2019'  # corrupted minus sign (3-char mojibake sequence)
changes = 0

# =========================================================
# PLOT 10 – cbar label  (literal \n in file = \\n in Python string)
# =========================================================
old_cbar = "cbar_kws={'label': '(avg_gap_3L " + mj + " avg_gap_5L) / avg_gap_3L\\n(+) = 5L better, (" + mj + ") = 3L better'})"
new_cbar = "cbar_kws={'label': 'Relative Improvement\\n(Gap 3L - Gap 5L) / Gap 3L\\n(+) = 5L better,  (-) = 3L better'})"
n = content.count(old_cbar)
content = content.replace(old_cbar, new_cbar)
changes += n
print(f"  [10] cbar label: {n} replacement(s)")

# =========================================================
# PLOT 10 – insert grp_display before sns.heatmap + fix set_title
# =========================================================
old_block = (
    "        ax = axes[0, col_idx]\n"
    "        sns.heatmap(matrix, annot=True, fmt='.2f', cmap='RdYlGn',\n"
    "                    center=0, vmin=-max_abs, vmax=max_abs,\n"
    "                    ax=ax, linewidths=0.5, linecolor='white',\n"
    "                    cbar_kws={'label': 'Relative Improvement\\n(Gap 3L - Gap 5L) / Gap 3L\\n(+) = 5L better,  (-) = 3L better'})\n"
    "        ax.set_title(f'Relative Improvement by Average Gap \u2014 {grp_label}', fontsize=10)"
)
new_block = (
    "        ax = axes[0, col_idx]\n"
    "        grp_display = grp_label.replace('!= 0', '\u2260 0')\n"
    "        sns.heatmap(matrix, annot=True, fmt='.2f', cmap='RdYlGn',\n"
    "                    center=0, vmin=-max_abs, vmax=max_abs,\n"
    "                    ax=ax, linewidths=0.5, linecolor='white',\n"
    "                    cbar_kws={'label': 'Relative Improvement\\n(Gap 3L - Gap 5L) / Gap 3L\\n(+) = 5L better,  (-) = 3L better'})\n"
    "        ax.set_title(f'3L vs. 5L Granularity Effect  ({grp_display})', fontsize=10)"
)
n2 = content.count(old_block)
content = content.replace(old_block, new_block)
changes += n2
print(f"  [10] title block: {n2} replacement(s)")

print(f"\nTotal changes: {changes}")

with open('FUZZY/3.-WEA2026/wea_analysis.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("File saved OK")
