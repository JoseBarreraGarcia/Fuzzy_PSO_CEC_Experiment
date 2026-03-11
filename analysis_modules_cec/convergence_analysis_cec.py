"""
CONVERGENCE ANALYSIS FOR CEC2017 BENCHMARKS

Generates detailed convergence plots:
- Convergence curves (fitness vs iteration) by function and MH
- Aggregated comparative convergence
- Improvement rate per iteration
- Convergence plot with mean ± std bands

Outputs:
  Resultados/resumen/level2_aggregated_cec/convergence/
    - convergence_by_function.png
    - convergence_overlay_all_functions.png
    - convergence_improvement_rate.png
    - convergence_mean_std_bands.png
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, str(Path(__file__).parent.parent))

# LNCS Format Configuration
plt.rcParams['figure.figsize'] = (7.5, 6)
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 9
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['axes.titlesize'] = 11
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 8
sns.set_style("whitegrid")
DPI_OUTPUT = 300

COLORS_MH = {
    'PSO': '#FF6B6B',
    'PSO_FCS:A': '#4ECDC4',
    'PSO_FCS:B': '#45B7D1',
    'PSO_FCS:C': '#FFA07A',
    'PSO_FCS:D': '#95E1D3'
}

MARKERS_MH = {
    'PSO': 'o',
    'PSO_FCS:A': 's',
    'PSO_FCS:B': '^',
    'PSO_FCS:C': 'D',
    'PSO_FCS:D': 'v'
}


def add_bar_value_labels(ax, bars, fmt='.2f', orientation='h'):
    """Add value labels on bars in a bar plot.
    
    Args:
        ax: matplotlib axis
        bars: bar container from barh() or bar()
        fmt: format string for numbers
        orientation: 'h' for horizontal bars, 'v' for vertical bars
    """
    for bar in bars:
        if orientation == 'h':
            # For horizontal bars (barh)
            width = bar.get_width()
            x_pos = width
            y_pos = bar.get_y() + bar.get_height() / 2.
            ha = 'left'
            va = 'center'
            value_str = f'{width:{fmt}}'
        else:
            # For vertical bars (bar)
            height = bar.get_height()
            x_pos = bar.get_x() + bar.get_width() / 2.
            y_pos = height
            ha = 'center'
            va = 'bottom'
            value_str = f'{height:{fmt}}'
        
        ax.text(x_pos, y_pos, value_str,
                ha=ha, va=va, fontsize=8, fontweight='bold')


def ensure_output_directory():
    """Create output directory for convergence plots."""
    output_dir = 'Resultados/resumen/level2_aggregated_cec/convergence'
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def load_experiment_data():
    """Load experiment data from Level 1."""
    try:
        df = pd.read_csv('Resultados/resumen/level1_raw_cec/ben_experiments_all_runs.csv')
        print(f"[OK] Data loaded: {len(df)} records")
        return df
    except FileNotFoundError:
        print("[ERROR] File ben_experiments_all_runs.csv not found")
        return None


def extract_convergence_by_iteration(df_experiments):
    """
    Extract convergence data by iteration from records.
    
    Assumes df_experiments contains columns like:
    - MH, funcion, iteracion, fitness_best, etc.
    """
    
    if 'iteracion' not in df_experiments.columns:
        print("[WARN] No 'iteracion' column - creating aggregated data by function")
        # If no per-iteration data, create aggregation by function
        return None
    
    # Group by function, MH and iteration
    convergence_data = df_experiments.groupby(['funcion', 'MH', 'iteracion'])['fitness_best'].agg(['mean', 'std', 'count']).reset_index()
    
    return convergence_data


def plot_convergence_by_function(output_dir, df_experiments):
    """
    Individual convergence plot by function.
    """
    
    if df_experiments is None:
        print("[WARN] No experiment data available")
        return
    
    if 'funcion' not in df_experiments.columns:
        print("[WARN] No function information available")
        return
    
    funciones = sorted(df_experiments['funcion'].unique())
    
    print(f"\n[INFO] Generating convergence plots for {len(funciones)} functions...")
    
    for funcion in funciones:
        df_func = df_experiments[df_experiments['funcion'] == funcion]
        
        fig, ax = plt.subplots(figsize=(7.5, 6))
        
        mhs = sorted(df_func['MH'].unique())
        
        for mh in mhs:
            df_mh = df_func[df_func['MH'] == mh]
            
            if 'iteracion' in df_mh.columns:
                convergence_mean = df_mh.groupby('iteracion')['fitness'].mean()
                convergence_std = df_mh.groupby('iteracion')['fitness'].std()
                
                color = COLORS_MH.get(mh, '#999999')
                marker = MARKERS_MH.get(mh, 'o')
                
                ax.plot(convergence_mean.index, convergence_mean.values,
                       label=mh, linewidth=1.5, marker=marker, markersize=3,
                       color=color, alpha=0.8)
                
                ax.fill_between(convergence_mean.index,
                               convergence_mean.values - convergence_std.values,
                               convergence_mean.values + convergence_std.values,
                               color=color, alpha=0.15)
            else:
                # Show average fitness
                fitness_avg = df_mh['fitness'].mean()
                color = COLORS_MH.get(mh, '#999999')
                ax.axhline(y=fitness_avg, label=f'{mh} (avg)', linewidth=1.5, color=color, linestyle='--')
        
        ax.set_xlabel('Iteration', fontsize=10)
        ax.set_ylabel('Best Fitness Found', fontsize=10)
        ax.set_title(f'Convergence CEC2017 - Function {funcion}', fontsize=11, fontweight='bold')
        ax.legend(loc='best', fontsize=8, framealpha=0.95)
        ax.grid(True, alpha=0.4, linestyle='--')
        
        plt.tight_layout()
        filepath = os.path.join(output_dir, f'convergence_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ {funcion}")


def plot_convergence_comparison_all_functions(output_dir, df_experiments):
    """
    Global comparative convergence plot.
    """
    
    if df_experiments is None or 'MH' not in df_experiments.columns:
        print("[WARN] No data for global comparison")
        return
    
    print("\n[INFO] Generating global convergence plot...")
    
    fig, ax = plt.subplots(figsize=(7.5, 6))
    
    mhs = sorted(df_experiments['MH'].unique())
    
    # Group by MH and calculate average fitness
    mh_stats = df_experiments.groupby('MH')['fitness'].agg(['mean', 'std', 'min', 'max', 'count']).reset_index()
    
    bars = []
    for idx, row in mh_stats.iterrows():
        mh = row['MH']
        color = COLORS_MH.get(mh, '#999999')
        bar = ax.bar(idx, row['mean'], yerr=row['std'], capsize=4,
              color=color, alpha=0.7, label=mh, width=0.6)
        bars.append(bar)
    
    add_bar_value_labels(ax, [b[0] for b in bars], fmt='.2e', orientation='v')
    
    ax.set_xticks(range(len(mh_stats)))
    ax.set_xticklabels(mh_stats['MH'])
    ax.set_ylabel('Average Fitness', fontsize=10)
    ax.set_xlabel('Metaheuristic', fontsize=10)
    ax.set_title('Aggregated Convergence: Average across CEC2017', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.4, axis='y', linestyle='--')
    
    plt.tight_layout()
    filepath = os.path.join(output_dir, 'convergence_overlay_all_functions.png')
    plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ convergence_overlay_all_functions.png")


def plot_convergence_with_uncertainty_bands(output_dir, df_experiments):
    """
    Convergence plot with uncertainty bands (mean ± std).
    """
    
    if df_experiments is None or 'MH' not in df_experiments.columns:
        print("[WARN] No data for uncertainty bands")
        return
    
    print("\n[INFO] Generating uncertainty bands plot...")
    
    fig, ax = plt.subplots(figsize=(7.5, 6))
    
    mhs = sorted(df_experiments['MH'].unique())
    
    # Group by MH and show statistics
    mh_stats = df_experiments.groupby('MH')['fitness'].agg(['mean', 'std', 'min', 'max']).reset_index()
    
    for idx, row in mh_stats.iterrows():
        mh = row['MH']
        color = COLORS_MH.get(mh, '#999999')
        marker = MARKERS_MH.get(mh, 'o')
        
        # Bar with ±1σ
        ax.errorbar(idx, row['mean'], yerr=row['std'],
                   fmt=marker, markersize=10, label=mh, color=color, 
                   capsize=4, capthick=1.5, elinewidth=1.5, alpha=0.8)
    
    ax.set_xticks(range(len(mh_stats)))
    ax.set_xticklabels(mh_stats['MH'])
    ax.set_ylabel('Fitness (Mean ± Std. Dev.)', fontsize=10)
    ax.set_xlabel('Metaheuristic', fontsize=10)
    ax.set_title('Convergence with Uncertainty Bands CEC2017', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.4, axis='y', linestyle='--')
    
    plt.tight_layout()
    filepath = os.path.join(output_dir, 'convergence_mean_std_bands.png')
    plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ convergence_mean_std_bands.png")


def plot_convergence_improvement_rate(output_dir, df_experiments):
    """
    Improvement rate plot by MH.
    """
    
    if df_experiments is None or 'MH' not in df_experiments.columns:
        print("[WARN] No data for improvement rate calculation")
        return
    
    print("\n[INFO] Generating improvement rate plot...")
    
    fig, ax = plt.subplots(figsize=(7.5, 6))
    
    mhs = sorted(df_experiments['MH'].unique())
    
    improvement_rates = []
    mh_list = []
    
    for mh in mhs:
        df_mh = df_experiments[df_experiments['MH'] == mh]
        
        # Average improvement = (worst - best) / worst
        max_fit = df_mh['fitness'].max()
        min_fit = df_mh['fitness'].min()
        
        if max_fit != 0:
            improvement = (max_fit - min_fit) / abs(max_fit)
        else:
            improvement = 0
        
        improvement_rates.append(improvement)
        mh_list.append(mh)
    
    # Create barplot
    colors = [COLORS_MH.get(mh, '#999999') for mh in mh_list]
    bars = ax.bar(range(len(mh_list)), improvement_rates, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
    
    add_bar_value_labels(ax, bars, fmt='.3f', orientation='v')
    
    ax.set_xticks(range(len(mh_list)))
    ax.set_xticklabels(mh_list)
    ax.set_ylabel('Improvement Rate', fontsize=10)
    ax.set_xlabel('Metaheuristic', fontsize=10)
    ax.set_title('Improvement Rate by Metaheuristic CEC2017', fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.4, axis='y', linestyle='--')
    
    plt.tight_layout()
    filepath = os.path.join(output_dir, 'convergence_improvement_rate.png')
    plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ convergence_improvement_rate.png")


def main():
    """Execute convergence analysis."""
    
    print("\n" + "=" * 80)
    print("CONVERGENCE ANALYSIS FOR CEC2017 BENCHMARKS")
    print("=" * 80)
    
    output_dir = ensure_output_directory()
    print(f"\n[INFO] Output directory: {output_dir}\n")
    
    # Load data
    df_experiments = load_experiment_data()
    if df_experiments is None:
        print("[ERROR] Could not load data")
        return
    
    # Generate plots
    plot_convergence_by_function(output_dir, df_experiments)
    plot_convergence_comparison_all_functions(output_dir, df_experiments)
    plot_convergence_with_uncertainty_bands(output_dir, df_experiments)
    plot_convergence_improvement_rate(output_dir, df_experiments)
    
    print("\n" + "=" * 80)
    print("[OK] CONVERGENCE ANALYSIS COMPLETED")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
