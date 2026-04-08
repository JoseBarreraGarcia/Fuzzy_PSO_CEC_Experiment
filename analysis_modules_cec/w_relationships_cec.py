"""
W-METRIC RELATIONSHIP ANALYSIS FOR BENCHMARK FUNCTIONS

For each PSO_FCS variant and benchmark function, reconstructs the
inertia weight (w) from the fuzzy controller using the per-iteration
DIV values stored in the database, then plots the relationships:

  - w vs Diversity  (scatter + trend)
  - w vs Progress   (line per run, aggregated)
  - w vs Fitness    (scatter + trend)

Also generates a summary correlation heatmap across all configs/functions.

Fully adaptive: auto-detects MH configs, input/output sets, granularity
levels, and benchmark functions from the data.

Outputs (in Resultados/resumen/level2_aggregated_cec/w_relationships/):
  - w_vs_metrics_{function}.png                Panel per function
  - w_vs_diversity_by_config.png               Scatter grid (config × func)
  - w_trajectory_by_config.png                 w over iterations
  - w_correlation_heatmap.png                  Summary heatmap
  - w_relationships_data.csv                   Underlying data
"""

import os
import sys
from pathlib import Path
from io import StringIO

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns

sys.path.insert(0, str(Path(__file__).parent.parent))

from BD.sqlite import BD
from FUZZY.fuzzy_controller_w import get_fuzzy_controller
from scipy.interpolate import RegularGridInterpolator

# ---------------------------------------------------------------------------
# Plot style
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

OUTPUT_DIR = 'Resultados/resumen/level2_aggregated_cec/w_relationships'


# ---------------------------------------------------------------------------
# MH name parsing (reuse from convergence_curves_cec)
# ---------------------------------------------------------------------------

def parse_mh_name(mh_name):
    """Parse 'PSO_FCS:A:3:I1' → {base, output_set, num_labels, input_set}."""
    parts = mh_name.split(':')
    if len(parts) >= 4:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': int(parts[2]), 'input_set': parts[3],
            'short_label': f"{parts[3]}-{parts[2]}L",
        }
    elif len(parts) >= 3:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': int(parts[2]), 'input_set': None,
            'short_label': f"{parts[1]}-{parts[2]}L",
        }
    elif len(parts) == 2:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': None, 'input_set': None,
            'short_label': parts[1],
        }
    return {
        'base': mh_name, 'output_set': None,
        'num_labels': None, 'input_set': None,
        'short_label': mh_name,
    }


def build_display_name(mh_name):
    info = parse_mh_name(mh_name)
    if info['base'] == 'PSO' and info['output_set'] is None:
        return 'PSO (linear)'
    return info['short_label']


# ---------------------------------------------------------------------------
# Dynamic styles
# ---------------------------------------------------------------------------
_BASE_COLORS = [
    '#E63946', '#457B9D', '#2A9D8F', '#E9C46A', '#F4A261',
    '#264653', '#A8DADC', '#6A0572', '#1D3557', '#B5838D',
    '#606C38', '#BC6C25',
]
_MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X', 'p', 'h', '*', '<', '>']


def assign_styles(mh_names):
    baseline = [m for m in mh_names if not m.startswith('PSO_FCS')]
    fcs = sorted([m for m in mh_names if m.startswith('PSO_FCS')],
                 key=lambda x: build_display_name(x))
    ordered = baseline + fcs
    colors, markers = {}, {}
    for i, mh in enumerate(ordered):
        colors[mh] = _BASE_COLORS[i % len(_BASE_COLORS)]
        markers[mh] = _MARKERS[i % len(_MARKERS)]
    return colors, markers


# ---------------------------------------------------------------------------
# w reconstruction  (pre-computed lookup table for speed)
# ---------------------------------------------------------------------------

# Cache: controller → 2D interpolator
_interp_cache = {}
_LUT_RES = 101  # grid resolution for lookup table

def _build_w_interpolator(w_set, num_labels, input_set):
    """Build a 2D interpolation function for (diversity_ratio, progress) → w."""
    key = (w_set, num_labels, input_set)
    if key in _interp_cache:
        return _interp_cache[key]

    fcs = get_fuzzy_controller(w_set, num_labels=num_labels, input_set=input_set)
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
    """Linear decreasing schedule for baseline PSO."""
    iters = np.arange(n_iters)
    w_vals = w_start - (w_start - w_end) * iters / max(max_iter, 1)
    return np.clip(w_vals, w_end, w_start)


def _compute_w_for_fcs(div_series, max_iter, mh_name):
    """Reconstruct w from DIV values using pre-computed lookup table.

    div_series: array of per-iteration DIV (raw, not normalized).
    max_iter: total iterations (for computing progress).
    mh_name: e.g. 'PSO_FCS:A:3:I1' (to pick the right controller).
    """
    info = parse_mh_name(mh_name)
    w_set = info['output_set'] or 'A'
    num_labels = info['num_labels'] or 3
    input_set = info['input_set'] or 'I1'

    interp = _build_w_interpolator(w_set, num_labels, input_set)

    divs = np.array(div_series, dtype=float)
    n = len(divs)

    # Track maxDiversity as the solver does (running max)
    max_div_running = np.maximum.accumulate(np.maximum(divs, 1e-12))
    diversity_ratio = np.clip(divs / max_div_running, 0.0, 1.0)
    progress = np.clip(np.arange(n) / max(max_iter, 1), 0.0, 1.0)

    # Vectorized interpolation
    points = np.column_stack([diversity_ratio, progress])
    w_vals = interp(points)

    return w_vals


# ---------------------------------------------------------------------------
# Data extraction + w reconstruction
# ---------------------------------------------------------------------------

def extract_data_with_w():
    """Read all iteration BLOBs, reconstruct w, return a DataFrame."""

    bd = BD()
    bd.conectar()
    cursor = bd.getCursor()

    cursor.execute("""
        SELECT it.fk_id_experimento, it.archivo, exp.MH, inst.nombre, exp.paramMH
        FROM iteraciones it
        JOIN experimentos exp ON it.fk_id_experimento = exp.id_experimento
        JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
        WHERE inst.tipo_problema = 'BEN'
    """)

    records = []
    skipped = 0

    rows = cursor.fetchall()
    total = len(rows)
    for idx, (exp_id, blob, mh, funcion, paramMH) in enumerate(rows):
        if (idx + 1) % 100 == 0 or idx == total - 1:
            print(f"\r  Processing {idx+1}/{total} experiments...", end='', flush=True)
        if blob is None:
            skipped += 1
            continue
        try:
            content = blob.decode('utf-8', errors='ignore') if isinstance(blob, bytes) else str(blob)
            df_iter = pd.read_csv(StringIO(content))

            # Normalize column names
            col_map = {}
            for c in df_iter.columns:
                cl = c.strip().lower()
                if cl == 'iter':
                    col_map[c] = 'iter'
                elif cl == 'best_fitness':
                    col_map[c] = 'best_fitness'
                elif cl == 'div':
                    col_map[c] = 'DIV'
            df_iter = df_iter.rename(columns=col_map)

            if 'best_fitness' not in df_iter.columns or 'DIV' not in df_iter.columns:
                skipped += 1
                continue

            n = len(df_iter)
            # Parse maxIter from paramMH ("iter:500,pop:50,...")
            max_iter = 500  # default
            if paramMH:
                for token in paramMH.split(','):
                    if token.strip().startswith('iter:'):
                        try:
                            max_iter = int(token.strip().split(':')[1])
                        except (ValueError, IndexError):
                            pass

            # Reconstruct w
            if mh.startswith('PSO_FCS'):
                w_vals = _compute_w_for_fcs(df_iter['DIV'].values, max_iter, mh)
            else:
                w_vals = _compute_w_for_pso(n, max_iter)

            # Compute progress for each row
            iters = df_iter['iter'].values if 'iter' in df_iter.columns else np.arange(n)
            progress = iters / max(max_iter, 1)

            # Compute diversity_ratio (running-max normalization)
            divs = df_iter['DIV'].values
            max_div_running = np.maximum.accumulate(np.maximum(divs, 1e-12))
            diversity_ratio = divs / max_div_running

            sub = pd.DataFrame({
                'iter': iters,
                'w': w_vals,
                'DIV': divs,
                'diversity_ratio': diversity_ratio,
                'progress': progress,
                'best_fitness': df_iter['best_fitness'].values,
                'id_experimento': exp_id,
                'MH': mh,
                'funcion': funcion,
            })
            records.append(sub)
        except Exception:
            skipped += 1
            continue

    bd.desconectar()
    print()  # newline after progress counter

    if not records:
        print("[WARN] No iteration data found")
        return None

    df = pd.concat(records, ignore_index=True)
    print(f"[OK] Extracted {len(df):,} rows from {len(records)} experiments (skipped {skipped})")
    return df


# ---------------------------------------------------------------------------
# Plot: 3-panel per function (w vs diversity, w vs progress, w vs fitness)
# ---------------------------------------------------------------------------

def plot_w_panels_per_function(df, output_dir, colors, markers):
    """For each function: 3-panel showing w vs diversity_ratio, progress, fitness."""

    funciones = sorted(df['funcion'].unique())
    fcs_only = df[df['MH'].str.startswith('PSO_FCS')]
    mh_list = sorted(fcs_only['MH'].unique(), key=lambda x: build_display_name(x))

    for funcion in funciones:
        df_f = fcs_only[fcs_only['funcion'] == funcion]
        if df_f.empty:
            continue

        fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))

        # ----- Panel 1: w vs diversity_ratio -----
        ax = axes[0]
        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh]
            # Aggregate: mean w per diversity_ratio bin
            df_m = df_m.copy()
            df_m['div_bin'] = pd.cut(df_m['diversity_ratio'], bins=30, labels=False)
            agg = df_m.groupby('div_bin').agg(
                div_r=('diversity_ratio', 'mean'), w_mean=('w', 'mean')
            ).dropna()
            c = colors.get(mh, '#999')
            ax.plot(agg['div_r'], agg['w_mean'], color=c, linewidth=1.2,
                    label=build_display_name(mh), alpha=0.85)
        # Add PSO baseline
        df_pso_div = df[(df['MH'] == 'PSO') & (df['funcion'] == funcion)]
        if not df_pso_div.empty:
            df_pso_div = df_pso_div.copy()
            df_pso_div['div_bin'] = pd.cut(df_pso_div['diversity_ratio'], bins=30, labels=False)
            agg_pso = df_pso_div.groupby('div_bin').agg(
                div_r=('diversity_ratio', 'mean'), w_mean=('w', 'mean')
            ).dropna()
            ax.plot(agg_pso['div_r'], agg_pso['w_mean'], color=colors.get('PSO', '#E63946'),
                    linewidth=2, linestyle='--', label='PSO (linear)', alpha=0.9)
        ax.set_xlabel('Diversity Ratio')
        ax.set_ylabel('Inertia Weight (w)')
        ax.set_title('w vs Diversity')
        ax.grid(True, alpha=0.3, linestyle='--')

        # ----- Panel 2: w vs progress -----
        ax = axes[1]
        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh]
            agg = df_m.groupby('iter').agg(
                progress=('progress', 'mean'), w_mean=('w', 'mean'), w_std=('w', 'std')
            ).reset_index()
            c = colors.get(mh, '#999')
            ax.plot(agg['progress'], agg['w_mean'], color=c, linewidth=1.2,
                    label=build_display_name(mh), alpha=0.85)
            ax.fill_between(agg['progress'],
                            agg['w_mean'] - agg['w_std'],
                            agg['w_mean'] + agg['w_std'],
                            color=c, alpha=0.07)
        # Add PSO baseline
        df_pso = df[(df['MH'] == 'PSO') & (df['funcion'] == funcion)]
        if not df_pso.empty:
            agg_pso = df_pso.groupby('iter').agg(
                progress=('progress', 'mean'), w_mean=('w', 'mean')
            ).reset_index()
            ax.plot(agg_pso['progress'], agg_pso['w_mean'], color=colors.get('PSO', '#E63946'),
                    linewidth=2, linestyle='--', label='PSO (linear)', alpha=0.9)
        ax.set_xlabel('Iteration Progress')
        ax.set_ylabel('Inertia Weight (w)')
        ax.set_title('w vs Progress')
        ax.grid(True, alpha=0.3, linestyle='--')

        # ----- Panel 3: w vs fitness (scatter, subsampled) -----
        ax = axes[2]
        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh]
            # Subsample for scatter readability
            sample = df_m.sample(n=min(500, len(df_m)), random_state=42)
            c = colors.get(mh, '#999')
            mk = markers.get(mh, 'o')
            ax.scatter(sample['w'], sample['best_fitness'], color=c, marker=mk,
                       s=8, alpha=0.3, label=build_display_name(mh))
        # Add PSO baseline
        df_pso_fit = df[(df['MH'] == 'PSO') & (df['funcion'] == funcion)]
        if not df_pso_fit.empty:
            sample_pso = df_pso_fit.sample(n=min(500, len(df_pso_fit)), random_state=42)
            ax.scatter(sample_pso['w'], sample_pso['best_fitness'],
                       color=colors.get('PSO', '#E63946'), marker=markers.get('PSO', 'o'),
                       s=12, alpha=0.4, label='PSO (linear)', edgecolors='none')
        ax.set_xlabel('Inertia Weight (w)')
        ax.set_ylabel('Best Fitness')
        ax.set_title('w vs Fitness')
        ax.grid(True, alpha=0.3, linestyle='--')

        # Shared legend below
        handles, labels = axes[1].get_legend_handles_labels()
        fig.legend(handles, labels, loc='lower center',
                   ncol=min(5, len(labels)), framealpha=0.9,
                   bbox_to_anchor=(0.5, -0.04))

        fig.suptitle(f'{funcion} — Inertia Weight Relationships', fontweight='bold', y=1.01)
        plt.tight_layout(rect=[0, 0.06, 1, 0.98])

        path = os.path.join(output_dir, f'w_vs_metrics_{funcion}.png')
        plt.savefig(path, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        print(f"  > w_vs_metrics_{funcion}.png")


# ---------------------------------------------------------------------------
# Plot: w trajectory over iterations by config
# ---------------------------------------------------------------------------

def plot_w_trajectory(df, output_dir, colors):
    """w over iterations, one subplot per function, lines per config."""

    fcs = df[df['MH'].str.startswith('PSO_FCS')]
    funciones = sorted(fcs['funcion'].unique())
    mh_list = sorted(fcs['MH'].unique(), key=lambda x: build_display_name(x))

    ncols = min(3, len(funciones))
    nrows = int(np.ceil(len(funciones) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.0 * ncols, 3.8 * nrows),
                              sharex=True, squeeze=False)

    for idx, funcion in enumerate(funciones):
        ax = axes[idx // ncols][idx % ncols]
        df_f = fcs[fcs['funcion'] == funcion]

        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh]
            agg = df_m.groupby('iter')['w'].agg(['mean', 'std']).reset_index()
            c = colors.get(mh, '#999')
            ax.plot(agg['iter'], agg['mean'], color=c, linewidth=1.1,
                    label=build_display_name(mh))
            ax.fill_between(agg['iter'], agg['mean'] - agg['std'],
                            agg['mean'] + agg['std'], color=c, alpha=0.07)

        # PSO baseline
        df_pso = df[(df['MH'] == 'PSO') & (df['funcion'] == funcion)]
        if not df_pso.empty:
            agg_pso = df_pso.groupby('iter')['w'].mean().reset_index()
            ax.plot(agg_pso['iter'], agg_pso['w'], color=colors.get('PSO', '#E63946'),
                    linewidth=2, linestyle='--', label='PSO (linear)', alpha=0.8)

        ax.set_title(funcion, fontweight='bold')
        ax.set_ylabel('w')
        ax.grid(True, alpha=0.3, linestyle='--')

    for idx in range(len(funciones), nrows * ncols):
        axes[idx // ncols][idx % ncols].set_visible(False)

    axes[-1][0].set_xlabel('Iteration')

    handles, labels = axes[0][0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center',
               ncol=min(5, len(labels)), framealpha=0.9,
               bbox_to_anchor=(0.5, -0.02))
    fig.suptitle('Inertia Weight Trajectory by Configuration', fontweight='bold', y=1.01)
    plt.tight_layout(rect=[0, 0.05, 1, 0.98])

    path = os.path.join(output_dir, 'w_trajectory_by_config.png')
    plt.savefig(path, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print(f"  > w_trajectory_by_config.png")


# ---------------------------------------------------------------------------
# Plot: Individual w trajectory per function
# ---------------------------------------------------------------------------

def plot_w_trajectory_individual(df, output_dir, colors):
    """One standalone plot per function: w over iterations for all configs."""

    sub_dir = os.path.join(output_dir, 'w_trajectory')
    os.makedirs(sub_dir, exist_ok=True)

    fcs = df[df['MH'].str.startswith('PSO_FCS')]
    funciones = sorted(fcs['funcion'].unique())
    mh_list = sorted(fcs['MH'].unique(), key=lambda x: build_display_name(x))

    for funcion in funciones:
        fig, ax = plt.subplots(figsize=(7, 4.5))
        df_f = fcs[fcs['funcion'] == funcion]

        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh]
            agg = df_m.groupby('iter')['w'].agg(['mean', 'std']).reset_index()
            c = colors.get(mh, '#999')
            ax.plot(agg['iter'], agg['mean'], color=c, linewidth=1.1,
                    label=build_display_name(mh))
            ax.fill_between(agg['iter'], agg['mean'] - agg['std'],
                            agg['mean'] + agg['std'], color=c, alpha=0.07)

        # PSO baseline
        df_pso = df[(df['MH'] == 'PSO') & (df['funcion'] == funcion)]
        if not df_pso.empty:
            agg_pso = df_pso.groupby('iter')['w'].mean().reset_index()
            ax.plot(agg_pso['iter'], agg_pso['w'], color=colors.get('PSO', '#E63946'),
                    linewidth=2, linestyle='--', label='PSO (linear)', alpha=0.8)

        ax.set_title(f'{funcion} — Inertia Weight Trajectory', fontweight='bold')
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Inertia Weight (w)')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(fontsize=7, loc='best', framealpha=0.9)
        plt.tight_layout()

        path = os.path.join(sub_dir, f'w_trajectory_{funcion}.png')
        plt.savefig(path, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        print(f"  > w_trajectory/{funcion}.png")


# ---------------------------------------------------------------------------
# Plot: Individual w vs diversity per function
# ---------------------------------------------------------------------------

def plot_w_vs_diversity_individual(df, output_dir, colors, markers):
    """One standalone plot per function: w vs diversity_ratio scatter + trend for all configs."""

    sub_dir = os.path.join(output_dir, 'w_vs_diversity')
    os.makedirs(sub_dir, exist_ok=True)

    fcs = df[df['MH'].str.startswith('PSO_FCS')]
    funciones = sorted(fcs['funcion'].unique())
    mh_list = sorted(fcs['MH'].unique(), key=lambda x: build_display_name(x))

    for funcion in funciones:
        fig, ax = plt.subplots(figsize=(7, 5))
        df_f = fcs[fcs['funcion'] == funcion]

        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh]
            if df_m.empty:
                continue
            sample = df_m.sample(n=min(800, len(df_m)), random_state=42)
            c = colors.get(mh, '#999')
            mk = markers.get(mh, 'o')
            ax.scatter(sample['diversity_ratio'], sample['w'], color=c, marker=mk,
                       s=10, alpha=0.25, label=build_display_name(mh), edgecolors='none')
            # Trend line
            if len(sample) > 10:
                z = np.polyfit(sample['diversity_ratio'], sample['w'], 1)
                x_line = np.linspace(sample['diversity_ratio'].min(),
                                     sample['diversity_ratio'].max(), 50)
                ax.plot(x_line, np.polyval(z, x_line), color=c,
                        linewidth=1.2, linestyle='--', alpha=0.7)

        # PSO baseline
        df_pso = df[(df['MH'] == 'PSO') & (df['funcion'] == funcion)]
        if not df_pso.empty:
            sample_pso = df_pso.sample(n=min(800, len(df_pso)), random_state=42)
            ax.scatter(sample_pso['diversity_ratio'], sample_pso['w'],
                       color=colors.get('PSO', '#E63946'), marker=markers.get('PSO', 'o'),
                       s=14, alpha=0.3, label='PSO (linear)', edgecolors='none')
            if len(sample_pso) > 10:
                z = np.polyfit(sample_pso['diversity_ratio'], sample_pso['w'], 1)
                x_line = np.linspace(sample_pso['diversity_ratio'].min(),
                                     sample_pso['diversity_ratio'].max(), 50)
                ax.plot(x_line, np.polyval(z, x_line), color=colors.get('PSO', '#E63946'),
                        linewidth=1.5, linestyle='--', alpha=0.7)

        ax.set_title(f'{funcion} — w vs Diversity Ratio', fontweight='bold')
        ax.set_xlabel('Diversity Ratio')
        ax.set_ylabel('Inertia Weight (w)')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.legend(fontsize=7, loc='best', framealpha=0.9)
        plt.tight_layout()

        path = os.path.join(sub_dir, f'w_vs_diversity_{funcion}.png')
        plt.savefig(path, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        print(f"  > w_vs_diversity/{funcion}.png")


# ---------------------------------------------------------------------------
# Plot: w vs diversity scatter grid (config × function)
# ---------------------------------------------------------------------------

def plot_w_vs_diversity_grid(df, output_dir, colors, markers):
    """Grid of scatter plots: rows = functions, cols = FCS configs."""

    fcs = df[df['MH'].str.startswith('PSO_FCS')]
    funciones = sorted(fcs['funcion'].unique())
    mh_list = sorted(fcs['MH'].unique(), key=lambda x: build_display_name(x))

    nrows = len(funciones)
    ncols = len(mh_list)
    if nrows == 0 or ncols == 0:
        return

    fig, axes = plt.subplots(nrows, ncols, figsize=(2.8 * ncols, 2.5 * nrows),
                              sharex=True, sharey=True, squeeze=False)

    for i, funcion in enumerate(funciones):
        for j, mh in enumerate(mh_list):
            ax = axes[i][j]
            df_m = fcs[(fcs['funcion'] == funcion) & (fcs['MH'] == mh)]
            if df_m.empty:
                ax.set_visible(False)
                continue

            sample = df_m.sample(n=min(800, len(df_m)), random_state=42)
            c = colors.get(mh, '#999')
            ax.scatter(sample['diversity_ratio'], sample['w'],
                       s=4, alpha=0.25, color=c, edgecolors='none')

            # Trend line
            if len(sample) > 10:
                z = np.polyfit(sample['diversity_ratio'], sample['w'], 1)
                x_line = np.linspace(sample['diversity_ratio'].min(),
                                     sample['diversity_ratio'].max(), 50)
                ax.plot(x_line, np.polyval(z, x_line), color='black',
                        linewidth=1.0, linestyle='--', alpha=0.7)

            if i == 0:
                ax.set_title(build_display_name(mh), fontsize=8, fontweight='bold')
            if j == 0:
                ax.set_ylabel(funcion, fontsize=9)
            ax.grid(True, alpha=0.2, linestyle='--')

    fig.text(0.5, -0.01, 'Diversity Ratio', ha='center', fontsize=10)
    fig.text(-0.01, 0.5, 'Inertia Weight (w)', va='center', rotation='vertical', fontsize=10)
    fig.suptitle('w vs Diversity Ratio by Configuration and Function',
                 fontweight='bold', y=1.01)
    plt.tight_layout(rect=[0.02, 0.02, 1, 0.98])

    path = os.path.join(output_dir, 'w_vs_diversity_by_config.png')
    plt.savefig(path, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print(f"  > w_vs_diversity_by_config.png")


# ---------------------------------------------------------------------------
# Plot: correlation heatmap (w vs each metric, per config × function)
# ---------------------------------------------------------------------------

def plot_correlation_heatmap(df, output_dir):
    """Heatmap showing Pearson r between w and each metric for every
    (config, function) pair."""

    fcs = df[df['MH'].str.startswith('PSO_FCS')]
    funciones = sorted(fcs['funcion'].unique())
    mh_list = sorted(fcs['MH'].unique(), key=lambda x: build_display_name(x))
    metrics = ['diversity_ratio', 'progress', 'best_fitness']
    metric_labels = ['Diversity', 'Progress', 'Fitness']

    # Build correlation matrix: rows = config, cols = function_metric
    row_labels = [build_display_name(m) for m in mh_list]
    col_labels = [f"{f}\n{ml}" for f in funciones for ml in metric_labels]
    corr_matrix = np.full((len(mh_list), len(col_labels)), np.nan)

    for i, mh in enumerate(mh_list):
        for j, funcion in enumerate(funciones):
            df_m = fcs[(fcs['MH'] == mh) & (fcs['funcion'] == funcion)]
            if len(df_m) < 10:
                continue
            for k, metric in enumerate(metrics):
                col_idx = j * len(metrics) + k
                if metric in df_m.columns:
                    valid = df_m[['w', metric]].dropna()
                    if len(valid) > 5 and valid[metric].std() > 1e-12:
                        corr_matrix[i, col_idx] = valid['w'].corr(valid[metric])

    fig, ax = plt.subplots(figsize=(max(10, len(col_labels) * 0.7), max(4, len(row_labels) * 0.5)))
    im = ax.imshow(corr_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')

    ax.set_xticks(range(len(col_labels)))
    ax.set_xticklabels(col_labels, fontsize=7, rotation=45, ha='right')
    ax.set_yticks(range(len(row_labels)))
    ax.set_yticklabels(row_labels, fontsize=8)

    # Annotate cells
    for i_r in range(corr_matrix.shape[0]):
        for i_c in range(corr_matrix.shape[1]):
            val = corr_matrix[i_r, i_c]
            if not np.isnan(val):
                txt_color = 'white' if abs(val) > 0.6 else 'black'
                ax.text(i_c, i_r, f'{val:.2f}', ha='center', va='center',
                        fontsize=6.5, color=txt_color)

    plt.colorbar(im, ax=ax, label='Pearson r', shrink=0.8)
    ax.set_title('Correlation: w vs Metrics (per Config × Function)', fontweight='bold')
    plt.tight_layout()

    path = os.path.join(output_dir, 'w_correlation_heatmap.png')
    plt.savefig(path, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print(f"  > w_correlation_heatmap.png")


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def export_csv(df, output_dir):
    path = os.path.join(output_dir, 'w_relationships_data.csv')
    # Only keep key columns for a manageable size
    cols = ['iter', 'w', 'diversity_ratio', 'DIV', 'progress', 'best_fitness',
            'MH', 'funcion', 'id_experimento']
    df[cols].to_csv(path, index=False)
    print(f"  > w_relationships_data.csv ({len(df):,} rows)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 70)
    print("W-METRIC RELATIONSHIP ANALYSIS")
    print("=" * 70 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Extract data and reconstruct w
    print("[INFO] Extracting iteration data and reconstructing w...")
    df = extract_data_with_w()
    if df is None or df.empty:
        print("[ERROR] No data available. Aborting.")
        return

    mh_names = sorted(df['MH'].unique())
    funciones = sorted(df['funcion'].unique())
    fcs_count = sum(1 for m in mh_names if m.startswith('PSO_FCS'))
    print(f"[INFO] {len(mh_names)} configs ({fcs_count} FCS + baseline) × {len(funciones)} functions")

    # 2. Styles
    colors, mkrs = assign_styles(mh_names)

    # 3. Export CSV
    print("\n[INFO] Exporting data...")
    export_csv(df, OUTPUT_DIR)

    # 4. Plots
    print("\n[INFO] Generating 3-panel per-function plots...")
    plot_w_panels_per_function(df, OUTPUT_DIR, colors, mkrs)

    print("\n[INFO] Generating w trajectory plot...")
    plot_w_trajectory(df, OUTPUT_DIR, colors)

    print("\n[INFO] Generating w vs diversity grid...")
    plot_w_vs_diversity_grid(df, OUTPUT_DIR, colors, mkrs)

    print("\n[INFO] Generating individual w trajectory plots...")
    plot_w_trajectory_individual(df, OUTPUT_DIR, colors)

    print("\n[INFO] Generating individual w vs diversity plots...")
    plot_w_vs_diversity_individual(df, OUTPUT_DIR, colors, mkrs)

    print("\n[INFO] Generating correlation heatmap...")
    plot_correlation_heatmap(df, OUTPUT_DIR)

    print("\n" + "=" * 70)
    print("[OK] W-METRIC RELATIONSHIP ANALYSIS COMPLETED")
    print(f"     Output: {OUTPUT_DIR}/")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
