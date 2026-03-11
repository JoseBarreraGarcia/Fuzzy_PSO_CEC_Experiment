"""
Fuzzy sets comparison analysis module

Compares different fuzzy sets (A, B, C) for PSO_FCS variants
Generates LNCS-formatted plots for conference publications
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import os


def setup_lncs_style():
    """Configure matplotlib for LNCS format (Times New Roman, 10pt)"""
    mpl.rcParams['font.family'] = 'serif'
    mpl.rcParams['font.serif'] = ['Times New Roman']
    mpl.rcParams['font.size'] = 10
    mpl.rcParams['axes.labelsize'] = 10
    mpl.rcParams['axes.titlesize'] = 10
    mpl.rcParams['xtick.labelsize'] = 9
    mpl.rcParams['ytick.labelsize'] = 9
    mpl.rcParams['legend.fontsize'] = 9
    mpl.rcParams['figure.titlesize'] = 11
    mpl.rcParams['lines.linewidth'] = 1.5
    mpl.rcParams['lines.markersize'] = 4


def load_w_timeseries():
    """Load and concatenate all w_timeseries CSVs from database analysis"""
    import glob
    csv_files = glob.glob('Resultados/resumen/SCP/w_timeseries_SCP_*.csv')
    if not csv_files:
        raise FileNotFoundError("No w_timeseries_SCP_*.csv files found in Resultados/resumen/SCP/")
    df_list = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(df_list, ignore_index=True)
    return df


def analyze_comparison(verbose=False):
    """Run fuzzy sets comparison analysis.

    If `verbose` is False, minimal terminal output is shown and a CSV
    summary is written to Resultados/resumen/SCP/comparison_summary.csv.
    """
    setup_lncs_style()

    VERBOSE = bool(verbose)
    if VERBOSE:
        print("[*] Loading w_timeseries data...")

    df = load_w_timeseries()
    
    mhs = sorted(df['MH'].unique())
    # Incluir todas las MH presentes, no solo PSO_FCS
    if VERBOSE:
        print(f"[*] Metaheuristics found: {mhs}")
        print(f"[*] Total rows: {len(df)}")
    
    # Create figure with 2x2 layout (max 12.4cm width for single column)
    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    
    # Extract color mapping (PSO_FCS:A -> blue, PSO_FCS:B -> orange, PSO_FCS:C -> green)
    color_map = {
        'PSO_FCS:A': '#0173B2',  # blue
        'PSO_FCS:B': '#DE8F05',  # orange
        'PSO_FCS:C': '#CC78BC',  # purple
    }
    
    # Plot 1: Inertia weight evolution comparison (top-left)
    ax = axes[0, 0]
    for mh in mhs:
        if 'PSO_FCS' in mh:
            mh_data = df[df['MH'] == mh].copy()
            if len(mh_data) > 0:
                w_per_iter = mh_data.groupby('iter')['w'].agg(['mean', 'std', 'count'])
                w_per_iter = w_per_iter[w_per_iter['count'] > 0]
                
                color = color_map.get(mh, 'gray')
                ax.plot(w_per_iter.index, w_per_iter['mean'], 
                       label=mh, marker='o', markersize=3, linewidth=1.5, color=color)
                ax.fill_between(w_per_iter.index, 
                               w_per_iter['mean'] - w_per_iter['std'],
                               w_per_iter['mean'] + w_per_iter['std'],
                               alpha=0.15, color=color)
    
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Inertia Weight')
    ax.set_title('Inertia Weight Evolution')
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    # Plot 2: Diversity evolution (top-right)
    ax = axes[0, 1]
    for mh in mhs:
        if 'PSO_FCS' in mh:
            mh_data = df[df['MH'] == mh].copy()
            if len(mh_data) > 0:
                div_per_iter = mh_data.groupby('iter')['div'].mean()
                color = color_map.get(mh, 'gray')
                ax.plot(div_per_iter.index, div_per_iter.values, 
                       label=mh, marker='s', markersize=3, linewidth=1.5, color=color)
    
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Population Diversity')
    ax.set_title('Diversity Evolution')
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.set_xlim(left=0)
    
    # Plot 3: w vs Diversity scatter (bottom-left)
    ax = axes[1, 0]
    for mh in mhs:
        if 'PSO_FCS' in mh:
            mh_data = df[df['MH'] == mh].copy()
            if len(mh_data) > 0:
                clean_data = mh_data[~mh_data['w'].isna()]
                color = color_map.get(mh, 'gray')
                ax.scatter(clean_data['div'], clean_data['w'], 
                          alpha=0.4, s=15, label=mh, color=color)
    
    ax.set_xlabel('Diversity')
    ax.set_ylabel('Inertia Weight')
    ax.set_title('Weight vs Diversity')
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Plot 4: Progress vs w (bottom-right)
    ax = axes[1, 1]
    for mh in mhs:
        if 'PSO_FCS' in mh:
            mh_data = df[df['MH'] == mh].copy()
            if len(mh_data) > 0:
                clean_data = mh_data[~mh_data['w'].isna()]
                color = color_map.get(mh, 'gray')
                ax.scatter(clean_data['progress'], clean_data['w'], 
                          alpha=0.4, s=15, label=mh, color=color)
    
    ax.set_xlabel('Progress')
    ax.set_ylabel('Inertia Weight')
    ax.set_title('Weight vs Progress')
    ax.legend(loc='best', framealpha=0.9)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Adjust layout for LNCS compliance (max 12.4cm width)
    plt.tight_layout()
    
    # Save figure
    output_path = 'Resultados/resumen/SCP/comparison_fuzzy_sets_LNCS.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
    if VERBOSE:
        print(f"[OK] Comparison plot saved: {output_path}")

    # Write summary statistics to CSV (always write)
    save_comparison_summary_csv(df, mhs)

    # Optionally print summary to terminal
    if VERBOSE:
        print_comparison_summary(df, mhs)

    plt.close()


def print_comparison_summary(df, mhs):
    """Print statistical summary for all fuzzy sets"""
    print("\n" + "=" * 80)
    print("FUZZY SETS COMPARISON - SUMMARY STATISTICS".center(80))
    print("=" * 80)
    
    for mh in mhs:
        if 'PSO_FCS' in mh:
            mh_data = df[df['MH'] == mh].copy()
            if len(mh_data) > 0:
                clean_w = mh_data[~mh_data['w'].isna()]['w']
                
                print(f"\n{mh}:")
                print(f"  Inertia Weight - Mean: {clean_w.mean():.6f}")
                print(f"  Inertia Weight - Std:  {clean_w.std():.6f}")
                print(f"  Inertia Weight - Min:  {clean_w.min():.6f}")
                print(f"  Inertia Weight - Max:  {clean_w.max():.6f}")
                print(f"  Diversity - Mean:      {mh_data['div'].mean():.6f}")
                print(f"  Diversity - Std:       {mh_data['div'].std():.6f}")
    
    print("\n" + "=" * 80)


def save_comparison_summary_csv(df, mhs):
    """Save the summary statistics to a CSV file for later review."""
    out_dir = os.path.join('Resultados', 'resumen', 'SCP')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'comparison_summary_SCP.csv')
    rows = []
    for mh in mhs:
        if 'PSO_FCS' in mh:
            mh_data = df[df['MH'] == mh].copy()
            if len(mh_data) > 0:
                clean_w = mh_data[~mh_data['w'].isna()]['w']
                rows.append({
                    'MH': mh,
                    'w_mean': clean_w.mean(),
                    'w_std': clean_w.std(),
                    'w_min': clean_w.min(),
                    'w_max': clean_w.max(),
                    'div_mean': mh_data['div'].mean(),
                    'div_std': mh_data['div'].std(),
                })
    if rows:
        pd.DataFrame(rows).to_csv(out_path, index=False)
        if os.path.exists(out_path):
            print(f"[OK] Comparison summary CSV written: {out_path}")


def analyze_w_evolution(verbose=False):
    """
    Analiza la evolución de w a través de iteraciones para cada fuzzy set.
    Genera un CSV con estadísticas agregadas: media, std, min, max por iteración.
    
    Output: Resultados/resumen/w_evolution_analysis.csv
    
    Columnas: instancia, binarizacion, MH, iter, w_mean, w_std, w_min, w_max, w_count
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from analysis_modules.level1_raw_data import extract_experiments_data
    
    # Leer datos
    df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
    df_exp = extract_experiments_data(verbose=False)
    
    df_merged = df_iter.merge(
        df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
        on='id_experimento'
    )
    
    # Filtrar solo PSO_FCS
    fcs_mhs = ['PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']
    df_fcs = df_merged[df_merged['MH'].isin(fcs_mhs)]
    
    # Agrupar por instancia, binarización, MH e iteración
    grouped = df_fcs.groupby(['experimento', 'binarizacion', 'MH', 'iter']).agg({
        'w': ['mean', 'std', 'min', 'max', 'count']
    }).reset_index()
    
    # Flatten column names
    grouped.columns = ['instancia', 'binarizacion', 'MH', 'iter', 'w_mean', 'w_std', 'w_min', 'w_max', 'w_count']
    
    # Crear directorio de salida
    output_dir = 'Resultados/resumen'
    os.makedirs(output_dir, exist_ok=True)
    
    # Guardar CSV
    csv_path = os.path.join(output_dir, 'w_evolution_analysis.csv')
    grouped.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] W evolution analysis saved: {csv_path}")
        print(f"[INFO] Total rows: {len(grouped)}")
        print(f"[INFO] Instancias: {sorted(grouped['instancia'].unique())}")
        print(f"[INFO] Binarizaciones: {sorted(grouped['binarizacion'].unique())}")
        print(f"[INFO] Fuzzy sets: {sorted(grouped['MH'].unique())}")
    
    return grouped


if __name__ == '__main__':
    # analyze_comparison()  # Comentado: requiere w_timeseries_SCP_*.csv
    
    print("\n[1/2] Generating w evolution CSV...")
    analyze_w_evolution(verbose=True)
    
    print("\n[2/2] Generating w evolution visualizations...")
    try:
        from w_evolution_visualizer import main as visualize_w_evolution
        visualize_w_evolution(verbose=True)
        print("[OK] Complete analysis finished successfully!")
    except ImportError:
        print("[WARN] w_evolution_visualizer module not found - skipping visualizations")
        print("      Run: python analysis_modules/w_evolution_visualizer.py separately")
