"""
DIVERSITY ANALYSIS FOR CEC2017 BENCHMARKS

Generates detailed population diversity plots:
- Diversity evolution by function and MH
- Aggregated comparative diversity
- Correlation between diversity and fitness
- Diversity distribution (boxplots)
- Analysis of final vs initial diversity

Outputs:
  Resultados/resumen/level2_aggregated_cec/diversity/
    - diversity_evolution_by_function.png
    - diversity_overlay_all_functions.png
    - diversity_vs_fitness_scatter.png
    - diversity_distribution_boxplot.png
    - diversity_timeline_all_mh.png
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

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
    """Create output directory for diversity plots."""
    output_dir = 'Resultados/resumen/level2_aggregated_cec/diversity'
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def load_experiment_data():
    """Load experiment data from Level 1."""
    try:
        df = pd.read_csv('Resultados/resumen/level1_raw_cec/ben_experiments_all_runs.csv')
        print(f"[OK] Data loaded: {len(df)} records")
        
        # Show available columns
        print(f"[INFO] Available columns: {list(df.columns)}")
        
        return df
    except FileNotFoundError:
        print("[ERROR] File ben_experiments_all_runs.csv not found")
        return None


def load_real_diversity_data():
    """
    Load real per-iteration diversity data from Level 1 CSV.
    Returns DataFrame with columns: iter, diversity, MH, funcion, etc.
    Returns None if the file does not exist.
    """
    path = 'Resultados/resumen/level1_raw_cec/ben_diversity_metrics.csv'
    if os.path.exists(path):
        df = pd.read_csv(path)
        if 'diversity' in df.columns and 'iter' in df.columns:
            print(f"[OK] Real diversity data loaded: {len(df)} rows")
            return df
    
    # Fallback: try the convergence_curves aggregated CSV
    path2 = 'Resultados/resumen/level2_aggregated_cec/convergence_curves/diversity_aggregated.csv'
    if os.path.exists(path2):
        df = pd.read_csv(path2)
        if 'DIV_mean' in df.columns:
            print(f"[OK] Aggregated diversity data loaded: {len(df)} rows")
            # Reshape to match expected format
            df = df.rename(columns={'DIV_mean': 'diversity'})
            return df
    
    return None


def extract_or_generate_diversity_data(df_experiments):
    """
    Try to load real per-iteration diversity from Level 1.
    Falls back to coefficient of variation as diversity proxy.
    """
    
    real_div = load_real_diversity_data()
    if real_div is not None:
        # Rename 'iter' to 'iteracion' for compatibility with plot functions
        if 'iter' in real_div.columns and 'iteracion' not in real_div.columns:
            real_div = real_div.rename(columns={'iter': 'iteracion'})
        return real_div
    
    print("[WARN] No real diversity data found. Using fitness CV as proxy.")
    
    # Fallback: coefficient of variation (absolute value to handle negative means)
    if 'fitness' in df_experiments.columns:
        df_experiments['diversity'] = df_experiments.groupby(['MH', 'funcion'])['fitness'].transform(
            lambda x: abs(x.std() / (x.mean() + 1e-10)) if x.mean() != 0 else 0
        )
    
    # Add pseudo-iteration based on row order
    df_experiments['iteracion'] = df_experiments.groupby(['MH', 'funcion']).cumcount() + 1
    
    return df_experiments


def plot_diversity_evolution_by_function(output_dir, df_experiments):
    """
    Diversity evolution plot by function (using simulated iteration).
    """
    
    if df_experiments is None:
        print("[WARN] No experiment data available")
        return
    
    if 'funcion' not in df_experiments.columns:
        print("[WARN] No function information available")
        return
    
    funciones = sorted(df_experiments['funcion'].unique())
    
    print(f"\n[INFO] Generating diversity plots for {len(funciones)} functions...")
    
    for funcion in funciones:
        df_func = df_experiments[df_experiments['funcion'] == funcion]
        
        fig, ax = plt.subplots(figsize=(7.5, 6))
        
        mhs = sorted(df_func['MH'].unique())
        
        for mh in mhs:
            df_mh = df_func[df_func['MH'] == mh]
            
            if 'iteracion' in df_mh.columns and 'diversity' in df_mh.columns:
                diversity_by_iter = df_mh.groupby('iteracion')['diversity'].agg(['mean', 'std']).reset_index()
                
                color = COLORS_MH.get(mh, '#999999')
                marker = MARKERS_MH.get(mh, 'o')
                
                ax.plot(diversity_by_iter['iteracion'], diversity_by_iter['mean'],
                       label=mh, linewidth=1.5, marker=marker, markersize=3,
                       color=color, alpha=0.8)
                
                ax.fill_between(diversity_by_iter['iteracion'],
                               diversity_by_iter['mean'] - diversity_by_iter['std'],
                               diversity_by_iter['mean'] + diversity_by_iter['std'],
                               color=color, alpha=0.15)
            else:
                # Show aggregated diversity
                diversity_avg = df_mh['diversity'].mean() if 'diversity' in df_mh.columns else 0
                if diversity_avg > 0:
                    color = COLORS_MH.get(mh, '#999999')
                    ax.axhline(y=diversity_avg, label=mh, linewidth=1.5, color=color, linestyle='--', alpha=0.8)
        
        ax.set_xlabel('Iteration', fontsize=10)
        ax.set_ylabel('Population Diversity', fontsize=10)
        ax.set_title(f'Diversity CEC2017 - Function {funcion}', fontsize=11, fontweight='bold')
        ax.legend(loc='best', fontsize=8, framealpha=0.95)
        ax.grid(True, alpha=0.4, linestyle='--')
        plt.tight_layout()
        filepath = os.path.join(output_dir, f'diversity_evolution_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ {funcion}")


def plot_diversity_overlay_all_functions(output_dir, df_experiments):
    """
    Comparative plot: aggregated diversity evolution across all functions.
    """
    
    if df_experiments is None or 'MH' not in df_experiments.columns:
        print("[WARN] No data for global diversity comparison")
        return
    
    print("\n[INFO] Generating global diversity plot...")
    
    fig, ax = plt.subplots(figsize=(7.5, 6))
    
    mhs = sorted(df_experiments['MH'].unique())
    
    # If data by iteration, show evolution
    if 'iteracion' in df_experiments.columns and 'diversity' in df_experiments.columns:
        for mh in mhs:
            df_mh = df_experiments[df_experiments['MH'] == mh]
            
            # Global diversity (average of all functions)
            diversity_global = df_mh.groupby('iteracion')['diversity'].mean()
            
            color = COLORS_MH.get(mh, '#999999')
            marker = MARKERS_MH.get(mh, 'o')
            
            ax.plot(diversity_global.index, diversity_global.values,
                   label=mh, linewidth=1.5, marker=marker, markersize=4,
                   color=color, alpha=0.85)
        
        ax.set_xlabel('Iteration', fontsize=10)
    else:
        # If no iterations, show average diversity by MH
        if 'diversity' in df_experiments.columns:
            diversity_by_mh = df_experiments.groupby('MH')['diversity'].agg(['mean', 'std']).reset_index()
            
            bars = []
            for idx, row in diversity_by_mh.iterrows():
                mh = row['MH']
                color = COLORS_MH.get(mh, '#999999')
                bar = ax.bar(idx, row['mean'], yerr=row['std'], capsize=4,
                      color=color, alpha=0.7, label=mh, width=0.6)
                bars.append(bar)
            
            add_bar_value_labels(ax, [b[0] for b in bars], fmt='.3f', orientation='v')
            
            ax.set_xticks(range(len(diversity_by_mh)))
            ax.set_xticklabels(diversity_by_mh['MH'])
            ax.set_ylabel('Average Diversity', fontsize=10)
    
    ax.set_ylabel('Population Diversity (average)', fontsize=10)
    ax.set_title('Aggregated Diversity Evolution: Average across CEC2017', 
                fontsize=11, fontweight='bold')
    ax.legend(loc='best', fontsize=8, framealpha=0.95)
    ax.grid(True, alpha=0.4, linestyle='--')
    
    plt.tight_layout()
    filepath = os.path.join(output_dir, 'diversity_overlay_all_functions.png')
    plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ diversity_overlay_all_functions.png")


def plot_diversity_vs_fitness_scatter(output_dir, df_experiments):
    """
    Scatter plot: relationship between diversity and fitness.
    """
    
    if df_experiments is None or 'diversity' not in df_experiments.columns:
        print("[WARN] No data for diversity-fitness correlation")
        return
    
    if 'fitness' not in df_experiments.columns:
        print("[WARN] No fitness data available")
        return
    
    print("\n[INFO] Generating diversity vs fitness correlation plot...")
    
    fig, ax = plt.subplots(figsize=(7.5, 6))
    
    mhs = sorted(df_experiments['MH'].unique())
    
    for mh in mhs:
        df_mh = df_experiments[df_experiments['MH'] == mh]
        
        # Filter valid values
        valid_mask = (df_mh['diversity'].notna()) & (df_mh['fitness'].notna())
        diversity_vals = df_mh[valid_mask]['diversity'].values
        fitness_vals = df_mh[valid_mask]['fitness'].values
        
        if len(diversity_vals) > 0:
            color = COLORS_MH.get(mh, '#999999')
            marker = MARKERS_MH.get(mh, 'o')
            
            # Scatter plot
            ax.scatter(diversity_vals, fitness_vals, label=mh, s=60,
                      color=color, marker=marker, alpha=0.6, edgecolors='black', linewidth=0.5)
            
            # Calculate correlation
            correlation = np.corrcoef(diversity_vals, fitness_vals)[0, 1]
            if not np.isnan(correlation):
                print(f"  - {mh}: correlation = {correlation:.4f}")
    
    ax.set_xlabel('Population Diversity', fontsize=10)
    ax.set_ylabel('Best Fitness Found', fontsize=10)
    ax.set_title('Diversity-Fitness Relationship in CEC2017', fontsize=11, fontweight='bold')
    ax.legend(loc='best', fontsize=8, framealpha=0.95)
    ax.grid(True, alpha=0.4, linestyle='--')
    
    plt.tight_layout()
    filepath = os.path.join(output_dir, 'diversity_vs_fitness_scatter.png')
    plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ diversity_vs_fitness_scatter.png")


def plot_diversity_distribution_boxplot(output_dir, df_experiments):
    """
    Boxplot: diversity distribution by MH.
    Visualizes variability of diversity across runs.
    """
    
    if df_experiments is None or 'diversity' not in df_experiments.columns:
        print("[WARN] No data for diversity boxplot")
        return
    
    print("\n[INFO] Generating diversity distribution boxplot...")
    
    fig, ax = plt.subplots(figsize=(7.5, 6))
    
    mhs = sorted(df_experiments['MH'].unique())
    
    # Prepare data for boxplot
    data_to_plot = [df_experiments[df_experiments['MH'] == mh]['diversity'].dropna().values 
                   for mh in mhs]
    
    # Create boxplot
    bp = ax.boxplot(data_to_plot, labels=mhs, patch_artist=True,
                   notch=False, widths=0.6)
    
    # Color boxes
    for patch, mh in zip(bp['boxes'], mhs):
        patch.set_facecolor(COLORS_MH.get(mh, '#999999'))
        patch.set_alpha(0.7)
    
    # Color whiskers and medians
    for whisker in bp['whiskers']:
        whisker.set(linewidth=1.5, color='gray')
    for median in bp['medians']:
        median.set(color='red', linewidth=2)
    
    ax.set_ylabel('Population Diversity', fontsize=10)
    ax.set_xlabel('Metaheuristic', fontsize=10)
    ax.set_title('Diversity Distribution by Metaheuristic CEC2017', 
                fontsize=11, fontweight='bold')
    ax.grid(True, alpha=0.4, axis='y', linestyle='--')
    
    plt.tight_layout()
    filepath = os.path.join(output_dir, 'diversity_distribution_boxplot.png')
    plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ diversity_distribution_boxplot.png")


def plot_diversity_timeline_all_mh(output_dir, df_experiments):
    """
    Timeline plot: temporal diversity evolution with multiple MH in same plot.
    Subplot visualization, one per MH.
    """
    
    if df_experiments is None:
        print("[WARN] No data for diversity timeline")
        return
    
    if 'diversity' not in df_experiments.columns:
        print("[WARN] No diversity column available")
        return
    
    print("\n[INFO] Generating diversity timeline by MH...")
    
    mhs = sorted(df_experiments['MH'].unique())
    n_mhs = len(mhs)
    
    # Create subplots (2x2 or 2x3 depending on MH count)
    ncols = min(3, n_mhs)
    nrows = (n_mhs + ncols - 1) // ncols
    
    fig, axes = plt.subplots(nrows, ncols, figsize=(7.5*ncols, 5*nrows))
    if n_mhs == 1:
        axes = [axes]
    else:
        axes = axes.flatten()
    
    for idx, mh in enumerate(mhs):
        ax = axes[idx]
        df_mh = df_experiments[df_experiments['MH'] == mh]
        
        if 'iteracion' in df_mh.columns and 'diversity' in df_mh.columns:
            # Diversity evolution by iteration
            diversity_by_iter = df_mh.groupby('iteracion')['diversity'].agg(['mean', 'std']).reset_index()
            
            color = COLORS_MH.get(mh, '#999999')
            marker = MARKERS_MH.get(mh, 'o')
            
            # Mean line
            ax.plot(diversity_by_iter['iteracion'], diversity_by_iter['mean'],
                   linewidth=1.5, marker=marker, markersize=3, color=color, alpha=0.8)
            
            # Uncertainty band
            ax.fill_between(diversity_by_iter['iteracion'],
                           diversity_by_iter['mean'] - diversity_by_iter['std'],
                           diversity_by_iter['mean'] + diversity_by_iter['std'],
                           color=color, alpha=0.2)
            
            ax.set_xlabel('Iteration', fontsize=9)
            ax.set_ylabel('Diversity', fontsize=9)
        else:
            # Show diversity distribution
            diversity_vals = df_mh['diversity'].dropna().values
            if len(diversity_vals) > 0:
                ax.hist(diversity_vals, bins=20, color=COLORS_MH.get(mh, '#999999'), 
                       alpha=0.7, edgecolor='black', linewidth=1)
                ax.set_xlabel('Diversity', fontsize=9)
                ax.set_ylabel('Frequency', fontsize=9)
        
        ax.set_title(f'{mh}', fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.4, linestyle='--')
    
    # Hide empty subplots
    for idx in range(n_mhs, len(axes)):
        axes[idx].set_visible(False)
    
    fig.suptitle('Diversity Timeline by Metaheuristic CEC2017', 
                fontsize=12, fontweight='bold', y=1.00)
    
    plt.tight_layout()
    filepath = os.path.join(output_dir, 'diversity_timeline_all_mh.png')
    plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ diversity_timeline_all_mh.png")


def main():
    """Execute diversity analysis."""
    
    print("\n" + "=" * 80)
    print("DIVERSITY ANALYSIS FOR CEC2017 BENCHMARKS")
    print("=" * 80)
    
    output_dir = ensure_output_directory()
    print(f"\n[INFO] Output directory: {output_dir}\n")
    
    # Load data
    df_experiments = load_experiment_data()
    if df_experiments is None:
        print("[ERROR] Could not load data")
        return
    
    # Generate or extract diversity data
    df_experiments = extract_or_generate_diversity_data(df_experiments)
    
    # Generate plots
    plot_diversity_evolution_by_function(output_dir, df_experiments)
    plot_diversity_overlay_all_functions(output_dir, df_experiments)
    plot_diversity_vs_fitness_scatter(output_dir, df_experiments)
    plot_diversity_distribution_boxplot(output_dir, df_experiments)
    plot_diversity_timeline_all_mh(output_dir, df_experiments)
    
    print("\n" + "=" * 80)
    print("[OK] DIVERSITY ANALYSIS COMPLETED")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
