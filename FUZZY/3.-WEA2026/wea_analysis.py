"""
WEA 2026 ANALYSIS PIPELINE
==========================
"Sensitivity Analysis of Fuzzy Rule Base Structure 
 for Adaptive Inertia Weight Control in PSO"

Covers all analysis tasks from 00_paper_plan.md (Section 5-6) and 
01_task_list.md (Phase 4: T4.1-T4.5).

Outputs:
  FUZZY/3.-WEA2026/resultados_wea/
    analysis/
      - all_runs.csv                       Level 1: raw experiment data
      - stats_by_config.csv                Level 2: descriptive stats per config
      - stats_by_function.csv              Level 2: stats per function
            - stats_by_category.csv              Level 2: stats grouped by function category
            - stats_by_optimum_group.csv         Level 2: stats grouped by optimum type
      - friedman_ranking.csv               Level 3: Friedman test ranking
            - friedman_ranking_optimum_zero.csv  Level 3: Friedman ranking for optimum = 0
            - friedman_ranking_optimum_nonzero.csv Level 3: Friedman ranking for optimum != 0
      - wilcoxon_pairwise.csv              Level 3: Wilcoxon pairwise p-values
      - mirror_pair_analysis.csv           Mirror pair comparison (R1↔R2, etc.)
      - granularity_effect.csv             3L vs 5L comparison per rule set
      - factorial_interaction.csv          Progress × Diversity interaction table
      - top_configs_global.csv             Best 20 configs overall
            - top_configs_optimum_zero.csv       Best configs for optimum = 0
            - top_configs_optimum_nonzero.csv    Best configs for optimum != 0
      - w_reconstruction_data.csv          Reconstructed w values
    plots/
      - 01_boxplot_by_rule_set.png         Boxplot grid per function
      - 02_boxplot_by_granularity.png      3L vs 5L boxplots
      - 03_convergence_by_function.png     Convergence curves per function
      - 04_w_trajectory_comparison.png     w over iterations per rule
      - 05_mirror_pair_overlay.png         Mirror pair w trajectories
      - 06_factorial_interaction.png       Progress × Diversity interaction plot
      - 07_cd_diagram.png                  Critical Difference diagram (Nemenyi)
      - 08_heatmap_mean_fitness.png        Config × Function heatmap
      - 09_violin_by_category.png          Violin plot by function category
      - 10_granularity_paired.png          Paired 3L vs 5L per Ri

Usage:
  python FUZZY/3.-WEA2026/wea_analysis.py
"""

import os
import sys
from pathlib import Path
from io import StringIO
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
from scipy import stats as sp_stats

# ---------------------------------------------------------------------------
# Project root
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from BD.sqlite import BD
from FUZZY.fuzzy_controller_w_3L import get_fuzzy_controller
from scipy.interpolate import RegularGridInterpolator

# ---------------------------------------------------------------------------
# Output directories
# ---------------------------------------------------------------------------
OUTPUT_BASE = SCRIPT_DIR / 'resultados_wea'
OUTPUT_ANALYSIS = OUTPUT_BASE / 'analysis'
OUTPUT_PLOTS = OUTPUT_BASE / 'plots'

# ---------------------------------------------------------------------------
# Plot style (LNCS/CCIS format)
# ---------------------------------------------------------------------------
plt.rcParams.update({
    'figure.figsize': (7.5, 5),
    'font.family': 'Times New Roman',
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 7.5,
})
sns.set_style("whitegrid")
DPI_OUTPUT = 300

# ---------------------------------------------------------------------------
# Known classical benchmark optima
# ---------------------------------------------------------------------------
OPTIMOS = {
    'F1': 0.0, 'F2': 0.0, 'F3': 0.0, 'F4': 0.0, 'F5': 0.0,
    'F6': 0.0, 'F7': 0.0, 'F8': -418.9829 * 2, 'F9': 0.0,
    'F10': 0.0, 'F11': 0.0, 'F12': 0.0, 'F13': 0.0,
    'F14': 1.0, 'F15': 0.0003075, 'F16': -1.0316, 'F17': 0.398,
    'F18': 3.0, 'F19': -3.86, 'F20': -3.32,
    'F21': -10.153199679058229, 'F22': -10.402940566818662,
    'F23': -10.536409816692046,
}

# Function categories
CATEGORIES = {
    'F1': 'Unimodal', 'F2': 'Unimodal', 'F3': 'Unimodal', 'F4': 'Unimodal',
    'F5': 'Multimodal', 'F6': 'Unimodal', 'F7': 'Unimodal',
    'F8': 'Multimodal', 'F9': 'Multimodal', 'F10': 'Multimodal',
    'F11': 'Multimodal', 'F12': 'Multimodal', 'F13': 'Multimodal',
    'F14': 'Fixed-dim', 'F15': 'Fixed-dim', 'F16': 'Fixed-dim',
    'F17': 'Fixed-dim', 'F18': 'Fixed-dim', 'F19': 'Fixed-dim',
    'F20': 'Fixed-dim', 'F21': 'Fixed-dim', 'F22': 'Fixed-dim',
    'F23': 'Fixed-dim',
}

OPTIMUM_GROUP_LABELS = {
    'optimum_zero': 'Optimum = 0',
    'optimum_nonzero': 'Optimum != 0',
}

# Rule set metadata (progress direction, diversity direction)
RULE_META = {
    'R1': {'progress': '↓', 'diversity': '—', 'label': 'Prog↓, Div—'},
    'R2': {'progress': '↑', 'diversity': '—', 'label': 'Prog↑, Div—'},
    'R3': {'progress': '—', 'diversity': '→', 'label': 'Prog—, Div→'},
    'R4': {'progress': '—', 'diversity': '←', 'label': 'Prog—, Div←'},
    'R5': {'progress': '↓', 'diversity': '→', 'label': 'Prog↓, Div→'},
    'R6': {'progress': '↓', 'diversity': '←', 'label': 'Prog↓, Div←'},
    'R7': {'progress': '↑', 'diversity': '→', 'label': 'Prog↑, Div→'},
    'R8': {'progress': '↑', 'diversity': '←', 'label': 'Prog↑, Div←'},
}

MIRROR_PAIRS = [('R1', 'R2'), ('R3', 'R4'), ('R5', 'R8'), ('R6', 'R7')]


# ---------------------------------------------------------------------------
# MH name parsing
# ---------------------------------------------------------------------------

def parse_mh_name(mh_name):
    """Parse 'PSO_FCS:O1:3:I1:R1' → dict with base, output_set, num_labels, input_set, rule_set."""
    parts = mh_name.split(':')
    if len(parts) >= 5:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': int(parts[2]), 'input_set': parts[3],
            'rule_set': parts[4],
            'short_label': f"R{parts[4][1:]}-{parts[2]}L",
        }
    elif len(parts) >= 4:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': int(parts[2]), 'input_set': parts[3],
            'rule_set': 'R1',
            'short_label': f"{parts[3]}-{parts[2]}L",
        }
    return {'base': mh_name, 'output_set': None, 'num_labels': None,
            'input_set': None, 'rule_set': None, 'short_label': mh_name}


def build_display_name(mh_name):
    info = parse_mh_name(mh_name)
    if info['base'] == 'PSO' and info['output_set'] is None:
        return 'PSO-STD'
    return info['short_label']


def classify_optimum_group(optimum_value):
    """Classify functions by whether their theoretical optimum is zero or not."""
    if pd.isna(optimum_value):
        return 'optimum_unknown'
    return 'optimum_zero' if np.isclose(optimum_value, 0.0) else 'optimum_nonzero'


def function_sort_key(func_name):
    """Natural ordering for benchmark names: F1, F5, F11, F21, F22, F23, ..."""
    if isinstance(func_name, str) and func_name.startswith('F') and func_name[1:].isdigit():
        return (0, int(func_name[1:]))
    return (1, str(func_name))


def sort_functions(function_names):
    """Return function names in natural numeric order."""
    return sorted(function_names, key=function_sort_key)


def display_name_sort_key(display_name):
    """Order configs as PSO-STD, then R1-3L..R8-3L, then R1-5L..R8-5L."""
    if display_name == 'PSO-STD':
        return (0, 0, 0, display_name)

    if isinstance(display_name, str) and display_name.startswith('R') and '-3L' in display_name:
        try:
            rule_num = int(display_name.split('-')[0][1:])
        except Exception:
            rule_num = 999
        return (1, 3, rule_num, display_name)

    if isinstance(display_name, str) and display_name.startswith('R') and '-5L' in display_name:
        try:
            rule_num = int(display_name.split('-')[0][1:])
        except Exception:
            rule_num = 999
        return (2, 5, rule_num, display_name)

    return (3, 99, 999, str(display_name))


def sort_display_names(display_names):
    """Return display names in the manuscript-friendly order."""
    return sorted(display_names, key=display_name_sort_key)


# ---------------------------------------------------------------------------
# Dynamic colors/markers
# ---------------------------------------------------------------------------
_BASE_COLORS = [
    '#E63946', '#457B9D', '#2A9D8F', '#E9C46A', '#F4A261',
    '#264653', '#A8DADC', '#6A0572', '#1D3557', '#B5838D',
    '#606C38', '#BC6C25', '#FF006E', '#8338EC', '#3A86FF',
    '#FB5607', '#FFBE0B', '#8AC926',
]
_MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X', 'p', 'h', '*', '<', '>',
            'd', '8', 'H', '+', 'x', '1']


def assign_styles(mh_names):
    baseline = [m for m in mh_names if not m.startswith('PSO_FCS')]
    fcs = sorted([m for m in mh_names if m.startswith('PSO_FCS')],
                 key=lambda x: display_name_sort_key(build_display_name(x)))
    ordered = baseline + fcs
    colors, markers = {}, {}
    for i, mh in enumerate(ordered):
        colors[mh] = _BASE_COLORS[i % len(_BASE_COLORS)]
        markers[mh] = _MARKERS[i % len(_MARKERS)]
    return colors, markers


# ---------------------------------------------------------------------------
# w reconstruction (cached lookup table)
# ---------------------------------------------------------------------------
_interp_cache = {}
_LUT_RES = 101


def _build_w_interpolator(w_set, num_labels, input_set, rule_set='R1'):
    key = (w_set, num_labels, input_set, rule_set)
    if key in _interp_cache:
        return _interp_cache[key]
    fcs = get_fuzzy_controller(w_set, num_labels=num_labels, input_set=input_set,
                               rule_set=rule_set)
    d_axis = np.linspace(0, 1, _LUT_RES)
    p_axis = np.linspace(0, 1, _LUT_RES)
    w_grid = np.zeros((_LUT_RES, _LUT_RES), dtype=float)
    for i, d in enumerate(d_axis):
        for j, p in enumerate(p_axis):
            w_grid[i, j] = fcs.compute_w(float(d), float(p))
    interp = RegularGridInterpolator((d_axis, p_axis), w_grid,
                                      method='linear', bounds_error=False,
                                      fill_value=None)
    _interp_cache[key] = interp
    return interp


def _compute_w_for_pso(n_iters, max_iter=500, w_start=0.9, w_end=0.1):
    iters = np.arange(n_iters)
    w_vals = w_start - (w_start - w_end) * iters / max(max_iter, 1)
    return np.clip(w_vals, w_end, w_start)


def _compute_w_for_fcs(div_series, max_iter, mh_name):
    info = parse_mh_name(mh_name)
    w_set = info['output_set'] or 'O1'
    num_labels = info['num_labels'] or 3
    input_set = info['input_set'] or 'I1'
    rule_set = info['rule_set'] or 'R1'
    interp = _build_w_interpolator(w_set, num_labels, input_set, rule_set)
    divs = np.array(div_series, dtype=float)
    n = len(divs)
    max_div_running = np.maximum.accumulate(np.maximum(divs, 1e-12))
    diversity_ratio = np.clip(divs / max_div_running, 0.0, 1.0)
    progress = np.clip(np.arange(n) / max(max_iter, 1), 0.0, 1.0)
    points = np.column_stack([diversity_ratio, progress])
    return interp(points)


# ===================================================================
# LEVEL 1: RAW DATA EXTRACTION
# ===================================================================

def extract_experiment_results():
    """Extract all completed BEN experiments from DB."""
    print("[L1] Extracting experiment results from DB...")
    bd = BD()
    bd.conectar()
    cursor = bd.getCursor()
    cursor.execute("""
        SELECT exp.id_experimento, exp.MH, inst.nombre AS funcion,
               res.fitness, res.tiempoEjecucion, exp.paramMH
        FROM experimentos exp
        JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
        LEFT JOIN resultados res ON exp.id_experimento = res.fk_id_experimento
        WHERE inst.tipo_problema = 'BEN'
          AND exp.estado IN ('terminado', 'completado', 'completada')
        ORDER BY inst.nombre, exp.MH
    """)
    cols = [d[0] for d in cursor.description]
    rows = cursor.fetchall()
    bd.desconectar()

    if not rows:
        print("[WARN] No completed BEN experiments found")
        return None

    df = pd.DataFrame(rows, columns=cols)

    # Enrich with parsed fields
    df['display_name'] = df['MH'].apply(build_display_name)
    df['rule_set'] = df['MH'].apply(lambda x: parse_mh_name(x).get('rule_set'))
    df['num_labels'] = df['MH'].apply(lambda x: parse_mh_name(x).get('num_labels'))
    df['category'] = df['funcion'].map(CATEGORIES)

    # Gap to optimum
    df['optimo'] = df['funcion'].map(OPTIMOS)
    df['optimum_group'] = df['optimo'].apply(classify_optimum_group)
    df['optimum_group_label'] = df['optimum_group'].map(OPTIMUM_GROUP_LABELS)
    df['gap_abs'] = (df['fitness'] - df['optimo']).abs()

    csv_path = OUTPUT_ANALYSIS / 'all_runs.csv'
    df.to_csv(csv_path, index=False)
    print(f"  [OK] all_runs.csv ({len(df)} rows)")
    return df


def extract_iteration_data():
    """Extract per-iteration data and reconstruct w values."""
    print("[L1] Extracting iteration data + reconstructing w...")
    bd = BD()
    bd.conectar()
    cursor = bd.getCursor()
    cursor.execute("""
        SELECT it.fk_id_experimento, it.archivo, exp.MH, inst.nombre, exp.paramMH
        FROM iteraciones it
        JOIN experimentos exp ON it.fk_id_experimento = exp.id_experimento
        JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
        WHERE inst.tipo_problema = 'BEN'
          AND exp.estado IN ('terminado', 'completado', 'completada')
    """)
    all_rows = cursor.fetchall()
    bd.desconectar()

    records = []
    skipped = 0
    total = len(all_rows)

    for idx, (exp_id, blob, mh, funcion, paramMH) in enumerate(all_rows):
        if (idx + 1) % 200 == 0 or idx == total - 1:
            print(f"\r  Processing {idx+1}/{total} ...", end='', flush=True)
        if blob is None:
            skipped += 1
            continue
        try:
            content = blob.decode('utf-8', errors='ignore') if isinstance(blob, bytes) else str(blob)
            df_iter = pd.read_csv(StringIO(content))

            # Normalize columns
            col_map = {}
            for c in df_iter.columns:
                cl = c.strip().lower()
                if cl == 'iter': col_map[c] = 'iter'
                elif cl == 'best_fitness': col_map[c] = 'best_fitness'
                elif cl == 'div': col_map[c] = 'DIV'
            df_iter = df_iter.rename(columns=col_map)

            if 'best_fitness' not in df_iter.columns or 'DIV' not in df_iter.columns:
                skipped += 1
                continue

            n = len(df_iter)
            max_iter = 500
            if paramMH:
                for token in paramMH.split(','):
                    if token.strip().startswith('iter:'):
                        try: max_iter = int(token.strip().split(':')[1])
                        except: pass

            if mh.startswith('PSO_FCS'):
                w_vals = _compute_w_for_fcs(df_iter['DIV'].values, max_iter, mh)
            else:
                w_vals = _compute_w_for_pso(n, max_iter)

            iters = df_iter['iter'].values if 'iter' in df_iter.columns else np.arange(n)
            progress = iters / max(max_iter, 1)
            divs = df_iter['DIV'].values
            max_div_running = np.maximum.accumulate(np.maximum(divs, 1e-12))
            diversity_ratio = divs / max_div_running

            sub = pd.DataFrame({
                'iter': iters, 'w': w_vals, 'DIV': divs,
                'diversity_ratio': diversity_ratio, 'progress': progress,
                'best_fitness': df_iter['best_fitness'].values,
                'id_experimento': exp_id, 'MH': mh, 'funcion': funcion,
            })
            records.append(sub)
        except Exception:
            skipped += 1

    print()
    if not records:
        print("[WARN] No iteration data found")
        return None

    df = pd.concat(records, ignore_index=True)
    df['display_name'] = df['MH'].apply(build_display_name)
    df['rule_set'] = df['MH'].apply(lambda x: parse_mh_name(x).get('rule_set'))
    df['num_labels'] = df['MH'].apply(lambda x: parse_mh_name(x).get('num_labels'))

    csv_path = OUTPUT_ANALYSIS / 'w_reconstruction_data.csv'
    # Save a summary (full data too large)
    summary = df.groupby(['MH', 'funcion', 'iter']).agg(
        w_mean=('w', 'mean'), w_std=('w', 'std'),
        div_mean=('DIV', 'mean'), fitness_mean=('best_fitness', 'mean')
    ).reset_index()
    summary.to_csv(csv_path, index=False)
    print(f"  [OK] w_reconstruction_data.csv ({len(summary)} rows, skipped {skipped})")
    return df


# ===================================================================
# LEVEL 2: DESCRIPTIVE STATISTICS
# ===================================================================

def compute_descriptive_stats(df):
    """Compute descriptive stats grouped by config and by function."""
    print("[L2] Computing descriptive statistics...")

    # --- Stats by config (MH × function) ---
    stats_config = df.groupby(['MH', 'display_name', 'funcion', 'category', 'optimum_group_label']).agg(
        fitness_min=('fitness', 'min'),
        fitness_max=('fitness', 'max'),
        fitness_mean=('fitness', 'mean'),
        fitness_std=('fitness', 'std'),
        fitness_median=('fitness', 'median'),
        n_runs=('fitness', 'count'),
        gap_abs_mean=('gap_abs', 'mean'),
        time_mean=('tiempoEjecucion', 'mean'),
    ).reset_index()
    stats_config['CV_pct'] = (stats_config['fitness_std'] / stats_config['fitness_mean'].abs().clip(1e-15)) * 100
    stats_config['IQR'] = df.groupby(['MH', 'display_name', 'funcion', 'category', 'optimum_group_label'])['fitness'].apply(
        lambda x: x.quantile(0.75) - x.quantile(0.25)).values
    stats_config.to_csv(OUTPUT_ANALYSIS / 'stats_by_config.csv', index=False)
    print(f"  [OK] stats_by_config.csv ({len(stats_config)} rows)")

    # --- Stats by function ---
    stats_func = df.groupby(['funcion', 'category', 'optimum_group_label']).agg(
        fitness_min=('fitness', 'min'), fitness_mean=('fitness', 'mean'),
        fitness_std=('fitness', 'std'), gap_abs_mean=('gap_abs', 'mean'),
        n_total=('fitness', 'count'),
    ).reset_index()
    stats_func.to_csv(OUTPUT_ANALYSIS / 'stats_by_function.csv', index=False)
    print(f"  [OK] stats_by_function.csv")

    # --- Stats by category ---
    stats_cat = df.groupby(['display_name', 'category', 'optimum_group_label']).agg(
        fitness_mean=('fitness', 'mean'), fitness_std=('fitness', 'std'),
        gap_abs_mean=('gap_abs', 'mean'), n_runs=('fitness', 'count'),
    ).reset_index()
    stats_cat.to_csv(OUTPUT_ANALYSIS / 'stats_by_category.csv', index=False)
    print(f"  [OK] stats_by_category.csv")

    # --- Stats by optimum group ---
    stats_opt = df.groupby(['display_name', 'optimum_group_label']).agg(
        fitness_mean=('fitness', 'mean'), fitness_std=('fitness', 'std'),
        gap_abs_mean=('gap_abs', 'mean'), gap_abs_std=('gap_abs', 'std'),
        n_runs=('fitness', 'count'), n_functions=('funcion', 'nunique'),
    ).reset_index()
    stats_opt.to_csv(OUTPUT_ANALYSIS / 'stats_by_optimum_group.csv', index=False)
    print(f"  [OK] stats_by_optimum_group.csv")

    return stats_config


# ===================================================================
# LEVEL 3: STATISTICAL TESTS
# ===================================================================

def friedman_ranking(df, output_name='friedman_ranking.csv', label='all functions'):
    """Friedman test + ranking across a set of functions."""
    print(f"[L3] Computing Friedman ranking ({label})...")
    funciones = sort_functions(df['funcion'].unique())
    configs = sort_display_names(df['display_name'].unique())

    if len(funciones) < 2 or len(configs) < 2:
        print(f"  [SKIP] Not enough data for Friedman ranking ({label})")
        return pd.DataFrame(columns=['config', 'mean_rank', 'rank_position', 'friedman_stat', 'friedman_p', 'scope'])

    # Build matrix: rows = functions, cols = configs, values = mean fitness
    matrix = []
    for func in funciones:
        row = []
        for cfg in configs:
            vals = df[(df['funcion'] == func) & (df['display_name'] == cfg)]['fitness']
            row.append(vals.mean() if len(vals) > 0 else np.nan)
        matrix.append(row)

    matrix = np.array(matrix)

    # Rank per function (lower fitness = rank 1)
    ranks = np.zeros_like(matrix)
    for i in range(len(funciones)):
        valid = ~np.isnan(matrix[i])
        if valid.sum() > 1:
            ranks[i, valid] = sp_stats.rankdata(matrix[i, valid])

    mean_ranks = np.nanmean(ranks, axis=0)

    # Friedman test
    valid_rows = [matrix[i, ~np.isnan(matrix[i])] for i in range(len(funciones))
                  if np.sum(~np.isnan(matrix[i])) == len(configs)]
    if len(valid_rows) >= 2:
        try:
            stat, p_value = sp_stats.friedmanchisquare(*[matrix[:, j] for j in range(len(configs))
                                                          if not np.any(np.isnan(matrix[:, j]))])
        except Exception:
            stat, p_value = np.nan, np.nan
    else:
        stat, p_value = np.nan, np.nan

    ranking_df = pd.DataFrame({
        'config': configs, 'mean_rank': mean_ranks,
    }).sort_values(['mean_rank', 'config'], key=lambda col: col.map(display_name_sort_key) if col.name == 'config' else col)
    ranking_df['rank_position'] = range(1, len(ranking_df) + 1)
    ranking_df['friedman_stat'] = stat
    ranking_df['friedman_p'] = p_value
    ranking_df['scope'] = label
    ranking_df.to_csv(OUTPUT_ANALYSIS / output_name, index=False)
    print(f"  [OK] {output_name} (Friedman chi2={stat:.2f}, p={p_value:.4e})")
    return ranking_df


def wilcoxon_pairwise(df):
    """Wilcoxon signed-rank pairwise tests between all configs."""
    print("[L3] Computing Wilcoxon pairwise tests...")
    funciones = sort_functions(df['funcion'].unique())
    configs = sort_display_names(df['display_name'].unique())

    # Mean fitness per (config, function)
    pivot = df.groupby(['display_name', 'funcion'])['fitness'].mean().unstack(fill_value=np.nan)

    results = []
    for i in range(len(configs)):
        for j in range(i + 1, len(configs)):
            c1, c2 = configs[i], configs[j]
            if c1 not in pivot.index or c2 not in pivot.index:
                continue
            v1 = pivot.loc[c1].dropna()
            v2 = pivot.loc[c2].dropna()
            common = v1.index.intersection(v2.index)
            if len(common) < 2:
                continue
            try:
                stat, p = sp_stats.wilcoxon(v1[common].values, v2[common].values)
            except Exception:
                stat, p = np.nan, np.nan
            results.append({
                'config_1': c1, 'config_2': c2,
                'wilcoxon_stat': stat, 'p_value': p,
                'significant_005': p < 0.05 if not np.isnan(p) else False,
            })

    df_wilcoxon = pd.DataFrame(results)
    if not df_wilcoxon.empty:
        # Holm-Bonferroni correction
        ps = df_wilcoxon['p_value'].values.copy()
        n_tests = len(ps)
        sorted_idx = np.argsort(ps)
        corrected = np.full(n_tests, np.nan)
        for rank_i, idx in enumerate(sorted_idx):
            corrected[idx] = min(ps[idx] * (n_tests - rank_i), 1.0)
        df_wilcoxon['p_holm'] = corrected
        df_wilcoxon['significant_holm_005'] = df_wilcoxon['p_holm'] < 0.05

    df_wilcoxon.to_csv(OUTPUT_ANALYSIS / 'wilcoxon_pairwise.csv', index=False)
    print(f"  [OK] wilcoxon_pairwise.csv ({len(df_wilcoxon)} pairs)")
    return df_wilcoxon


def mirror_pair_analysis(df):
    """Compare mirror pairs: R1↔R2, R3↔R4, R5↔R8, R6↔R7."""
    print("[L3] Computing mirror pair analysis...")
    results = []
    funciones = sort_functions(df['funcion'].unique())

    for r_a, r_b in MIRROR_PAIRS:
        for num_l in [3, 5]:
            label_a = f"R{r_a[1:]}-{num_l}L"
            label_b = f"R{r_b[1:]}-{num_l}L"
            for func in funciones:
                vals_a = df[(df['display_name'] == label_a) & (df['funcion'] == func)]['fitness']
                vals_b = df[(df['display_name'] == label_b) & (df['funcion'] == func)]['fitness']
                if len(vals_a) < 2 or len(vals_b) < 2:
                    continue
                # Mann-Whitney U test
                try:
                    stat, p = sp_stats.mannwhitneyu(vals_a, vals_b, alternative='two-sided')
                except Exception:
                    stat, p = np.nan, np.nan
                # Cohen's d (effect size)
                pooled_std = np.sqrt((vals_a.std()**2 + vals_b.std()**2) / 2)
                cohens_d = (vals_a.mean() - vals_b.mean()) / pooled_std if pooled_std > 1e-15 else 0
                results.append({
                    'pair': f"{r_a}↔{r_b}", 'labels': num_l,
                    'function': func,
                    f'{r_a}_mean': vals_a.mean(), f'{r_b}_mean': vals_b.mean(),
                    'winner': label_a if vals_a.mean() < vals_b.mean() else label_b,
                    'p_value': p, 'cohens_d': cohens_d,
                    'significant': p < 0.05 if not np.isnan(p) else False,
                })

    df_mirror = pd.DataFrame(results)
    df_mirror.to_csv(OUTPUT_ANALYSIS / 'mirror_pair_analysis.csv', index=False)
    print(f"  [OK] mirror_pair_analysis.csv ({len(df_mirror)} comparisons)")
    return df_mirror


def granularity_effect(df):
    """Compare 3L vs 5L for each rule set Ri."""
    print("[L3] Computing granularity effect (3L vs 5L)...")
    results = []
    funciones = sort_functions(df['funcion'].unique())
    rule_sets = sorted(RULE_META.keys())

    for rs in rule_sets:
        for func in funciones:
            label_3 = f"R{rs[1:]}-3L"
            label_5 = f"R{rs[1:]}-5L"
            v3 = df[(df['display_name'] == label_3) & (df['funcion'] == func)]['fitness']
            v5 = df[(df['display_name'] == label_5) & (df['funcion'] == func)]['fitness']
            if len(v3) < 2 or len(v5) < 2:
                continue
            try:
                stat, p = sp_stats.mannwhitneyu(v3, v5, alternative='two-sided')
            except Exception:
                stat, p = np.nan, np.nan
            pooled_std = np.sqrt((v3.std()**2 + v5.std()**2) / 2)
            cohens_d = (v3.mean() - v5.mean()) / pooled_std if pooled_std > 1e-15 else 0
            results.append({
                'rule_set': rs, 'function': func,
                'mean_3L': v3.mean(), 'mean_5L': v5.mean(),
                'winner': '3L' if v3.mean() < v5.mean() else '5L',
                'p_value': p, 'cohens_d': cohens_d,
                'significant': p < 0.05 if not np.isnan(p) else False,
            })

    df_gran = pd.DataFrame(results)
    df_gran.to_csv(OUTPUT_ANALYSIS / 'granularity_effect.csv', index=False)
    print(f"  [OK] granularity_effect.csv ({len(df_gran)} comparisons)")
    return df_gran


def factorial_interaction(df):
    """Progress direction × Diversity direction interaction table."""
    print("[L3] Computing factorial interaction table...")
    results = []

    for rs, meta in RULE_META.items():
        for num_l in [3, 5]:
            label = f"R{rs[1:]}-{num_l}L"
            for optimum_group, optimum_label in OPTIMUM_GROUP_LABELS.items():
                subset = df[(df['display_name'] == label) & (df['optimum_group'] == optimum_group)]
                if subset.empty:
                    continue
                results.append({
                    'rule_set': rs, 'labels': num_l,
                    'progress_dir': meta['progress'],
                    'diversity_dir': meta['diversity'],
                    'strategy': meta['label'],
                    'optimum_group': optimum_group,
                    'optimum_group_label': optimum_label,
                    'fitness_mean': subset['fitness'].mean(),
                    'fitness_std': subset['fitness'].std(),
                    'gap_abs_mean': subset['gap_abs'].mean(),
                    'gap_abs_std': subset['gap_abs'].std(),
                    'n_runs': len(subset),
                })

    df_fact = pd.DataFrame(results)
    df_fact.to_csv(OUTPUT_ANALYSIS / 'factorial_interaction.csv', index=False)
    print(f"  [OK] factorial_interaction.csv")
    return df_fact


def top_configs(df, n=20, output_name='top_configs_global.csv', label='all functions'):
    """Top N configs using mean per-function rank plus mean absolute gap."""
    print(f"[L3] Computing top {n} configs ({label})...")
    if df.empty:
        print(f"  [SKIP] No data for top configs ({label})")
        return pd.DataFrame()

    rank_base = df.groupby(['display_name', 'funcion'])['gap_abs'].mean().reset_index(name='gap_abs_mean_by_function')
    rank_base['mean_rank_component'] = rank_base.groupby('funcion')['gap_abs_mean_by_function'].rank(method='average')

    mean_ranks = rank_base.groupby('display_name')['mean_rank_component'].mean().rename('mean_rank')

    top = df.groupby('display_name').agg(
        fitness_mean=('fitness', 'mean'), fitness_std=('fitness', 'std'),
        gap_abs_mean=('gap_abs', 'mean'), gap_abs_std=('gap_abs', 'std'),
        n_runs=('fitness', 'count'), n_functions=('funcion', 'nunique'),
    ).reset_index()
    top = top.merge(mean_ranks, on='display_name', how='left')
    top = top.sort_values(['mean_rank', 'gap_abs_mean', 'fitness_mean', 'display_name'],
                          key=lambda col: col.map(display_name_sort_key) if col.name == 'display_name' else col).head(n).reset_index(drop=True)
    top['rank'] = range(1, len(top) + 1)
    top['scope'] = label
    top.to_csv(OUTPUT_ANALYSIS / output_name, index=False)
    print(f"  [OK] {output_name}")
    return top


# ===================================================================
# PLOTS
# ===================================================================

def plot_boxplot_by_rule(df, colors):
    """01: Boxplot grid — one panel per function, configs on x-axis."""
    print("[PLOT] 01_boxplot_by_rule_set.png ...")
    funciones = sort_functions(df['funcion'].unique())
    n_func = len(funciones)
    ncols = min(3, n_func)
    nrows = int(np.ceil(n_func / ncols))

    fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 4 * nrows))
    if nrows * ncols == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for i, func in enumerate(funciones):
        ax = axes[i]
        sub = df[df['funcion'] == func].copy()
        order = sort_display_names(sub['display_name'].unique())
        sns.boxplot(data=sub, x='display_name', y='fitness', order=order,
                    ax=ax, palette='Set2', linewidth=0.7, fliersize=2)
        ax.set_title(f'{func} ({CATEGORIES.get(func, "")})', fontsize=10)
        ax.set_xlabel('')
        ax.set_ylabel('Fitness')
        ax.tick_params(axis='x', rotation=75, labelsize=7)
        ax.grid(True, alpha=0.3, linestyle='--')

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.suptitle('Fitness Distribution by Rule Set Configuration', fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '01_boxplot_by_rule_set.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_boxplot_granularity(df):
    """02: 3L vs 5L boxplots — one panel per function, gap_abs on y-axis."""
    print("[PLOT] 02_boxplot_by_granularity.png ...")
    fcs_only = df[df['MH'].str.startswith('PSO_FCS')].copy()
    if fcs_only.empty:
        print("  [SKIP] No PSO_FCS data")
        return

    # Normalize granularity as integers (3 or 5) to avoid string mismatches like '3.0L'.
    fcs_only['granularity'] = pd.to_numeric(fcs_only['num_labels'], errors='coerce').round().astype('Int64')
    funciones = sort_functions(fcs_only['funcion'].unique())
    n_func = len(funciones)
    ncols = min(3, n_func)
    nrows = int(np.ceil(n_func / ncols))

    fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 4 * nrows))
    if nrows * ncols == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for i, func in enumerate(funciones):
        ax = axes[i]
        sub = fcs_only[fcs_only['funcion'] == func]
        if sub.empty:
            ax.set_visible(False)
            continue
        data_3l = sub[sub['granularity'] == 3]['gap_abs'].dropna().values
        data_5l = sub[sub['granularity'] == 5]['gap_abs'].dropna().values
        if len(data_3l) == 0 and len(data_5l) == 0:
            ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'{func} ({CATEGORIES.get(func, "")})', fontsize=9)
            ax.set_axis_off()
            continue
        bp = ax.boxplot([data_3l, data_5l], tick_labels=['3L', '5L'], patch_artist=True,
                        medianprops=dict(color='black', linewidth=1.5))
        for patch, color in zip(bp['boxes'], ['#457B9D', '#E9C46A']):
            patch.set_facecolor(color)
            patch.set_alpha(0.8)
        opt_label = sub['optimum_group_label'].iloc[0] if len(sub) > 0 else ''
        ax.set_title(f'{func} ({CATEGORIES.get(func, "")}) — {opt_label}', fontsize=9)
        ax.set_xlabel('Granularity (labels)')
        ax.set_ylabel('Average Gap to Optimum')
        ax.grid(True, alpha=0.3, linestyle='--')

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    plt.suptitle('Granularity Effect (3L vs 5L) per Function — Average Gap to Optimum', fontsize=12, y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '02_boxplot_by_granularity.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_convergence(df_iter, colors, markers):
    """03: Convergence curves (mean fitness over iterations) per function."""
    print("[PLOT] 03_convergence_by_function.png ...")
    funciones = sort_functions(df_iter['funcion'].unique())
    mh_list = sorted(df_iter['MH'].unique(), key=lambda x: display_name_sort_key(build_display_name(x)))
    n_func = len(funciones)
    ncols = min(3, n_func)
    nrows = int(np.ceil(n_func / ncols))

    fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 4 * nrows))
    if nrows * ncols == 1:
        axes = np.array([axes])
    axes = axes.flatten()

    for i, func in enumerate(funciones):
        ax = axes[i]
        df_f = df_iter[df_iter['funcion'] == func]
        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh]
            if df_m.empty:
                continue
            agg = df_m.groupby('iter')['best_fitness'].mean().reset_index()
            c = colors.get(mh, '#999')
            lw = 2 if not mh.startswith('PSO_FCS') else 1
            ls = '--' if not mh.startswith('PSO_FCS') else '-'
            ax.plot(agg['iter'], agg['best_fitness'], color=c,
                    linewidth=lw, linestyle=ls, label=build_display_name(mh), alpha=0.85)
        ax.set_title(f'{func} ({CATEGORIES.get(func, "")})', fontsize=10)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Mean Best Fitness')
        ax.set_yscale('symlog')
        ax.grid(True, alpha=0.3, linestyle='--')

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=min(6, len(labels)),
               bbox_to_anchor=(0.5, -0.02), fontsize=7)
    plt.suptitle('Convergence Curves by Function', fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '03_convergence_by_function.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_w_trajectories(df_iter, colors):
    """04: w over iterations per rule set (mean across all functions)."""
    print("[PLOT] 04_w_trajectory_comparison.png ...")
    mh_list = sorted(df_iter['MH'].unique(), key=lambda x: display_name_sort_key(build_display_name(x)))

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    pso_mh = next((mh for mh in mh_list if parse_mh_name(mh)['base'] == 'PSO'), None)
    pso_agg = None
    if pso_mh is not None:
        df_pso = df_iter[df_iter['MH'] == pso_mh]
        if not df_pso.empty:
            pso_agg = df_pso.groupby('iter')['w'].mean().reset_index()

    for ax_idx, num_l in enumerate([3, 5]):
        ax = axes[ax_idx]

        # Explicit PSO-STD baseline in red for both panels.
        if pso_agg is not None:
            ax.plot(pso_agg['iter'], pso_agg['w'], color='#D62828', linewidth=2.6,
                    linestyle='--', label='PSO-STD', alpha=0.95, zorder=5)

        for mh in mh_list:
            info = parse_mh_name(mh)
            if info['base'] == 'PSO':
                continue
            if info['num_labels'] != num_l:
                continue

            df_m = df_iter[df_iter['MH'] == mh]
            if df_m.empty:
                continue
            agg = df_m.groupby('iter')['w'].mean().reset_index()
            c = colors.get(mh, '#999')
            lw = 1.2
            ls = '-'
            ax.plot(agg['iter'], agg['w'], color=c, linewidth=lw,
                    linestyle=ls, label=build_display_name(mh), alpha=0.85)

        ax.set_title(f'{"3-Label" if num_l == 3 else "5-Label"} System', fontsize=11)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Inertia Weight (w)')
        ax.set_ylim(0.0, 1.0)
        ax.legend(fontsize=7, loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')

    plt.suptitle('Inertia Weight Trajectories by Rule Set', fontsize=13)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '04_w_trajectory_comparison.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_mirror_pairs(df_iter, colors):
    """05: Mirror pair overlay — R1 vs R2, R3 vs R4, R5 vs R8, R6 vs R7."""
    print("[PLOT] 05_mirror_pair_overlay.png ...")
    fig, axes = plt.subplots(2, 4, figsize=(18, 8))

    for col, (r_a, r_b) in enumerate(MIRROR_PAIRS):
        for row, num_l in enumerate([3, 5]):
            ax = axes[row, col]
            label_a = f"R{r_a[1:]}-{num_l}L"
            label_b = f"R{r_b[1:]}-{num_l}L"

            for label, ls, c_name in [(label_a, '-', '#2A9D8F'), (label_b, '--', '#E63946')]:
                df_m = df_iter[df_iter['display_name'] == label]
                if df_m.empty:
                    continue
                agg = df_m.groupby('iter').agg(
                    w_mean=('w', 'mean'), w_std=('w', 'std')).reset_index()
                ax.plot(agg['iter'], agg['w_mean'], color=c_name, linewidth=1.5,
                        linestyle=ls, label=label)
                ax.fill_between(agg['iter'],
                                agg['w_mean'] - agg['w_std'],
                                agg['w_mean'] + agg['w_std'],
                                color=c_name, alpha=0.1)

            meta_a = RULE_META.get(r_a, {})
            meta_b = RULE_META.get(r_b, {})
            ax.set_title(f'{r_a} ({meta_a.get("label","")}) vs {r_b} ({meta_b.get("label","")}) [{num_l}L]',
                         fontsize=8)
            ax.set_xlabel('Iteration')
            ax.set_ylabel('w')
            ax.set_ylim(0.0, 1.0)
            ax.legend(fontsize=7)
            ax.grid(True, alpha=0.3, linestyle='--')

    plt.suptitle('Mirror Pair w Trajectory Comparison', fontsize=13)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '05_mirror_pair_overlay.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_factorial_interaction(df, df_fact):
    """06: Factorial interaction — matrix 2x3, one panel per function."""
    print("[PLOT] 06_factorial_interaction.png ...")
    funciones = sort_functions(df['funcion'].unique())
    ncols = 3
    nrows = 2
    prog_map = {'↓': 0, '—': 1, '↑': 2}

    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 9), squeeze=False)
    axes_flat = axes.flatten()

    fcs = df[df['MH'].str.startswith('PSO_FCS')].copy()

    for i, func in enumerate(funciones):
        ax = axes_flat[i]
        sub_func = fcs[fcs['funcion'] == func]
        opt_label = sub_func['optimum_group_label'].iloc[0] if len(sub_func) > 0 else ''
        metric_col = 'fitness' if opt_label == 'Optimum = 0' else 'gap_abs'
        metric_label = 'Average Fitness' if opt_label == 'Optimum = 0' else 'Average Gap to Optimum'

        for div_dir, marker, color in [('—', 'o', '#264653'), ('→', 's', '#2A9D8F'), ('←', '^', '#E76F51')]:
            pts_x, pts_y, pts_e = [], [], []
            for prog_dir in ['↓', '—', '↑']:
                matching = [
                    (rs, meta) for rs, meta in RULE_META.items()
                    if meta['progress'] == prog_dir and meta['diversity'] == div_dir
                ]
                if not matching:
                    continue
                rs_names = [f"R{rs[1:]}-3L" for rs, _ in matching] + [f"R{rs[1:]}-5L" for rs, _ in matching]
                sub_pts = sub_func[sub_func['display_name'].isin(rs_names)]
                if sub_pts.empty:
                    continue
                pts_x.append(prog_map[prog_dir])
                pts_y.append(sub_pts[metric_col].mean())
                pts_e.append(sub_pts[metric_col].std())

            if pts_x:
                ax.plot(pts_x, pts_y, marker=marker, color=color,
                        linewidth=2, markersize=7, label=f'Div {div_dir}')
                ax.errorbar(pts_x, pts_y, yerr=pts_e, color=color,
                            fmt='none', capsize=4, alpha=0.5)

        ax.set_xticks([0, 1, 2])
        ax.set_xticklabels(['↓ (H→L)', '— (flat)', '↑ (L→H)'], fontsize=8)
        ax.set_xlabel('Progress Direction')
        ax.set_ylabel(metric_label)
        ax.set_title(f'{func} ({CATEGORIES.get(func, "")}) — {metric_label}', fontsize=9)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3, linestyle='--')

    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.suptitle('Progress × Diversity Interaction per Function (2x3 Matrix)', fontsize=13)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '06_factorial_interaction.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_cd_diagram(df):
    """07: Per-function ranking chart (2x3 matrix), avoiding all-functions aggregation."""
    print("[PLOT] 07_cd_diagram.png ...")
    funciones = sort_functions(df['funcion'].unique())
    fig, axes = plt.subplots(2, 3, figsize=(18, 9), squeeze=False)
    axes_flat = axes.flatten()

    for i, func in enumerate(funciones):
        ax = axes_flat[i]
        sub = df[df['funcion'] == func].copy()
        if sub.empty:
            ax.set_visible(False)
            continue
        opt_label = sub['optimum_group_label'].iloc[0] if len(sub) > 0 else ''
        metric_col = 'fitness' if opt_label == 'Optimum = 0' else 'gap_abs'
        metric_label = 'Average Fitness' if opt_label == 'Optimum = 0' else 'Average Gap to Optimum'

        rank_tbl = sub.groupby('display_name')[metric_col].mean().reset_index()
        rank_tbl = rank_tbl.sort_values(metric_col, ascending=True)
        rank_tbl['display_name'] = pd.Categorical(rank_tbl['display_name'], categories=rank_tbl['display_name'], ordered=True)

        sns.barplot(data=rank_tbl, y='display_name', x=metric_col, ax=ax, palette='viridis')
        ax.set_title(f'{func} — {metric_label}', fontsize=10)
        ax.set_xlabel(metric_label)
        ax.set_ylabel('Configuration')
        ax.grid(True, alpha=0.3, axis='x', linestyle='--')

    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.suptitle('Per-Function Ranking by Configuration (2x3 Matrix)', fontsize=13)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '07_cd_diagram.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_heatmap_fitness(stats_config):
    """08: Two heatmaps of mean absolute gap — one per optimum group."""
    print("[PLOT] 08_heatmap_mean_fitness.png ...")
    groups = [g for g in ['Optimum = 0', 'Optimum != 0']
              if g in stats_config['optimum_group_label'].dropna().unique()]
    if not groups:
        print("  [SKIP] No data for heatmap")
        return

    fig, axes = plt.subplots(1, len(groups),
                              figsize=(max(5, 2.5 * 3) * len(groups), max(6, len(stats_config['display_name'].unique()) * 0.4)),
                              squeeze=False)

    for col_idx, grp_label in enumerate(groups):
        sub = stats_config[stats_config['optimum_group_label'] == grp_label]
        pivot = sub.pivot_table(index='display_name', columns='funcion', values='gap_abs_mean')
        pivot = pivot.reindex(index=sort_display_names(pivot.index), columns=sort_functions(pivot.columns))
        ax = axes[0, col_idx]
        if pivot.empty:
            ax.set_visible(False)
            continue
        grp_display = grp_label.replace('!= 0', '≠ 0')
        sns.heatmap(pivot, annot=True, fmt='.2e', cmap='RdYlGn_r', ax=ax,
                    linewidths=0.5, linecolor='white',
                    cbar_kws={'label': 'Average Gap to Optimum'})
        ax.set_title(f'Average Gap to Optimum  ({grp_display})', fontsize=11)
        ax.set_ylabel('Configuration')
        ax.set_xlabel('Function')

    plt.suptitle('Mean Average Gap to Optimum per Configuration and Function', fontsize=13)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '08_heatmap_mean_fitness.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_violin_by_category(df):
    """09: Violin plot per function (2x3 matrix), not by category."""
    print("[PLOT] 09_violin_by_category.png ...")
    fcs_only = df[df['MH'].str.startswith('PSO_FCS')].copy()
    if fcs_only.empty:
        print("  [SKIP] No PSO_FCS data")
        return

    funciones = sort_functions(fcs_only['funcion'].unique())
    fig, axes = plt.subplots(2, 3, figsize=(18, 9), squeeze=False)
    axes_flat = axes.flatten()

    for i, func in enumerate(funciones):
        ax = axes_flat[i]
        sub = fcs_only[fcs_only['funcion'] == func].copy()
        if sub.empty:
            ax.set_visible(False)
            continue
        opt_label = sub['optimum_group_label'].iloc[0] if len(sub) > 0 else ''
        metric_col = 'fitness' if opt_label == 'Optimum = 0' else 'gap_abs'
        metric_label = 'Average Fitness' if opt_label == 'Optimum = 0' else 'Average Gap to Optimum'
        order = sort_display_names(sub['display_name'].unique())

        sns.violinplot(data=sub, x='display_name', y=metric_col, order=order,
                       ax=ax, palette='Set2', scale='width', inner='box', linewidth=0.7)
        ax.set_title(f'{func} ({CATEGORIES.get(func, "")}) — {metric_label}', fontsize=9)
        ax.set_xlabel('')
        ax.set_ylabel(metric_label)
        ax.tick_params(axis='x', rotation=75, labelsize=7)
        ax.grid(True, alpha=0.3, linestyle='--')

    for j in range(i + 1, len(axes_flat)):
        axes_flat[j].set_visible(False)

    plt.suptitle('Distribution per Function (2x3 Matrix)', fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '09_violin_by_category.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


def plot_granularity_paired(df):
    """10: Two heatmaps (Optimum=0 vs Optimum!=0) using average gap to optimum."""
    print("[PLOT] 10_granularity_paired.png ...")
    rule_sets = sorted(RULE_META.keys(), key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
    group_to_funcs = {
        'Optimum = 0': sort_functions(df[df['optimum_group_label'] == 'Optimum = 0']['funcion'].unique()),
        'Optimum != 0': sort_functions(df[df['optimum_group_label'] == 'Optimum != 0']['funcion'].unique()),
    }
    groups = [g for g in ['Optimum = 0', 'Optimum != 0'] if len(group_to_funcs[g]) > 0]
    if not groups:
        print("  [SKIP] No data for granularity paired plot")
        return

    fig, axes = plt.subplots(1, len(groups), figsize=(8 * len(groups), 6), squeeze=False)

    for col_idx, grp_label in enumerate(groups):
        funcs = group_to_funcs[grp_label]
        matrix = pd.DataFrame(index=[f'R{rs[1:]}' for rs in rule_sets], columns=funcs, dtype=float)

        for rs in rule_sets:
            label_3 = f"R{rs[1:]}-3L"
            label_5 = f"R{rs[1:]}-5L"
            for func in funcs:
                g3 = df[(df['display_name'] == label_3) & (df['funcion'] == func)]['gap_abs']
                g5 = df[(df['display_name'] == label_5) & (df['funcion'] == func)]['gap_abs']
                if len(g3) > 0 and len(g5) > 0:
                    mean3 = g3.mean()
                    mean5 = g5.mean()
                    denom = mean3 if abs(mean3) > 1e-15 else 1.0
                    matrix.loc[f'R{rs[1:]}', func] = (mean3 - mean5) / denom

        matrix = matrix.astype(float)
        max_abs = matrix.abs().max().max()
        if np.isnan(max_abs) or max_abs == 0:
            max_abs = 1.0

        ax = axes[0, col_idx]
        grp_display = grp_label.replace('!= 0', '≠ 0')
        sns.heatmap(matrix, annot=True, fmt='.2f', cmap='RdYlGn',
                    center=0, vmin=-max_abs, vmax=max_abs,
                    ax=ax, linewidths=0.5, linecolor='white',
                    cbar_kws={'label': 'Relative Improvement\n(Gap 3L - Gap 5L) / Gap 3L\n(+) = 5L better,  (-) = 3L better'})
        ax.set_title(f'3L vs. 5L Granularity Effect  ({grp_display})', fontsize=10)
        ax.set_xlabel('Function')
        ax.set_ylabel('Rule Set')

    plt.suptitle('Granularity Effect (3L vs. 5L): Relative Improvement by Average Gap to Optimum', fontsize=12)
    plt.tight_layout()
    plt.savefig(OUTPUT_PLOTS / '10_granularity_paired.png', dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print("  [OK]")


# ===================================================================
# MAIN PIPELINE
# ===================================================================

def main():
    """Execute the complete WEA 2026 analysis pipeline."""
    import time as _time

    start = _time.time()

    print("\n" + "=" * 80)
    print("  WEA 2026 ANALYSIS PIPELINE")
    print("  Sensitivity Analysis of Fuzzy Rule Base Structure")
    print("=" * 80 + "\n")

    # Create output directories
    OUTPUT_ANALYSIS.mkdir(parents=True, exist_ok=True)
    OUTPUT_PLOTS.mkdir(parents=True, exist_ok=True)

    # LEVEL 1: Extract raw data
    print("\n--- LEVEL 1: RAW DATA EXTRACTION ---\n")
    df = extract_experiment_results()
    if df is None or df.empty:
        print("[ABORT] No data to analyze. Run experiments first.")
        return

    df_iter = extract_iteration_data()

    # LEVEL 2: Descriptive statistics
    print("\n--- LEVEL 2: DESCRIPTIVE STATISTICS ---\n")
    stats_config = compute_descriptive_stats(df)

    # LEVEL 3: Statistical tests
    print("\n--- LEVEL 3: STATISTICAL TESTS ---\n")
    ranking_df = friedman_ranking(df, 'friedman_ranking.csv', 'all functions')
    friedman_ranking(df[df['optimum_group'] == 'optimum_zero'],
                     'friedman_ranking_optimum_zero.csv', 'optimum = 0')
    friedman_ranking(df[df['optimum_group'] == 'optimum_nonzero'],
                     'friedman_ranking_optimum_nonzero.csv', 'optimum != 0')
    wilcoxon_pairwise(df)
    df_mirror = mirror_pair_analysis(df)
    df_gran = granularity_effect(df)
    df_fact = factorial_interaction(df)
    top_configs(df, output_name='top_configs_global.csv', label='all functions')
    top_configs(df[df['optimum_group'] == 'optimum_zero'],
                output_name='top_configs_optimum_zero.csv', label='optimum = 0')
    top_configs(df[df['optimum_group'] == 'optimum_nonzero'],
                output_name='top_configs_optimum_nonzero.csv', label='optimum != 0')

    # PLOTS
    print("\n--- GENERATING PLOTS ---\n")
    mh_list = sorted(df['MH'].unique(), key=lambda x: display_name_sort_key(build_display_name(x)))
    colors, markers_dict = assign_styles(mh_list)

    plot_boxplot_by_rule(df, colors)
    plot_boxplot_granularity(df)

    if df_iter is not None and not df_iter.empty:
        plot_convergence(df_iter, colors, markers_dict)
        plot_w_trajectories(df_iter, colors)
        plot_mirror_pairs(df_iter, colors)

    plot_factorial_interaction(df, df_fact)
    plot_cd_diagram(df)
    plot_heatmap_fitness(stats_config)
    plot_violin_by_category(df)
    plot_granularity_paired(df)

    elapsed = _time.time() - start

    print("\n" + "=" * 80)
    print("  PIPELINE COMPLETE")
    print("=" * 80)
    print(f"\n  Time: {elapsed:.1f}s")
    print(f"\n  Analysis CSVs: {OUTPUT_ANALYSIS}/")
    print(f"  Plots:         {OUTPUT_PLOTS}/")
    print(f"\n  Files generated:")
    for f in sorted(OUTPUT_ANALYSIS.glob('*.csv')):
        print(f"    [CSV]  {f.name}")
    for f in sorted(OUTPUT_PLOTS.glob('*.png')):
        print(f"    [PNG]  {f.name}")
    print()


if __name__ == '__main__':
    warnings.filterwarnings('ignore', category=FutureWarning)
    main()



