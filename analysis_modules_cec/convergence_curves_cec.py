"""
CONVERGENCE CURVES ANALYSIS FOR BENCHMARK FUNCTIONS

Generates publication-quality convergence and diversity evolution plots
from iteration-level data stored in the database (iteraciones BLOBs).

Fully adaptive: auto-detects MH configurations, input sets, output sets,
granularity levels, and benchmark functions from the data.

Outputs (in Resultados/resumen/level2_aggregated_cec/convergence_curves/):
  - convergence_{function}.png          Fitness vs iteration per function
  - diversity_{function}.png            Diversity vs iteration per function
  - convergence_diversity_panel_{func}  Combined 2-row panel per function
  - convergence_multimodal_summary.png  Side-by-side multimodal comparison
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

# ---------------------------------------------------------------------------
# Plot style (LNCS / IEEE conference format)
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

OUTPUT_DIR = 'Resultados/resumen/level2_aggregated_cec/convergence_curves'


# ---------------------------------------------------------------------------
# MH name parsing utilities
# ---------------------------------------------------------------------------

def parse_mh_name(mh_name):
    """Parse an MH name like 'PSO_FCS:A:3:I1' into components.

    Returns dict with keys: base, output_set, num_labels, input_set, short_label.
    For 'PSO' (baseline), most fields are None.
    """
    parts = mh_name.split(':')
    if len(parts) >= 4:
        return {
            'base': parts[0],
            'output_set': parts[1],
            'num_labels': int(parts[2]),
            'input_set': parts[3],
            'short_label': f"{parts[3]}-{parts[2]}L",
        }
    elif len(parts) >= 3:
        return {
            'base': parts[0],
            'output_set': parts[1],
            'num_labels': int(parts[2]),
            'input_set': None,
            'short_label': f"{parts[1]}-{parts[2]}L",
        }
    elif len(parts) == 2:
        return {
            'base': parts[0],
            'output_set': parts[1],
            'num_labels': None,
            'input_set': None,
            'short_label': parts[1],
        }
    else:
        return {
            'base': mh_name,
            'output_set': None,
            'num_labels': None,
            'input_set': None,
            'short_label': mh_name,
        }


def build_display_name(mh_name):
    """Build a short, readable display name for legends."""
    info = parse_mh_name(mh_name)
    if info['base'] == 'PSO' and info['output_set'] is None:
        return 'PSO (baseline)'
    return info['short_label']


# ---------------------------------------------------------------------------
# Dynamic color / marker assignment
# ---------------------------------------------------------------------------

# Base palette: visually distinguishable, colorblind-friendly
_BASE_COLORS = [
    '#E63946',   # red (baseline PSO)
    '#457B9D',   # steel blue
    '#2A9D8F',   # teal
    '#E9C46A',   # gold
    '#F4A261',   # orange
    '#264653',   # dark teal
    '#A8DADC',   # light blue
    '#6A0572',   # purple
    '#1D3557',   # navy
    '#B5838D',   # mauve
    '#606C38',   # olive
    '#BC6C25',   # sienna
]

_MARKERS = ['o', 's', '^', 'D', 'v', 'P', 'X', 'p', 'h', '*', '<', '>']


def assign_styles(mh_names):
    """Return dicts mapping MH name -> color and MH name -> marker.

    PSO baseline always gets the first color and 'o' marker.
    FCS variants are sorted by short_label for consistent ordering.
    """
    baseline = [m for m in mh_names if not m.startswith('PSO_FCS')]
    fcs = sorted([m for m in mh_names if m.startswith('PSO_FCS')],
                 key=lambda x: build_display_name(x))
    ordered = baseline + fcs

    colors = {}
    markers = {}
    for i, mh in enumerate(ordered):
        colors[mh] = _BASE_COLORS[i % len(_BASE_COLORS)]
        markers[mh] = _MARKERS[i % len(_MARKERS)]
    return colors, markers


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def extract_iteration_data():
    """Read all iteration BLOBs from the database.

    Returns a DataFrame with columns:
        iter, best_fitness, DIV, id_experimento, MH, funcion
    """
    bd = BD()
    bd.conectar()
    cursor = bd.getCursor()

    # Get all BLOBs joined with experiment info
    cursor.execute("""
        SELECT it.fk_id_experimento, it.archivo, exp.MH, inst.nombre
        FROM iteraciones it
        JOIN experimentos exp ON it.fk_id_experimento = exp.id_experimento
        JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
        WHERE inst.tipo_problema = 'BEN'
    """)

    records = []
    for exp_id, blob, mh, funcion in cursor.fetchall():
        if blob is None:
            continue
        try:
            content = blob.decode('utf-8', errors='ignore') if isinstance(blob, bytes) else str(blob)
            df_iter = pd.read_csv(StringIO(content))

            # Normalize column names (handle possible variations)
            col_map = {}
            for c in df_iter.columns:
                cl = c.strip().lower()
                if cl == 'iter':
                    col_map[c] = 'iter'
                elif cl in ('best_fitness', 'fitness'):
                    col_map[c] = 'best_fitness'
                elif cl == 'div':
                    col_map[c] = 'DIV'
                elif cl == 'diversity':
                    col_map[c] = 'DIV'
            df_iter = df_iter.rename(columns=col_map)

            keep = [c for c in ['iter', 'best_fitness', 'DIV'] if c in df_iter.columns]
            if 'best_fitness' not in keep:
                continue

            df_sub = df_iter[keep].copy()
            df_sub['id_experimento'] = exp_id
            df_sub['MH'] = mh
            df_sub['funcion'] = funcion
            records.append(df_sub)
        except Exception:
            continue

    bd.desconectar()

    if not records:
        print("[WARN] No iteration data found in database")
        return None

    df = pd.concat(records, ignore_index=True)
    print(f"[OK] Extracted {len(df):,} iteration rows from {len(records)} experiments")
    return df


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def aggregate_by_iter(df, value_col='best_fitness'):
    """Group by (MH, funcion, iter) and compute mean/std of value_col."""
    grouped = df.groupby(['MH', 'funcion', 'iter'])[value_col].agg(['mean', 'std']).reset_index()
    grouped.columns = ['MH', 'funcion', 'iter', f'{value_col}_mean', f'{value_col}_std']
    return grouped


# ---------------------------------------------------------------------------
# Plot functions
# ---------------------------------------------------------------------------

def _subsample_iterations(iters, max_points=100):
    """Return indices to plot so that lines are not overloaded with markers."""
    if len(iters) <= max_points:
        return np.arange(len(iters))
    return np.linspace(0, len(iters) - 1, max_points, dtype=int)


def plot_convergence_per_function(df_agg, output_dir, colors, markers):
    """One fitness-vs-iteration plot per benchmark function."""
    funciones = sorted(df_agg['funcion'].unique())
    mh_list = sorted(df_agg['MH'].unique(), key=lambda x: build_display_name(x))

    for funcion in funciones:
        df_f = df_agg[df_agg['funcion'] == funcion]
        fig, ax = plt.subplots(figsize=(7.5, 4.5))

        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh].sort_values('iter')
            if df_m.empty:
                continue
            iters = df_m['iter'].values
            means = df_m['best_fitness_mean'].values
            stds = df_m['best_fitness_std'].values

            label = build_display_name(mh)
            color = colors.get(mh, '#999999')
            marker = markers.get(mh, 'o')

            # Line (full), markers (subsampled)
            ax.plot(iters, means, color=color, linewidth=1.3, label=label, zorder=3)
            idx = _subsample_iterations(iters, max_points=15)
            ax.plot(iters[idx], means[idx], marker=marker, color=color,
                    linestyle='none', markersize=4, zorder=4)
            ax.fill_between(iters, means - stds, means + stds,
                            color=color, alpha=0.10)

        ax.set_xlabel('Iteration')
        ax.set_ylabel('Best Fitness')
        ax.set_title(f'Convergence — {funcion}', fontweight='bold')
        ax.legend(loc='best', framealpha=0.9, ncol=2 if len(mh_list) > 5 else 1)
        ax.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()

        filepath = os.path.join(output_dir, f'convergence_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        print(f"  > convergence_{funcion}.png")


def plot_diversity_per_function(df_agg, output_dir, colors, markers):
    """One diversity-vs-iteration plot per benchmark function."""
    if 'DIV_mean' not in df_agg.columns:
        print("[WARN] No diversity data — skipping diversity plots")
        return

    funciones = sorted(df_agg['funcion'].unique())
    mh_list = sorted(df_agg['MH'].unique(), key=lambda x: build_display_name(x))

    for funcion in funciones:
        df_f = df_agg[df_agg['funcion'] == funcion]
        fig, ax = plt.subplots(figsize=(7.5, 4.5))

        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh].sort_values('iter')
            if df_m.empty:
                continue
            iters = df_m['iter'].values
            means = df_m['DIV_mean'].values
            stds = df_m['DIV_std'].values

            label = build_display_name(mh)
            color = colors.get(mh, '#999999')
            marker = markers.get(mh, 'o')

            ax.plot(iters, means, color=color, linewidth=1.3, label=label, zorder=3)
            idx = _subsample_iterations(iters, max_points=15)
            ax.plot(iters[idx], means[idx], marker=marker, color=color,
                    linestyle='none', markersize=4, zorder=4)
            ax.fill_between(iters, means - stds, means + stds,
                            color=color, alpha=0.10)

        ax.set_xlabel('Iteration')
        ax.set_ylabel('Population Diversity')
        ax.set_title(f'Diversity Evolution — {funcion}', fontweight='bold')
        ax.legend(loc='best', framealpha=0.9, ncol=2 if len(mh_list) > 5 else 1)
        ax.grid(True, alpha=0.3, linestyle='--')
        plt.tight_layout()

        filepath = os.path.join(output_dir, f'diversity_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        print(f"  > diversity_{funcion}.png")


def plot_combined_panels(df_fit, df_div, output_dir, colors, markers):
    """Two-row panel (fitness + diversity) per function."""
    has_div = df_div is not None and 'DIV_mean' in df_div.columns

    funciones = sorted(df_fit['funcion'].unique())
    mh_list = sorted(df_fit['MH'].unique(), key=lambda x: build_display_name(x))

    for funcion in funciones:
        nrows = 2 if has_div else 1
        fig, axes = plt.subplots(nrows, 1, figsize=(7.5, 3.5 * nrows), sharex=True)
        if nrows == 1:
            axes = [axes]

        # --- top: fitness ---
        ax = axes[0]
        df_ff = df_fit[df_fit['funcion'] == funcion]
        for mh in mh_list:
            df_m = df_ff[df_ff['MH'] == mh].sort_values('iter')
            if df_m.empty:
                continue
            it = df_m['iter'].values
            mu = df_m['best_fitness_mean'].values
            sd = df_m['best_fitness_std'].values
            label = build_display_name(mh)
            c = colors.get(mh, '#999')
            mk = markers.get(mh, 'o')
            ax.plot(it, mu, color=c, linewidth=1.2, label=label)
            idx = _subsample_iterations(it, 12)
            ax.plot(it[idx], mu[idx], marker=mk, color=c, linestyle='none', markersize=3.5)
            ax.fill_between(it, mu - sd, mu + sd, color=c, alpha=0.08)
        ax.set_ylabel('Best Fitness')
        ax.set_title(f'{funcion} — Convergence & Diversity', fontweight='bold')
        ax.legend(loc='best', framealpha=0.9, ncol=2 if len(mh_list) > 5 else 1)
        ax.grid(True, alpha=0.3, linestyle='--')

        # --- bottom: diversity ---
        if has_div:
            ax2 = axes[1]
            df_fd = df_div[df_div['funcion'] == funcion]
            for mh in mh_list:
                df_m = df_fd[df_fd['MH'] == mh].sort_values('iter')
                if df_m.empty:
                    continue
                it = df_m['iter'].values
                mu = df_m['DIV_mean'].values
                sd = df_m['DIV_std'].values
                c = colors.get(mh, '#999')
                mk = markers.get(mh, 'o')
                ax2.plot(it, mu, color=c, linewidth=1.2)
                idx = _subsample_iterations(it, 12)
                ax2.plot(it[idx], mu[idx], marker=mk, color=c, linestyle='none', markersize=3.5)
                ax2.fill_between(it, mu - sd, mu + sd, color=c, alpha=0.08)
            ax2.set_xlabel('Iteration')
            ax2.set_ylabel('Population Diversity')
            ax2.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()
        filepath = os.path.join(output_dir, f'convergence_diversity_panel_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        print(f"  > convergence_diversity_panel_{funcion}.png")


def plot_multimodal_summary(df_fit, output_dir, colors, markers):
    """Side-by-side convergence for multimodal functions only.

    Auto-detects multimodal functions as those where at least one
    PSO_FCS variant has a better mean fitness than baseline PSO.
    """
    funciones = sorted(df_fit['funcion'].unique())
    mh_list = sorted(df_fit['MH'].unique(), key=lambda x: build_display_name(x))

    # Identify multimodal: functions where any FCS beats PSO mean at last iteration
    multimodal = []
    for funcion in funciones:
        df_f = df_fit[df_fit['funcion'] == funcion]
        last_iter = df_f['iter'].max()
        df_last = df_f[df_f['iter'] == last_iter]

        pso_row = df_last[df_last['MH'] == 'PSO']
        fcs_rows = df_last[df_last['MH'].str.startswith('PSO_FCS')]
        if pso_row.empty or fcs_rows.empty:
            continue

        pso_mean = pso_row['best_fitness_mean'].values[0]
        # For minimization: FCS better means smaller value
        # For maximization (negative optima): FCS better means more negative (also smaller)
        # Both cases: best = min
        fcs_best = fcs_rows['best_fitness_mean'].min()
        if fcs_best < pso_mean:
            multimodal.append(funcion)

    if not multimodal:
        # Fallback: just pick the last N/2 functions alphabetically
        multimodal = funciones[len(funciones) // 2:]

    n = len(multimodal)
    if n == 0:
        return

    fig, axes = plt.subplots(1, n, figsize=(4.0 * n, 4.5), sharey=False)
    if n == 1:
        axes = [axes]

    for ax, funcion in zip(axes, multimodal):
        df_f = df_fit[df_fit['funcion'] == funcion]
        for mh in mh_list:
            df_m = df_f[df_f['MH'] == mh].sort_values('iter')
            if df_m.empty:
                continue
            it = df_m['iter'].values
            mu = df_m['best_fitness_mean'].values
            sd = df_m['best_fitness_std'].values
            label = build_display_name(mh)
            c = colors.get(mh, '#999')
            mk = markers.get(mh, 'o')
            ax.plot(it, mu, color=c, linewidth=1.2, label=label)
            idx = _subsample_iterations(it, 10)
            ax.plot(it[idx], mu[idx], marker=mk, color=c, linestyle='none', markersize=3)
            ax.fill_between(it, mu - sd, mu + sd, color=c, alpha=0.08)
        ax.set_xlabel('Iteration')
        ax.set_ylabel('Best Fitness')
        ax.set_title(funcion, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--')

    # Shared legend below
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', ncol=min(5, len(labels)),
               framealpha=0.9, bbox_to_anchor=(0.5, -0.02))
    plt.tight_layout(rect=[0, 0.06, 1, 1])

    filepath = os.path.join(output_dir, 'convergence_multimodal_summary.png')
    plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    print(f"  > convergence_multimodal_summary.png")


# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def export_aggregated_csv(df_fit, df_div, output_dir):
    """Save the aggregated iteration data as CSV for external use."""
    csv_path = os.path.join(output_dir, 'convergence_aggregated.csv')
    df_fit.to_csv(csv_path, index=False)
    print(f"  > convergence_aggregated.csv ({len(df_fit):,} rows)")

    if df_div is not None and not df_div.empty:
        csv_path = os.path.join(output_dir, 'diversity_aggregated.csv')
        df_div.to_csv(csv_path, index=False)
        print(f"  > diversity_aggregated.csv ({len(df_div):,} rows)")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Execute convergence curves analysis pipeline."""
    print("\n" + "=" * 70)
    print("CONVERGENCE CURVES ANALYSIS")
    print("=" * 70 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Extract data from database
    print("[INFO] Extracting iteration data from database...")
    df = extract_iteration_data()
    if df is None or df.empty:
        print("[ERROR] No iteration data available. Aborting.")
        return

    mh_names = sorted(df['MH'].unique())
    funciones = sorted(df['funcion'].unique())
    print(f"[INFO] Found {len(mh_names)} MH configs × {len(funciones)} functions")
    for mh in mh_names:
        print(f"       - {mh}  →  {build_display_name(mh)}")

    # 2. Assign visual styles
    colors, markers_dict = assign_styles(mh_names)

    # 3. Aggregate
    print("\n[INFO] Aggregating fitness convergence...")
    df_fit = aggregate_by_iter(df, 'best_fitness')

    df_div = None
    if 'DIV' in df.columns:
        print("[INFO] Aggregating diversity evolution...")
        df_div = aggregate_by_iter(df, 'DIV')

    # 4. Export CSVs
    print("\n[INFO] Exporting aggregated CSVs...")
    export_aggregated_csv(df_fit, df_div, OUTPUT_DIR)

    # 5. Generate plots
    print("\n[INFO] Generating convergence plots...")
    plot_convergence_per_function(df_fit, OUTPUT_DIR, colors, markers_dict)

    if df_div is not None:
        print("\n[INFO] Generating diversity plots...")
        plot_diversity_per_function(df_div, OUTPUT_DIR, colors, markers_dict)

    print("\n[INFO] Generating combined panels...")
    plot_combined_panels(df_fit, df_div, OUTPUT_DIR, colors, markers_dict)

    print("\n[INFO] Generating multimodal summary...")
    plot_multimodal_summary(df_fit, OUTPUT_DIR, colors, markers_dict)

    print("\n" + "=" * 70)
    print("[OK] CONVERGENCE CURVES ANALYSIS COMPLETED")
    print(f"     Output: {OUTPUT_DIR}/")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
