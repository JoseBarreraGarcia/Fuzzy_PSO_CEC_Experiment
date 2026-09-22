"""
W VERIFICATION: 3D SCATTER PLOTS (w vs diversity vs progress)

For each benchmark function, generates 3D scatter plots showing the
observed inertia weight (w) as a function of diversity ratio and
iteration progress — derived from actual PSO execution data.

Three output types:
  - per_function/: One plot per function, all 12 configs as colored series
  - panels/: 2×3 panel per function × label group (R1-R6 subplots)
  - individual/: One plot per (config × function)

Axes: X = Diversity, Y = Progress, Z = w

Output → Resultados/resumen/w_verification_3d/
"""

import os
import sys
from pathlib import Path
from io import StringIO

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

sys.path.insert(0, str(Path(__file__).parent.parent))

from BD.sqlite import BD
from FUZZY.fuzzy_controller_w_3L import get_fuzzy_controller
from scipy.interpolate import RegularGridInterpolator

# ---------------------------------------------------------------------------
# Style
# ---------------------------------------------------------------------------
plt.rcParams.update({
    'font.family': 'Times New Roman',
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
})
DPI_OUTPUT = 300

OUTPUT_DIR = 'Resultados/resumen/w_verification_3d'

# ---------------------------------------------------------------------------
# MH name parsing
# ---------------------------------------------------------------------------

def parse_mh_name(mh_name):
    """Parse 'PSO_FCS:A:3:I1:R1' → components dict."""
    parts = mh_name.split(':')
    if len(parts) >= 5:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': int(parts[2]), 'input_set': parts[3],
            'rule_set': parts[4],
            'short_label': f"{parts[3]}-{parts[2]}L-{parts[4]}",
        }
    elif len(parts) >= 4:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': int(parts[2]), 'input_set': parts[3],
            'rule_set': None,
            'short_label': f"{parts[3]}-{parts[2]}L",
        }
    elif len(parts) >= 3:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': int(parts[2]), 'input_set': None,
            'rule_set': None,
            'short_label': f"{parts[1]}-{parts[2]}L",
        }
    elif len(parts) == 2:
        return {
            'base': parts[0], 'output_set': parts[1],
            'num_labels': None, 'input_set': None,
            'rule_set': None,
            'short_label': parts[1],
        }
    return {
        'base': mh_name, 'output_set': None,
        'num_labels': None, 'input_set': None,
        'rule_set': None,
        'short_label': mh_name,
    }


# ---------------------------------------------------------------------------
# w reconstruction (lookup-table approach)
# ---------------------------------------------------------------------------
_interp_cache = {}
_LUT_RES = 101


def _build_w_interpolator(w_set, num_labels, input_set, rule_set='R1'):
    key = (w_set, num_labels, input_set, rule_set)
    if key in _interp_cache:
        return _interp_cache[key]

    fcs = get_fuzzy_controller(w_set, num_labels=num_labels,
                               input_set=input_set, rule_set=rule_set)
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
    w_vals = interp(points)
    return w_vals, diversity_ratio, progress


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def extract_fcs_data():
    """Extract iteration data for PSO_FCS configs only, reconstruct w."""

    bd = BD()
    bd.conectar()
    cursor = bd.getCursor()

    cursor.execute("""
        SELECT it.fk_id_experimento, it.archivo, exp.MH, inst.nombre, exp.paramMH
        FROM iteraciones it
        JOIN experimentos exp ON it.fk_id_experimento = exp.id_experimento
        JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
        WHERE inst.tipo_problema = 'BEN'
          AND exp.MH LIKE 'PSO_FCS%%'
    """)

    records = []
    skipped = 0

    rows = cursor.fetchall()
    total = len(rows)
    for idx, (exp_id, blob, mh, funcion, paramMH) in enumerate(rows):
        if (idx + 1) % 200 == 0 or idx == total - 1:
            print(f"\r  Processing {idx+1}/{total} experiments...", end='', flush=True)
        if blob is None:
            skipped += 1
            continue
        try:
            content = blob.decode('utf-8', errors='ignore') if isinstance(blob, bytes) else str(blob)
            df_iter = pd.read_csv(StringIO(content))

            col_map = {}
            for c in df_iter.columns:
                cl = c.strip().lower()
                if cl == 'iter':
                    col_map[c] = 'iter'
                elif cl == 'div':
                    col_map[c] = 'DIV'
            df_iter = df_iter.rename(columns=col_map)

            if 'DIV' not in df_iter.columns:
                skipped += 1
                continue

            max_iter = 500
            if paramMH:
                for token in paramMH.split(','):
                    if token.strip().startswith('iter:'):
                        try:
                            max_iter = int(token.strip().split(':')[1])
                        except (ValueError, IndexError):
                            pass

            w_vals, div_ratio, progress = _compute_w_for_fcs(
                df_iter['DIV'].values, max_iter, mh)

            sub = pd.DataFrame({
                'progress': progress,
                'diversity_ratio': div_ratio,
                'w': w_vals,
                'id_experimento': exp_id,
                'MH': mh,
                'funcion': funcion,
            })
            records.append(sub)
        except Exception:
            skipped += 1
            continue

    bd.desconectar()
    print()

    if not records:
        print("[WARN] No iteration data found")
        return None

    df = pd.concat(records, ignore_index=True)
    print(f"[OK] Extracted {len(df):,} rows from {len(records)} experiments (skipped {skipped})")
    return df


# ---------------------------------------------------------------------------
# Color palette for 12 configs
# ---------------------------------------------------------------------------

_CONFIG_COLORS = [
    '#E63946', '#457B9D', '#2A9D8F', '#E9C46A', '#F4A261', '#264653',
    '#A8DADC', '#6A0572', '#1D3557', '#B5838D', '#606C38', '#BC6C25',
]


# ---------------------------------------------------------------------------
# Plot 1: Individual per-config per-function (72 scatter plots)
# ---------------------------------------------------------------------------

def plot_individual(df, output_dir):
    """One 3D scatter per (config, function) showing observed w."""

    sub_dir = os.path.join(output_dir, 'individual')
    os.makedirs(sub_dir, exist_ok=True)

    mh_list = sorted(df['MH'].unique(), key=lambda x: parse_mh_name(x)['short_label'])
    funciones = sorted(df['funcion'].unique())

    count = 0
    for mh in mh_list:
        info = parse_mh_name(mh)
        label = info['short_label']

        for funcion in funciones:
            df_sub = df[(df['MH'] == mh) & (df['funcion'] == funcion)]
            if df_sub.empty:
                continue

            n_runs = df_sub['id_experimento'].nunique()

            max_pts = 8000
            if len(df_sub) > max_pts:
                df_plot = df_sub.sample(n=max_pts, random_state=42)
            else:
                df_plot = df_sub

            fig = plt.figure(figsize=(9, 7))
            ax = fig.add_subplot(111, projection='3d')

            sc = ax.scatter(
                df_plot['diversity_ratio'].values,
                df_plot['progress'].values,
                df_plot['w'].values,
                c=df_plot['w'].values, cmap='viridis',
                s=4, alpha=0.4, edgecolors='none',
            )

            ax.set_xlabel('Diversity', fontsize=9, labelpad=8)
            ax.set_ylabel('Progress', fontsize=9, labelpad=8)
            ax.set_zlabel('w', fontsize=9, labelpad=8)
            ax.set_title(
                f'{label} — {funcion}  ({n_runs} runs)',
                fontsize=11, fontweight='bold', pad=12,
            )
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.set_zlim(0, 1)
            ax.tick_params(labelsize=8)

            fig.colorbar(sc, ax=ax, shrink=0.55, pad=0.1, label='w')

            filename = f"w_3d_{label}_{funcion}.png"
            filepath = os.path.join(sub_dir, filename)
            plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
            plt.close()
            count += 1

    print(f"  > {count} individual plots in individual/")


# ---------------------------------------------------------------------------
# Plot 2: Per-function summary (all 12 configs as colored scatter series)
# ---------------------------------------------------------------------------

def plot_per_function_all_configs(df, output_dir):
    """One 3D scatter per function, 12 configs as separate colored series."""

    summary_dir = os.path.join(output_dir, 'per_function')
    os.makedirs(summary_dir, exist_ok=True)

    funciones = sorted(df['funcion'].unique())
    mh_list = sorted(df['MH'].unique(), key=lambda x: parse_mh_name(x)['short_label'])
    n_configs = len(mh_list)

    for funcion in funciones:
        df_f = df[df['funcion'] == funcion]
        if df_f.empty:
            continue

        fig = plt.figure(figsize=(12, 9))
        ax = fig.add_subplot(111, projection='3d')

        for ci, mh in enumerate(mh_list):
            info = parse_mh_name(mh)
            label = info['short_label']
            color = _CONFIG_COLORS[ci % len(_CONFIG_COLORS)]

            df_sub = df_f[df_f['MH'] == mh]
            if df_sub.empty:
                continue

            max_pts = 2000
            if len(df_sub) > max_pts:
                df_pts = df_sub.sample(n=max_pts, random_state=42 + ci)
            else:
                df_pts = df_sub

            ax.scatter(
                df_pts['diversity_ratio'].values,
                df_pts['progress'].values,
                df_pts['w'].values,
                c=color, s=5, alpha=0.35, edgecolors='none',
                label=label,
            )

        ax.set_xlabel('Diversity', fontsize=10, labelpad=10)
        ax.set_ylabel('Progress', fontsize=10, labelpad=10)
        ax.set_zlabel('w', fontsize=10, labelpad=10)
        ax.set_title(
            f'Observed w — {funcion}\n({n_configs} configs, all runs)',
            fontsize=12, fontweight='bold', pad=15,
        )
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_zlim(0, 1)
        ax.tick_params(labelsize=8)

        ax.legend(fontsize=7, loc='upper left', framealpha=0.9,
                  markerscale=3, ncol=2)

        filename = f"w_observed_{funcion}.png"
        filepath = os.path.join(summary_dir, filename)
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        print(f"  > per_function/{filename}")


# ---------------------------------------------------------------------------
# Plot 3: Panel 2×3 per function (one scatter subplot per R1-R6)
# ---------------------------------------------------------------------------

def plot_panel_per_function(df, output_dir):
    """For each function and num_labels group, a 2×3 panel of scatter subplots."""

    panel_dir = os.path.join(output_dir, 'panels')
    os.makedirs(panel_dir, exist_ok=True)

    funciones = sorted(df['funcion'].unique())
    mh_list = sorted(df['MH'].unique(), key=lambda x: parse_mh_name(x)['short_label'])

    # Group configs by num_labels
    groups = {}
    for mh in mh_list:
        info = parse_mh_name(mh)
        nl = info['num_labels']
        if nl not in groups:
            groups[nl] = []
        groups[nl].append((mh, info))

    count = 0
    for nl in sorted(groups.keys()):
        configs = groups[nl]
        configs.sort(key=lambda x: x[1].get('rule_set', 'R1'))
        n = len(configs)
        cols = 3
        rows = (n + cols - 1) // cols

        for funcion in funciones:
            fig = plt.figure(figsize=(6 * cols, 5 * rows))
            fig.suptitle(
                f'Observed w: {funcion} ({nl}-Label)',
                fontsize=14, fontweight='bold', y=1.02,
            )

            for idx, (mh, info) in enumerate(configs):
                rs = info.get('rule_set', '?')

                df_sub = df[(df['MH'] == mh) & (df['funcion'] == funcion)]
                n_runs = df_sub['id_experimento'].nunique() if not df_sub.empty else 0

                ax = fig.add_subplot(rows, cols, idx + 1, projection='3d')

                if not df_sub.empty:
                    max_pts = 4000
                    if len(df_sub) > max_pts:
                        df_plot = df_sub.sample(n=max_pts, random_state=42 + idx)
                    else:
                        df_plot = df_sub

                    ax.scatter(
                        df_plot['diversity_ratio'].values,
                        df_plot['progress'].values,
                        df_plot['w'].values,
                        c=df_plot['w'].values, cmap='viridis',
                        s=3, alpha=0.4, edgecolors='none',
                    )

                ax.set_xlabel('Diversity', fontsize=9)
                ax.set_ylabel('Progress', fontsize=9)
                ax.set_zlabel('w', fontsize=9)
                ax.set_title(f'{rs} ({n_runs} runs)', fontsize=12, fontweight='bold')
                ax.set_xlim(0, 1)
                ax.set_ylim(0, 1)
                ax.set_zlim(0, 1)
                ax.tick_params(labelsize=8)

            plt.tight_layout()
            filename = f"w_panel_{nl}L_{funcion}.png"
            filepath = os.path.join(panel_dir, filename)
            plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
            plt.close()
            print(f"  > panels/{filename}")
            count += 1

    print(f"  > {count} panel plots total")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    print("\n" + "=" * 70)
    print("W VERIFICATION: 3D SCATTER PLOTS")
    print("=" * 70 + "\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("[INFO] Extracting iteration data for PSO_FCS configs...")
    df = extract_fcs_data()
    if df is None or df.empty:
        print("[ERROR] No data available. Aborting.")
        return

    mh_names = sorted(df['MH'].unique())
    funciones = sorted(df['funcion'].unique())
    print(f"[INFO] {len(mh_names)} configs × {len(funciones)} functions\n")

    print("[INFO] Generating per-function summary plots (all configs)...")
    plot_per_function_all_configs(df, OUTPUT_DIR)

    print("\n[INFO] Generating panel plots (2×3 per function per label group)...")
    plot_panel_per_function(df, OUTPUT_DIR)

    print(f"\n[INFO] Generating individual plots (config × function)...")
    plot_individual(df, OUTPUT_DIR)

    print(f"\n" + "=" * 70)
    print("[OK] W VERIFICATION COMPLETED")
    print(f"     Output: {OUTPUT_DIR}/")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    main()
