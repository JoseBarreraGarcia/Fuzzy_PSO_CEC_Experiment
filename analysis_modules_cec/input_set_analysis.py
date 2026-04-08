"""
Analysis: Effect of Input Fuzzy Set Configuration on PSO_FCS Performance

Factors analyzed (keeping rules and output w_set=A constant):
  - num_labels: 3 vs 5 linguistic labels for input variables
  - input_set: I1 (Standard), I2 (Narrow), I3 (Wide), I4 (Shoulder)

Data source: Resultados/resumen/level1_raw_cec/ben_mh_comparison.csv
"""

import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# ── LNCS-style formatting ──────────────────────────────────────────────────
plt.rcParams.update({
    'figure.figsize': (7.5, 5),
    'font.family': 'Times New Roman',
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8,
})
sns.set_style("whitegrid")
DPI = 300

# ── Load data ───────────────────────────────────────────────────────────────
df_comp = pd.read_csv('Resultados/resumen/level1_raw_cec/ben_mh_comparison.csv')
df_runs = pd.read_csv('Resultados/resumen/level1_raw_cec/ben_experiments_all_runs.csv')

OUTPUT_DIR = 'Resultados/resumen/input_set_analysis'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Parse MH name into components ──────────────────────────────────────────
def parse_mh(mh):
    """Parse PSO_FCS:A:3:I1 -> (w_set=A, num_labels=3, input_set=I1)"""
    if mh == 'PSO':
        return pd.Series({'w_set': None, 'num_labels': None, 'input_set': None, 'is_fuzzy': False})
    parts = mh.split(':')
    return pd.Series({
        'w_set': parts[1] if len(parts) > 1 else None,
        'num_labels': int(parts[2]) if len(parts) > 2 else None,
        'input_set': parts[3] if len(parts) > 3 else None,
        'is_fuzzy': True,
    })

# Parse for both dataframes
for df in [df_comp, df_runs]:
    parsed = df['MH'].apply(parse_mh)
    for col in parsed.columns:
        df[col] = parsed[col]

# Only fuzzy variants (exclude base PSO)
df_fcs = df_comp[df_comp['is_fuzzy'] == True].copy()
df_fcs_runs = df_runs[df_runs['is_fuzzy'] == True].copy()

# Functions that benefit from gap analysis (non-zero optima)
FUNCTIONS_GAP = ['F21', 'F22', 'F23']
FUNCTIONS_ALL = sorted(df_comp['funcion'].unique())
# Explicit order for subplot grids: unimodal top row, multimodal bottom row
FUNCTIONS_ORDERED = ['F1', 'F5', 'F11', 'F21', 'F22', 'F23']

# ── Color/marker definitions ───────────────────────────────────────────────
COLORS_INPUT = {'I1': '#2CA02C', 'I2': '#D62728', 'I3': '#1F77B4', 'I4': '#FF7F0E'}
MARKERS_LABELS = {3: 'o', 5: 's'}
INPUT_NAMES = {'I1': 'Standard', 'I2': 'Narrow', 'I3': 'Wide', 'I4': 'Shoulder'}

print("=" * 70)
print("ANALYSIS: INPUT FUZZY SET EFFECT ON PSO_FCS PERFORMANCE")
print("  w_set = A (constant), rules = constant")
print("  Variables: num_labels (3,5) × input_set (I1,I2,I3,I4)")
print("=" * 70)

# ═══════════════════════════════════════════════════════════════════════════
# TABLE 1: Mean Gap (%) by input_set × num_labels for Shekel functions
# ═══════════════════════════════════════════════════════════════════════════
print("\n── TABLE 1: Mean Gap to Optimum (%) - Shekel Functions (F21-F23) ──")

df_gap = df_fcs[df_fcs['funcion'].isin(FUNCTIONS_GAP)].copy()
pivot_gap = df_gap.pivot_table(
    values='gap_pct_medio',
    index='input_set',
    columns=['num_labels', 'funcion'],
    aggfunc='mean'
).round(2)

# Compute average across functions per (input_set, num_labels)
avg_gap = df_gap.groupby(['input_set', 'num_labels'])['gap_pct_medio'].mean().round(2)
avg_gap_pivot = avg_gap.unstack('num_labels')
avg_gap_pivot.columns = [f'Avg_Gap_{nl}L' for nl in avg_gap_pivot.columns]

print(pivot_gap.to_string())
print("\nAverage Gap across F21-F23:")
print(avg_gap_pivot.to_string())

# Save CSV
avg_gap.reset_index().to_csv(os.path.join(OUTPUT_DIR, 'gap_by_input_num_labels.csv'), index=False)

# ═══════════════════════════════════════════════════════════════════════════
# TABLE 2: Mean Fitness by input_set × num_labels for ALL functions
# ═══════════════════════════════════════════════════════════════════════════
print("\n── TABLE 2: Mean Fitness by input_set × num_labels (all functions) ──")

pivot_fitness = df_fcs.pivot_table(
    values='fitness_mean',
    index=['funcion'],
    columns=['input_set', 'num_labels'],
    aggfunc='mean'
).round(4)

print(pivot_fitness.to_string())
pivot_fitness.to_csv(os.path.join(OUTPUT_DIR, 'fitness_by_input_num_labels.csv'))

# ═══════════════════════════════════════════════════════════════════════════
# TABLE 3: Ranking by input_set across all functions
# ═══════════════════════════════════════════════════════════════════════════
print("\n── TABLE 3: Ranking Analysis ──")

# Rank within each function (1 = best fitness_mean)
df_fcs_ranked = df_fcs.copy()
df_fcs_ranked['rank'] = df_fcs_ranked.groupby('funcion')['fitness_mean'].rank(method='min')

# Average rank by input_set and num_labels
rank_summary = df_fcs_ranked.groupby(['input_set', 'num_labels'])['rank'].mean().round(2)
rank_pivot = rank_summary.unstack('num_labels')
rank_pivot.columns = [f'{nl}_labels' for nl in rank_pivot.columns]
rank_pivot = rank_pivot.sort_values(rank_pivot.columns[0])

print("Average Rank (1=best) across all functions:")
print(rank_pivot.to_string())
rank_pivot.to_csv(os.path.join(OUTPUT_DIR, 'ranking_input_num_labels.csv'))

# ═══════════════════════════════════════════════════════════════════════════
# TABLE 4: Std deviation analysis (robustness)
# ═══════════════════════════════════════════════════════════════════════════
print("\n── TABLE 4: Robustness (Average Std) ──")

std_summary = df_fcs.groupby(['input_set', 'num_labels']).agg(
    avg_fitness_std=('fitness_std', 'mean'),
    avg_time=('tiempo_medio', 'mean')
).round(4)
print(std_summary.to_string())
std_summary.to_csv(os.path.join(OUTPUT_DIR, 'robustness_input_num_labels.csv'))

# ═══════════════════════════════════════════════════════════════════════════
# PLOT 1: Heatmap (input_set × num_labels) — split A (unimodal) / B (multimodal)
# ═══════════════════════════════════════════════════════════════════════════
FUNCS_UNIMODAL = ['F1', 'F5', 'F11']
FUNCS_MULTIMODAL = ['F21', 'F22', 'F23']

# 1A: Unimodal — fitness_mean
fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
for idx, func in enumerate(FUNCS_UNIMODAL):
    ax = axes[idx]
    df_f = df_fcs[df_fcs['funcion'] == func]
    heat_data = df_f.pivot_table(values='fitness_mean', index='input_set', columns='num_labels')
    heat_data.columns = [f'{c}L' for c in heat_data.columns]
    heat_data = heat_data.reindex(['I1', 'I2', 'I3', 'I4'])
    sns.heatmap(heat_data, annot=True, fmt='.1f', cmap='RdYlGn_r', ax=ax,
                cbar=idx == 2, linewidths=0.5, linecolor='white')
    ax.set_title(func, fontweight='bold')
    ax.set_xlabel('Num. Labels')
    ax.set_ylabel('Input Set' if idx == 0 else '')
fig.suptitle('Mean Fitness by Input Config — Unimodal Functions\nw_set=A, rules constant',
             fontsize=11, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '01a_heatmap_unimodal.png'), dpi=DPI, bbox_inches='tight')
plt.close()
print("\n[OK] 01a_heatmap_unimodal.png saved")

# 1B: Multimodal — gap_pct_medio
fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
for idx, func in enumerate(FUNCS_MULTIMODAL):
    ax = axes[idx]
    df_f = df_fcs[df_fcs['funcion'] == func]
    heat_data = df_f.pivot_table(values='gap_pct_medio', index='input_set', columns='num_labels')
    heat_data.columns = [f'{c}L' for c in heat_data.columns]
    heat_data = heat_data.reindex(['I1', 'I2', 'I3', 'I4'])
    sns.heatmap(heat_data, annot=True, fmt='.1f', cmap='RdYlGn_r', ax=ax,
                cbar=idx == 2, vmin=10, vmax=40,
                linewidths=0.5, linecolor='white')
    ax.set_title(func, fontweight='bold')
    ax.set_xlabel('Num. Labels')
    ax.set_ylabel('Input Set' if idx == 0 else '')
fig.suptitle('Gap to Optimum (%) by Input Config — Multimodal Functions\nw_set=A, rules constant',
             fontsize=11, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '01b_heatmap_multimodal.png'), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] 01b_heatmap_multimodal.png saved")

# ═══════════════════════════════════════════════════════════════════════════
# PLOT 2: Per-function bar chart — 3L vs 5L by input_set, split A/B
# ═══════════════════════════════════════════════════════════════════════════
input_sets = ['I1', 'I2', 'I3', 'I4']
width = 0.35

def _plot_bar_3vs5(funcs_list, metric, ylabel, title_suffix, filename):
    fig, axes = plt.subplots(1, len(funcs_list), figsize=(5 * len(funcs_list), 5))
    if len(funcs_list) == 1:
        axes = [axes]
    for idx, func in enumerate(funcs_list):
        ax = axes[idx]
        df_f = df_fcs[df_fcs['funcion'] == func]
        by_config = df_f.groupby(['input_set', 'num_labels'])[metric].mean()
        x = np.arange(len(input_sets))
        for i, nl in enumerate([3, 5]):
            vals = [by_config.get((iset, nl), np.nan) for iset in input_sets]
            bars = ax.bar(x + i * width - width/2, vals, width, label=f'{nl} labels',
                          color=['#4ECDC4', '#FF6B6B'][i], alpha=0.85, edgecolor='black', linewidth=0.5)
            for bar, v in zip(bars, vals):
                if not np.isnan(v):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.01,
                            f'{v:.1f}', ha='center', va='bottom', fontsize=7, fontweight='bold')
        ax.set_xlabel('Input Fuzzy Set')
        if idx == 0:
            ax.set_ylabel(ylabel)
        ax.set_title(func, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([f'{k}\n({INPUT_NAMES[k]})' for k in input_sets], fontsize=8)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis='y')
    fig.suptitle(f'3 vs 5 Labels: {title_suffix}\nw_set=A, rules constant',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=DPI, bbox_inches='tight')
    plt.close()

_plot_bar_3vs5(FUNCS_UNIMODAL, 'fitness_mean', 'Mean Fitness',
               'Mean Fitness — Unimodal Functions', '02a_3vs5_bar_unimodal.png')
print("[OK] 02a_3vs5_bar_unimodal.png saved")

_plot_bar_3vs5(FUNCS_MULTIMODAL, 'gap_pct_medio', 'Gap to Optimum (%)',
               'Gap to Optimum — Multimodal Functions', '02b_3vs5_bar_multimodal.png')
print("[OK] 02b_3vs5_bar_multimodal.png saved")

# ═══════════════════════════════════════════════════════════════════════════
# PLOT 3: Per-function boxplot — distribution by input_set, split A/B
# ═══════════════════════════════════════════════════════════════════════════
def _plot_boxplot_by_input(funcs_list, metric, ylabel, title_suffix, filename):
    fig, axes = plt.subplots(1, len(funcs_list), figsize=(5 * len(funcs_list), 5))
    if len(funcs_list) == 1:
        axes = [axes]
    order = [f'{iset}:{nl}L' for iset in ['I1','I2','I3','I4'] for nl in [3,5]]
    colors_cfg = [COLORS_INPUT[iset] for iset in ['I1','I2','I3','I4'] for _ in [3,5]]
    for idx, func in enumerate(funcs_list):
        ax = axes[idx]
        df_f = df_fcs_runs[df_fcs_runs['funcion'] == func].copy()
        df_f['config'] = df_f['input_set'] + ':' + df_f['num_labels'].astype(int).astype(str) + 'L'
        bp_data = [df_f[df_f['config'] == cfg][metric].dropna().values for cfg in order]
        bp = ax.boxplot(bp_data, tick_labels=order, patch_artist=True, showmeans=True,
                        meanprops=dict(marker='x', markeredgecolor='black', markersize=6),
                        widths=0.6)
        for patch, c in zip(bp['boxes'], colors_cfg):
            patch.set_facecolor(c)
            patch.set_alpha(0.7)
        ax.set_xticklabels(order, rotation=45, ha='right', fontsize=7)
        if idx == 0:
            ax.set_ylabel(ylabel)
        ax.set_title(func, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    fig.suptitle(f'{title_suffix}\nw_set=A, rules constant',
                 fontsize=11, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=DPI, bbox_inches='tight')
    plt.close()

_plot_boxplot_by_input(FUNCS_UNIMODAL, 'fitness', 'Fitness',
                       'Fitness Distribution — Unimodal Functions', '03a_boxplot_unimodal.png')
print("[OK] 03a_boxplot_unimodal.png saved")

_plot_boxplot_by_input(FUNCS_MULTIMODAL, 'gap_optimo_pct', 'Gap to Optimum (%)',
                       'Gap Distribution — Multimodal Functions', '03b_boxplot_multimodal.png')
print("[OK] 03b_boxplot_multimodal.png saved")

# ═══════════════════════════════════════════════════════════════════════════
# PLOT 4: Scatter — Mean Fitness vs Std by input_set (per function)
# ═══════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(2, 3, figsize=(14, 9))
axes = axes.flatten()

for idx, func in enumerate(FUNCTIONS_ORDERED):
    ax = axes[idx]
    df_f = df_fcs[df_fcs['funcion'] == func]
    
    # Plot in order I1, I2, I3, I4 × 3L, 5L so legend is consistent
    for iset in ['I1', 'I2', 'I3', 'I4']:
        for nl in [3, 5]:
            row_data = df_f[(df_f['input_set'] == iset) & (df_f['num_labels'] == nl)]
            if len(row_data) == 0:
                continue
            row = row_data.iloc[0]
            ax.scatter(row['fitness_mean'], row['fitness_std'],
                       c=COLORS_INPUT[iset], marker=MARKERS_LABELS[nl],
                       s=90, edgecolors='black', linewidth=0.5, zorder=3)
    
    # Also plot PSO baseline
    pso_row = df_comp[(df_comp['funcion'] == func) & (df_comp['MH'] == 'PSO')]
    if len(pso_row) > 0:
        ax.scatter(pso_row['fitness_mean'].values[0], pso_row['fitness_std'].values[0],
                   c='red', marker='*', s=170, edgecolors='black', linewidth=0.5,
                   zorder=4, label='PSO')
    
    ax.set_title(func, fontweight='bold', fontsize=12)
    ax.set_xlabel('Mean Fitness', fontsize=11)
    ax.set_ylabel('Std Dev', fontsize=11)
    ax.tick_params(labelsize=10)
    ax.grid(True, alpha=0.3)

# Legend — ordered: I1, I2, I3, I4, then markers, then PSO
from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS_INPUT['I1'],
           markersize=10, markeredgecolor='black', label='I1 (Standard)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS_INPUT['I2'],
           markersize=10, markeredgecolor='black', label='I2 (Narrow)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS_INPUT['I3'],
           markersize=10, markeredgecolor='black', label='I3 (Wide)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS_INPUT['I4'],
           markersize=10, markeredgecolor='black', label='I4 (Shoulder)'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
           markersize=10, markeredgecolor='black', label='\u25CB = 3 labels'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='gray',
           markersize=10, markeredgecolor='black', label='\u25A1 = 5 labels'),
    Line2D([0], [0], marker='*', color='w', markerfacecolor='red',
           markersize=14, markeredgecolor='black', label='PSO (baseline)'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=4, fontsize=10,
           bbox_to_anchor=(0.5, -0.02))

fig.suptitle('Mean Fitness vs Std Dev by Input Config\nw_set=A, rules constant',
             fontsize=13, fontweight='bold')
plt.tight_layout(rect=[0, 0.06, 1, 0.95])
plt.savefig(os.path.join(OUTPUT_DIR, '04_scatter_fitness_std.png'), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] 04_scatter_fitness_std.png saved")

# ═══════════════════════════════════════════════════════════════════════════
# TABLE (was Plot 5): Ranking data — saved as CSV only
# ═══════════════════════════════════════════════════════════════════════════
rank_data = df_fcs_ranked.groupby(['input_set', 'num_labels'])['rank'].mean()
rank_detail = df_fcs_ranked.pivot_table(
    values='rank', index='funcion',
    columns=['input_set', 'num_labels'], aggfunc='mean'
).round(2)
rank_detail.to_csv(os.path.join(OUTPUT_DIR, '05_ranking_per_function.csv'))
print("[OK] 05_ranking_per_function.csv saved (table only, no plot)")

# ═══════════════════════════════════════════════════════════════════════════
# PLOT 6: Per-function comparison — best input_set winner
# ═══════════════════════════════════════════════════════════════════════════
print("\n── TABLE 5: Winner per Function ──")
winners = []
for func in FUNCTIONS_ORDERED:
    df_f = df_fcs[df_fcs['funcion'] == func].sort_values('fitness_mean')
    best = df_f.iloc[0]
    winners.append({
        'Function': func,
        'Best_Config': f"{best['input_set']}:{int(best['num_labels'])}L",
        'Input_Set': best['input_set'],
        'Num_Labels': int(best['num_labels']),
        'Fitness_Mean': round(best['fitness_mean'], 4),
        'Gap_%': round(best['gap_pct_medio'], 4),
    })

df_winners = pd.DataFrame(winners)
print(df_winners.to_string(index=False))
df_winners.to_csv(os.path.join(OUTPUT_DIR, 'winners_per_function.csv'), index=False)

# Count wins
print("\nWin count by input_set:")
print(df_winners['Input_Set'].value_counts().to_string())
print("\nWin count by num_labels:")
print(df_winners['Num_Labels'].value_counts().to_string())

# ═══════════════════════════════════════════════════════════════════════════
# PSO vs PSO_FCS COMPARISON
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("PSO (traditional) vs PSO_FCS (fuzzy controlled)")
print("=" * 70)

df_pso = df_comp[df_comp['MH'] == 'PSO'].copy()

# TABLE: PSO vs best FCS and vs avg FCS per function
print("\n── TABLE 6: PSO vs PSO_FCS per Function ──")
comparison_rows = []
for func in FUNCTIONS_ORDERED:
    pso = df_pso[df_pso['funcion'] == func]
    fcs_func = df_fcs[df_fcs['funcion'] == func]
    
    if len(pso) == 0 or len(fcs_func) == 0:
        continue
    
    pso_mean = pso['fitness_mean'].values[0]
    pso_std = pso['fitness_std'].values[0]
    pso_min = pso['fitness_min'].values[0]
    
    best_fcs = fcs_func.loc[fcs_func['fitness_mean'].idxmin()]
    avg_fcs_mean = fcs_func['fitness_mean'].mean()
    avg_fcs_std = fcs_func['fitness_std'].mean()
    
    # For minimization: negative improvement = FCS is worse
    if pso_mean != 0:
        improv_best = ((pso_mean - best_fcs['fitness_mean']) / abs(pso_mean)) * 100
        improv_avg = ((pso_mean - avg_fcs_mean) / abs(pso_mean)) * 100
    else:
        improv_best = pso_mean - best_fcs['fitness_mean']
        improv_avg = pso_mean - avg_fcs_mean
    
    # Determine winner
    # For Shekel (negative fitness, lower=better): PSO wins if pso_mean < fcs_mean
    pso_wins_vs_best = pso_mean < best_fcs['fitness_mean']
    pso_wins_vs_avg = pso_mean < avg_fcs_mean
    
    comparison_rows.append({
        'Function': func,
        'PSO_Mean': round(pso_mean, 4),
        'PSO_Std': round(pso_std, 4),
        'Best_FCS': f"{best_fcs['input_set']}:{int(best_fcs['num_labels'])}L",
        'BestFCS_Mean': round(best_fcs['fitness_mean'], 4),
        'BestFCS_Std': round(best_fcs['fitness_std'], 4),
        'AvgFCS_Mean': round(avg_fcs_mean, 4),
        'Improv_BestFCS_%': round(improv_best, 2),
        'Improv_AvgFCS_%': round(improv_avg, 2),
        'Winner_vs_Best': 'PSO' if pso_wins_vs_best else 'FCS',
        'Winner_vs_Avg': 'PSO' if pso_wins_vs_avg else 'FCS',
    })

df_comparison = pd.DataFrame(comparison_rows)
print(df_comparison.to_string(index=False))
df_comparison.to_csv(os.path.join(OUTPUT_DIR, 'pso_vs_psofcs_comparison.csv'), index=False)

# Win count
pso_wins_best = sum(1 for r in comparison_rows if r['Winner_vs_Best'] == 'PSO')
fcs_wins_best = sum(1 for r in comparison_rows if r['Winner_vs_Best'] == 'FCS')
pso_wins_avg = sum(1 for r in comparison_rows if r['Winner_vs_Avg'] == 'PSO')
fcs_wins_avg = sum(1 for r in comparison_rows if r['Winner_vs_Avg'] == 'FCS')

print(f"\nPSO vs Best FCS config:  PSO wins {pso_wins_best}/{len(comparison_rows)}, FCS wins {fcs_wins_best}/{len(comparison_rows)}")
print(f"PSO vs Avg FCS configs:  PSO wins {pso_wins_avg}/{len(comparison_rows)}, FCS wins {fcs_wins_avg}/{len(comparison_rows)}")

# ── TABLE (was Plot 6): PSO vs PSO_FCS per-function — saved as CSV only ──
print("[OK] pso_vs_psofcs_comparison.csv already saved (table only, no plot)")

# ── PLOT 7: PSO vs best FCS — relative improvement (from raw 31 runs) ────
# For each function, identify best FCS config (by mean fitness from df_comp),
# then compute mean fitness from the 31 raw runs for both PSO and that config.
df_pso_runs_all = df_runs[df_runs['MH'] == 'PSO']
improv_runs_rows = []
for func in FUNCTIONS_ORDERED:
    pso_runs = df_pso_runs_all[df_pso_runs_all['funcion'] == func]['fitness'].dropna()
    fcs_func = df_fcs[df_fcs['funcion'] == func]
    if len(pso_runs) == 0 or len(fcs_func) == 0:
        continue
    best_fcs_mh = fcs_func.loc[fcs_func['fitness_mean'].idxmin(), 'MH']
    fcs_runs = df_runs[(df_runs['MH'] == best_fcs_mh) & (df_runs['funcion'] == func)]['fitness'].dropna()
    pso_mean_runs = pso_runs.mean()
    fcs_mean_runs = fcs_runs.mean()
    if pso_mean_runs != 0:
        improv = ((pso_mean_runs - fcs_mean_runs) / abs(pso_mean_runs)) * 100
    else:
        improv = pso_mean_runs - fcs_mean_runs
    improv_runs_rows.append({'Function': func, 'Improv_%': round(improv, 2),
                             'PSO_Mean_31': round(pso_mean_runs, 4),
                             'BestFCS_Mean_31': round(fcs_mean_runs, 4),
                             'Best_FCS': best_fcs_mh})

df_improv = pd.DataFrame(improv_runs_rows)
df_improv.to_csv(os.path.join(OUTPUT_DIR, '07_pso_vs_best_fcs_improvement.csv'), index=False)

# Split into two groups by scale: unimodal (F1,F5,F11) and multimodal (F21-F23)
FUNCS_UNIMODAL = ['F1', 'F5', 'F11']
FUNCS_MULTIMODAL = ['F21', 'F22', 'F23']

def _plot_improvement_barh(df_rows, funcs_subset, filename, subtitle):
    """Helper to plot horizontal bar chart for a subset of functions."""
    subset = [r for r in df_rows if r['Function'] in funcs_subset]
    # Ensure the order matches funcs_subset
    subset_sorted = sorted(subset, key=lambda r: funcs_subset.index(r['Function']))
    funcs_s = [r['Function'] for r in subset_sorted]
    vals_s = [r['Improv_%'] for r in subset_sorted]
    colors_s = ["#4275C1" if v > 0 else "#8E4646" for v in vals_s]

    fig, ax = plt.subplots(figsize=(9, 3.5))
    # Reverse so first function is at top
    bars = ax.barh(funcs_s[::-1], vals_s[::-1],
                   color=colors_s[::-1], edgecolor='black', linewidth=0.5, alpha=0.85)

    for bar, v in zip(bars, vals_s[::-1]):
        x_pos = bar.get_width()
        # Place label inside the bar
        if v >= 0:
            ha = 'right' if abs(v) > 2 else 'left'
            x_text = x_pos * 0.95 if abs(v) > 2 else x_pos + abs(x_pos) * 0.05 + 0.3
            color = 'white' if abs(v) > 2 else 'black'
        else:
            ha = 'left' if abs(v) > 2 else 'right'
            x_text = x_pos * 0.95 if abs(v) > 2 else x_pos - abs(x_pos) * 0.05 - 0.3
            color = 'white' if abs(v) > 2 else 'black'
        ax.text(x_text, bar.get_y() + bar.get_height()/2,
                f'{v:+.1f}%', ha=ha, va='center', fontsize=10, fontweight='bold',
                color=color)

    ax.axvline(x=0, color='black', linewidth=1)
    ax.set_xlabel('Relative Improvement of PSO_FCS over PSO (%)\\n'
                  '(positive/green = PSO_FCS better; negative/red = PSO better)',
                  fontsize=10)
    ax.set_title(f'PSO vs Best PSO_FCS: Mean of 31 Runs — {subtitle}',
                 fontweight='bold', fontsize=12)
    ax.grid(True, alpha=0.3, axis='x')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=DPI, bbox_inches='tight')
    plt.close()

_plot_improvement_barh(improv_runs_rows, FUNCS_UNIMODAL,
                       '07a_improvement_unimodal.png', 'Unimodal Functions (F1, F5, F11)')
print("[OK] 07a_improvement_unimodal.png saved")

_plot_improvement_barh(improv_runs_rows, FUNCS_MULTIMODAL,
                       '07b_improvement_multimodal.png', 'Multimodal Functions (F21, F22, F23)')
print("[OK] 07b_improvement_multimodal.png saved")

# ── PLOT 8: Boxplot — PSO vs all FCS runs (per function, from raw data) ──
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()

df_pso_runs = df_runs[df_runs['MH'] == 'PSO']

for idx, func in enumerate(FUNCTIONS_ORDERED):
    ax = axes[idx]
    
    pso_fitness = df_pso_runs[df_pso_runs['funcion'] == func]['fitness'].dropna().values
    fcs_fitness = df_fcs_runs[df_fcs_runs['funcion'] == func]['fitness'].dropna().values
    
    bp = ax.boxplot([pso_fitness, fcs_fitness], tick_labels=['PSO', 'PSO_FCS\n(all configs)'],
                    patch_artist=True, showmeans=True,
                    meanprops=dict(marker='x', markeredgecolor='black', markersize=7))
    
    bp['boxes'][0].set_facecolor('#FF6B6B')
    bp['boxes'][0].set_alpha(0.7)
    bp['boxes'][1].set_facecolor('#4ECDC4')
    bp['boxes'][1].set_alpha(0.7)
    
    ax.set_title(func, fontweight='bold')
    ax.set_ylabel('Fitness')
    ax.grid(True, alpha=0.3, axis='y')

fig.suptitle('PSO vs PSO_FCS (all configs pooled): Fitness Distribution',
             fontsize=12, fontweight='bold')
plt.tight_layout(rect=[0, 0, 1, 0.95])
plt.savefig(os.path.join(OUTPUT_DIR, '08_pso_vs_fcs_boxplot.png'), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] 08_pso_vs_fcs_boxplot.png saved")

# ── PLOT 9: Violin plot — PSO vs all FCS runs (per function, from raw data) ──
fig, axes = plt.subplots(2, 3, figsize=(14, 8))
axes = axes.flatten()

for idx, func in enumerate(FUNCTIONS_ORDERED):
    ax = axes[idx]
    
    pso_fitness = df_pso_runs[df_pso_runs['funcion'] == func]['fitness'].dropna()
    fcs_fitness = df_fcs_runs[df_fcs_runs['funcion'] == func]['fitness'].dropna()
    
    violin_data = pd.DataFrame([
        *[{'Algorithm': 'PSO', 'Fitness': v} for v in pso_fitness],
        *[{'Algorithm': 'PSO_FCS\n(all configs)', 'Fitness': v} for v in fcs_fitness],
    ])
    
    if len(violin_data) > 0:
        parts = ax.violinplot(
            [pso_fitness.values, fcs_fitness.values],
            positions=[1, 2], showmeans=True, showmedians=True, showextrema=True)
        
        for i, pc in enumerate(parts['bodies']):
            pc.set_facecolor(['#FF6B6B', '#4ECDC4'][i])
            pc.set_alpha(0.7)
            pc.set_edgecolor('black')
        parts['cmeans'].set_color('black')
        parts['cmedians'].set_color('blue')
        parts['cmedians'].set_linestyle('--')
        
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['PSO', 'PSO_FCS\n(all configs)'])
    
    ax.set_title(func, fontweight='bold')
    ax.set_ylabel('Fitness')
    ax.grid(True, alpha=0.3, axis='y')

# Legend for violin
from matplotlib.patches import Patch
from matplotlib.lines import Line2D as Line2D_v
violin_legend = [
    Patch(facecolor='#FF6B6B', alpha=0.7, edgecolor='black', label='PSO'),
    Patch(facecolor='#4ECDC4', alpha=0.7, edgecolor='black', label='PSO_FCS (all configs)'),
    Line2D_v([0], [0], color='black', linewidth=1.5, label='Mean'),
    Line2D_v([0], [0], color='blue', linewidth=1.5, linestyle='--', label='Median'),
]
fig.legend(handles=violin_legend, loc='lower center', ncol=4, fontsize=9,
           bbox_to_anchor=(0.5, -0.01))

fig.suptitle('PSO vs PSO_FCS (all configs pooled): Fitness Distribution (Violin)',
             fontsize=12, fontweight='bold')
plt.tight_layout(rect=[0, 0.04, 1, 0.95])
plt.savefig(os.path.join(OUTPUT_DIR, '09_pso_vs_fcs_violin.png'), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] 09_pso_vs_fcs_violin.png saved")

# ═══════════════════════════════════════════════════════════════════════════
# TABLE 7: Wilcoxon Rank-Sum Test — PSO vs Best PSO_FCS per function
# ═══════════════════════════════════════════════════════════════════════════
from scipy.stats import wilcoxon, mannwhitneyu

print("\n── TABLE 7: Wilcoxon / Mann-Whitney U Test — PSO vs Best PSO_FCS ──")
wilcoxon_rows = []
df_pso_runs_w = df_runs[df_runs['MH'] == 'PSO']

for func in FUNCTIONS_ORDERED:
    pso_fit = df_pso_runs_w[df_pso_runs_w['funcion'] == func]['fitness'].dropna().values
    fcs_func = df_fcs[df_fcs['funcion'] == func]
    if len(pso_fit) == 0 or len(fcs_func) == 0:
        continue
    best_fcs_mh = fcs_func.loc[fcs_func['fitness_mean'].idxmin(), 'MH']
    fcs_fit = df_runs[(df_runs['MH'] == best_fcs_mh) & (df_runs['funcion'] == func)]['fitness'].dropna().values

    n = min(len(pso_fit), len(fcs_fit))
    pso_fit_paired = pso_fit[:n]
    fcs_fit_paired = fcs_fit[:n]

    # Wilcoxon signed-rank (paired, same seed order)
    try:
        stat_w, p_wilcox = wilcoxon(pso_fit_paired, fcs_fit_paired)
    except ValueError:
        stat_w, p_wilcox = np.nan, np.nan

    # Mann-Whitney U (unpaired, as confirmation)
    stat_u, p_mwu = mannwhitneyu(pso_fit, fcs_fit, alternative='two-sided')

    # Determine direction for minimization: who has lower mean?
    pso_mean = pso_fit.mean()
    fcs_mean = fcs_fit.mean()
    better = 'PSO_FCS' if fcs_mean < pso_mean else 'PSO'

    wilcoxon_rows.append({
        'Function': func,
        'Best_FCS': best_fcs_mh,
        'PSO_Mean': round(pso_mean, 4),
        'FCS_Mean': round(fcs_mean, 4),
        'Better': better,
        'Wilcoxon_p': round(p_wilcox, 6) if not np.isnan(p_wilcox) else 'N/A',
        'Wilcoxon_sig': ('***' if p_wilcox < 0.001 else '**' if p_wilcox < 0.01
                         else '*' if p_wilcox < 0.05 else 'ns') if not np.isnan(p_wilcox) else 'N/A',
        'MannWhitney_p': round(p_mwu, 6),
        'MannWhitney_sig': '***' if p_mwu < 0.001 else '**' if p_mwu < 0.01
                           else '*' if p_mwu < 0.05 else 'ns',
    })

df_wilcoxon = pd.DataFrame(wilcoxon_rows)
print(df_wilcoxon.to_string(index=False))
df_wilcoxon.to_csv(os.path.join(OUTPUT_DIR, '10_wilcoxon_pso_vs_fcs.csv'), index=False)
print("\n[OK] 10_wilcoxon_pso_vs_fcs.csv saved")
print("     Significance: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")

# ═══════════════════════════════════════════════════════════════════════════
# TABLE 8 + PLOT 10: Computational Efficiency — Time overhead vs quality gain
# ═══════════════════════════════════════════════════════════════════════════
print("\n── TABLE 8: Computational Efficiency — PSO vs Best PSO_FCS ──")
efficiency_rows = []

for func in FUNCTIONS_ORDERED:
    pso_runs_f = df_pso_runs_w[df_pso_runs_w['funcion'] == func]
    fcs_func = df_fcs[df_fcs['funcion'] == func]
    if len(pso_runs_f) == 0 or len(fcs_func) == 0:
        continue
    best_fcs_mh = fcs_func.loc[fcs_func['fitness_mean'].idxmin(), 'MH']
    fcs_runs_f = df_runs[(df_runs['MH'] == best_fcs_mh) & (df_runs['funcion'] == func)]

    pso_time_mean = pso_runs_f['tiempoEjecucion'].mean()
    fcs_time_mean = fcs_runs_f['tiempoEjecucion'].mean()
    time_overhead_pct = ((fcs_time_mean - pso_time_mean) / pso_time_mean) * 100

    pso_fit_mean = pso_runs_f['fitness'].mean()
    fcs_fit_mean = fcs_runs_f['fitness'].mean()
    pso_fit_std = pso_runs_f['fitness'].std()
    fcs_fit_std = fcs_runs_f['fitness'].std()

    # Fitness improvement (for minimization: positive = FCS better)
    if pso_fit_mean != 0:
        fitness_improv_pct = ((pso_fit_mean - fcs_fit_mean) / abs(pso_fit_mean)) * 100
    else:
        fitness_improv_pct = pso_fit_mean - fcs_fit_mean

    # Std reduction (positive = FCS more stable)
    if pso_fit_std != 0:
        std_reduction_pct = ((pso_fit_std - fcs_fit_std) / pso_fit_std) * 100
    else:
        std_reduction_pct = 0.0

    efficiency_rows.append({
        'Function': func,
        'Best_FCS': best_fcs_mh,
        'PSO_Time_s': round(pso_time_mean, 2),
        'FCS_Time_s': round(fcs_time_mean, 2),
        'Time_Overhead_%': round(time_overhead_pct, 2),
        'PSO_Fitness': round(pso_fit_mean, 4),
        'FCS_Fitness': round(fcs_fit_mean, 4),
        'Fitness_Improv_%': round(fitness_improv_pct, 2),
        'PSO_Std': round(pso_fit_std, 4),
        'FCS_Std': round(fcs_fit_std, 4),
        'Std_Reduction_%': round(std_reduction_pct, 2),
    })

df_efficiency = pd.DataFrame(efficiency_rows)
print(df_efficiency.to_string(index=False))
df_efficiency.to_csv(os.path.join(OUTPUT_DIR, '11_computational_efficiency.csv'), index=False)
print("\n[OK] 11_computational_efficiency.csv saved")

# ── PLOT 10: Efficiency scatter — Time overhead vs Std reduction ──────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# 10a: Time overhead vs Std reduction
ax = axes[0]
for _, row in df_efficiency.iterrows():
    color = '#4ECDC4' if row['Std_Reduction_%'] > 0 else '#FF6B6B'
    ax.scatter(row['Time_Overhead_%'], row['Std_Reduction_%'],
               s=120, c=color, edgecolors='black', linewidth=0.5, zorder=3)
    ax.annotate(row['Function'], (row['Time_Overhead_%'], row['Std_Reduction_%']),
                textcoords='offset points', xytext=(6, 4), fontsize=10, fontweight='bold')

ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
ax.axvline(x=0, color='gray', linestyle='--', linewidth=0.8, alpha=0.6)
ax.set_xlabel('Time Overhead of PSO_FCS (%)', fontsize=11)
ax.set_ylabel('Std Reduction (%)\n(positive = FCS more stable)', fontsize=11)
ax.set_title('Fuzzy Overhead vs Variability Reduction', fontweight='bold', fontsize=12)
ax.grid(True, alpha=0.3)

# 10b: Time overhead bar + Std reduction bar (grouped)
ax2 = axes[1]
funcs_eff = [r['Function'] for r in efficiency_rows]
x = np.arange(len(funcs_eff))
w = 0.35

bars1 = ax2.bar(x - w/2, [r['Time_Overhead_%'] for r in efficiency_rows], w,
                label='Time Overhead (%)', color='#FFA07A', edgecolor='black', linewidth=0.5, alpha=0.85)
bars2 = ax2.bar(x + w/2, [r['Std_Reduction_%'] for r in efficiency_rows], w,
                label='Std Reduction (%)', color='#4ECDC4', edgecolor='black', linewidth=0.5, alpha=0.85)

ax2.set_xticks(x)
ax2.set_xticklabels(funcs_eff, fontsize=10)
ax2.set_ylabel('Percentage (%)', fontsize=11)
ax2.set_title('Fuzzy Controller Cost-Benefit per Function', fontweight='bold', fontsize=12)
ax2.legend(fontsize=9)
ax2.axhline(y=0, color='black', linewidth=0.8)
ax2.grid(True, alpha=0.3, axis='y')

fig.suptitle('Computational Efficiency: PSO vs Best PSO_FCS',
             fontsize=13, fontweight='bold')
plt.tight_layout(rect=[0, 0, 1, 0.94])
plt.savefig(os.path.join(OUTPUT_DIR, '10_efficiency_analysis.png'), dpi=DPI, bbox_inches='tight')
plt.close()
print("[OK] 10_efficiency_analysis.png saved")

# ═══════════════════════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 70)
print("SUMMARY OF FINDINGS")
print("=" * 70)

# Best overall config
overall_rank = df_fcs_ranked.groupby(['input_set', 'num_labels'])['rank'].mean()
best_config = overall_rank.idxmin()
print(f"\n1. Best overall configuration: input_set={best_config[0]}, num_labels={best_config[1]}")
print(f"   Average rank: {overall_rank[best_config]:.2f}")

# 3L vs 5L
avg_3 = df_fcs_ranked[df_fcs_ranked['num_labels'] == 3]['rank'].mean()
avg_5 = df_fcs_ranked[df_fcs_ranked['num_labels'] == 5]['rank'].mean()
print(f"\n2. 3 labels avg rank: {avg_3:.2f} vs 5 labels avg rank: {avg_5:.2f}")
if avg_3 < avg_5:
    print("   → 3 labels performs better on average")
else:
    print("   → 5 labels performs better on average")

# Input set comparison
avg_by_input = df_fcs_ranked.groupby('input_set')['rank'].mean().sort_values()
print(f"\n3. Input set ranking (avg rank, lower=better):")
for iset, rank_val in avg_by_input.items():
    print(f"   {iset} ({INPUT_NAMES[iset]}): {rank_val:.2f}")

# PSO vs FCS summary
print(f"\n4. PSO vs PSO_FCS (best config per function):")
print(f"   PSO wins: {pso_wins_best}/{len(comparison_rows)} functions")
print(f"   FCS wins: {fcs_wins_best}/{len(comparison_rows)} functions")
for r in comparison_rows:
    symbol = '✓ PSO' if r['Winner_vs_Best'] == 'PSO' else '✓ FCS'
    print(f"   {r['Function']}: {symbol} ({r['Improv_BestFCS_%']:+.1f}%)")

print(f"\nAll outputs saved to: {OUTPUT_DIR}/")
print("=" * 70)
