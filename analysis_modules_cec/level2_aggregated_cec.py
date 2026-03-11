"""
LEVEL 2: AGGREGATED STATISTICS & PLOTS FOR CEC2017 BENCHMARKS

Generates aggregated plots and analysis based on Level 1 CSVs.

Outputs:
  Resultados/resumen/level2_aggregated_cec/
    - Convergence plots by function (fitness vs iterations)
    - Diversity plots by MH
    - PSO vs PSO_FCS comparison (fuzzy effectiveness)
    - Gap to optimum distribution by MH
    - Inertia weight vs convergence analysis
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent))

# LNCS Format Configuration
plt.rcParams['figure.figsize'] = (7.5, 6)  # 3.25 inch width for 1-column LNCS (88mm = 3.46 inch)
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


def add_bar_value_labels(ax, bars, fmt='.2f', orientation='h', label_position='end'):
    """Add value labels on bars in a bar plot.
    
    Args:
        ax: matplotlib axis
        bars: bar container from barh() or bar()
        fmt: format string for numbers
        orientation: 'h' for horizontal bars, 'v' for vertical bars
        label_position: 'end' for at end of bar, 'center' for at center of bar
    """
    for bar in bars:
        if orientation == 'h':
            # For horizontal bars (barh)
            width = bar.get_width()
            value_str = f'{width:{fmt}}'
            
            if label_position == 'center':
                # Labels at the center of the bar
                x_pos = width / 2.
                y_pos = bar.get_y() + bar.get_height() / 2.
                ha = 'center'
                va = 'center'
            else:  # 'end' (default)
                # Labels at the end of bar (right side)
                x_pos = width
                y_pos = bar.get_y() + bar.get_height() / 2.
                ha = 'left'
                va = 'center'
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


def ensure_directories():
    """Create necessary output directories."""
    base_dir = 'Resultados/resumen/level2_aggregated_cec'
    os.makedirs(os.path.join(base_dir, 'convergence'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'diversity'), exist_ok=True)
    os.makedirs(os.path.join(base_dir, 'comparison'), exist_ok=True)
    return base_dir


def load_raw_data():
    """Load CSVs from Level 1."""
    
    level1_dir = 'Resultados/resumen/level1_raw_cec'
    
    data = {}
    
    try:
        data['experiments'] = pd.read_csv(os.path.join(level1_dir, 'ben_experiments_all_runs.csv'))
        
        # Load additional CSVs if they exist
        if os.path.exists(os.path.join(level1_dir, 'ben_convergence_data.csv')):
            data['convergence'] = pd.read_csv(os.path.join(level1_dir, 'ben_convergence_data.csv'))
        else:
            data['convergence'] = None
        
        if os.path.exists(os.path.join(level1_dir, 'ben_diversity_metrics.csv')):
            data['diversity'] = pd.read_csv(os.path.join(level1_dir, 'ben_diversity_metrics.csv'))
        else:
            data['diversity'] = None
        
        if os.path.exists(os.path.join(level1_dir, 'ben_mh_comparison.csv')):
            data['comparison'] = pd.read_csv(os.path.join(level1_dir, 'ben_mh_comparison.csv'))
        else:
            data['comparison'] = None
        
        print("[OK] Level 1 CSVs loaded successfully")
        return data
    
    except Exception as e:
        print(f"[ERROR] Could not load CSVs: {e}")
        return None


def plot_convergence_by_function(output_dir, df_convergence):
    """Convergence plots (fitness vs iteration) by function."""
    
    if df_convergence is None or 'funcion' not in df_convergence.columns:
        print("[WARN] No convergence data available")
        return
    
    funciones = df_convergence['funcion'].unique()
    
    for funcion in funciones:
        df_func = df_convergence[df_convergence['funcion'] == funcion]
        mhs = df_func['MH'].unique()
        
        fig, ax = plt.subplots(figsize=(7.5, 6))
        
        # Plot average convergence by MH
        for mh in sorted(mhs):
            df_mh = df_func[df_func['MH'] == mh]
            
            # Group by iteration and calculate mean
            convergence_mean = df_mh.groupby(df_mh.columns.get_loc('iter') if 'iter' in df_mh.columns else np.arange(len(df_mh)))['fitness'].mean()
            
            color = COLORS_MH.get(mh, '#999999')
            ax.plot(convergence_mean.index, convergence_mean.values, 
                   label=mh, linewidth=1.5, marker='o', markersize=3, color=color)
        
        ax.set_xlabel('Iteration', fontsize=10)
        ax.set_ylabel('Best Fitness Found', fontsize=10)
        ax.set_title(f'Convergence Behavior - Function {funcion}', fontsize=11, fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        filepath = os.path.join(output_dir, 'convergence', f'convergence_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        
        print(f"  > Convergence saved: {funcion}")


def plot_diversity_by_mh(output_dir, df_diversity):
    """Population diversity plots by MH."""
    
    if df_diversity is None or 'diversity' not in df_diversity.columns:
        print("[WARN] No diversity data available")
        return
    
    funciones = df_diversity['funcion'].unique()
    
    for funcion in funciones:
        df_func = df_diversity[df_diversity['funcion'] == funcion]
        mhs = df_func['MH'].unique()
        
        fig, ax = plt.subplots(figsize=(7.5, 6))
        
        for mh in sorted(mhs):
            df_mh = df_func[df_func['MH'] == mh]
            
            # Average diversity by iteration
            diversity_mean = df_mh.groupby('iter')['diversity'].mean()
            
            color = COLORS_MH.get(mh, '#999999')
            ax.plot(diversity_mean.index, diversity_mean.values,
                   label=mh, linewidth=1.5, marker='s', markersize=3, color=color)
        
        ax.set_xlabel('Iteration', fontsize=10)
        ax.set_ylabel('Population Diversity', fontsize=10)
        ax.set_title(f'Diversity Evolution - Function {funcion}', fontsize=11, fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        filepath = os.path.join(output_dir, 'diversity', f'diversity_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        
        print(f"  > Diversity saved: {funcion}")


def plot_pso_vs_psofcs(output_dir, df_comparison, df_experiments=None):
    """PSO vs PSO_FCS comparison (fuzzy effectiveness)."""
    
    if df_comparison is None or 'MH' not in df_comparison.columns:
        print("[WARN] No comparison data available")
        return
    
    funciones = df_comparison['funcion'].unique()
    
    for funcion in funciones:
        df_func = df_comparison[df_comparison['funcion'] == funcion]
        
        fig, axes = plt.subplots(2, 2, figsize=(9, 8))
        
        # 1. Minimum fitness
        ax = axes[0, 0]
        df_sorted = df_func.sort_values('fitness_min')
        bars = ax.barh(df_sorted['MH'], df_sorted['fitness_min'])
        for i, (idx, row) in enumerate(df_sorted.iterrows()):
            mh = row['MH']
            bars[i].set_color(COLORS_MH.get(mh, '#999999'))
        add_bar_value_labels(ax, bars, fmt='.2e', orientation='h', label_position='center')
        ax.set_xlabel('Best Fitness', fontsize=12)
        ax.set_title('Best Fitness Achieved', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        # 2. Gap distribution (boxplot)
        ax = axes[0, 1]
        if df_experiments is not None and 'gap_optimo_pct' in df_experiments.columns:
            df_func_exp = df_experiments[df_experiments['funcion'] == funcion]
            data_to_plot = [df_func_exp[df_func_exp['MH'] == mh]['gap_optimo_pct'].dropna().values 
                           for mh in sorted(df_func_exp['MH'].unique())]
            labels = sorted(df_func_exp['MH'].unique())
            
            bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
            
            # Color boxes
            for patch, label in zip(bp['boxes'], labels):
                patch.set_facecolor(COLORS_MH.get(label, '#999999'))
                patch.set_alpha(0.7)
            
            # Add mean markers (X)
            for i, (label, data) in enumerate(zip(labels, data_to_plot)):
                mean_val = np.mean(data)
                ax.plot(i + 1, mean_val, marker='x', markersize=6, color='black', 
                       markeredgewidth=1.5, zorder=3)
            
            ax.set_ylabel('Gap to Optimum (%)', fontsize=12)
            ax.set_xlabel('Metaheuristic', fontsize=12)
            ax.set_title(f'Gap Distribution', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='y')
            ax.tick_params(axis='x', labelsize=9, rotation=22)
        else:
            # Fallback to bar chart if experiment data not available
            df_sorted = df_func.sort_values('gap_pct_medio')
            bars = ax.barh(df_sorted['MH'], df_sorted['gap_pct_medio'])
            for i, bar in enumerate(bars):
                mh = df_sorted.iloc[i]['MH']
                bar.set_color(COLORS_MH.get(mh, '#999999'))
            add_bar_value_labels(ax, bars, fmt='.1f', orientation='h')
            ax.set_xlabel('Gap to Optimum (%)', fontsize=12)
            ax.set_title('Relative Error to Global Optimum', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, axis='x')
        
        # 3. Mean fitness vs std (NO labels on data points)
        ax = axes[1, 0]
        for idx, row in df_func.iterrows():
            mh = row['MH']
            color = COLORS_MH.get(mh, '#999999')
            ax.errorbar(row['fitness_mean'], row.get('fitness_std', 0), 
                       fmt='o', markersize=8, label=mh, color=color, capsize=4, linewidth=1.5)
        ax.set_xlabel('Mean Fitness', fontsize=12)
        ax.set_ylabel('Standard Deviation', fontsize=12)
        ax.set_title('Mean ± Std. Dev.', fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=7)
        ax.grid(True, alpha=0.3)
        
        # 4. Execution time (with labels at start of bars)
        ax = axes[1, 1]
        df_sorted = df_func.sort_values('tiempo_medio')
        bars = ax.barh(df_sorted['MH'], df_sorted['tiempo_medio'])
        for i, bar in enumerate(bars):
            mh = df_sorted.iloc[i]['MH']
            bar.set_color(COLORS_MH.get(mh, '#999999'))
        add_bar_value_labels(ax, bars, fmt='.2f', orientation='h', label_position='center')
        ax.set_xlabel('Average Time (s)', fontsize=12)
        ax.set_title('Computational Efficiency', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='x')
        
        fig.suptitle(f'Comparative Analysis: PSO vs PSO_FCS - Function {funcion}', 
                    fontsize=11, fontweight='bold', y=0.995)
        
        plt.tight_layout()
        filepath = os.path.join(output_dir, 'comparison', f'comparison_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        
        print(f"  > Comparison saved: {funcion}")


def plot_gap_distribution(output_dir, df_experiments):
    """Gap to optimum distribution by MH."""
    
    if df_experiments is None or 'gap_optimo_pct' not in df_experiments.columns:
        print("[WARN] No gap data available")
        return
    
    funciones = df_experiments['funcion'].unique()
    
    for funcion in funciones:
        df_func = df_experiments[df_experiments['funcion'] == funcion]
        
        fig, ax = plt.subplots(figsize=(7.5, 6))
        
        # Boxplot of gap
        data_to_plot = [df_func[df_func['MH'] == mh]['gap_optimo_pct'].dropna().values 
                       for mh in sorted(df_func['MH'].unique())]
        labels = sorted(df_func['MH'].unique())
        
        bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
        
        # Color boxes
        for patch, label in zip(bp['boxes'], labels):
            patch.set_facecolor(COLORS_MH.get(label, '#999999'))
            patch.set_alpha(0.7)
        
        # Add mean markers (X)
        for i, (label, data) in enumerate(zip(labels, data_to_plot)):
            mean_val = np.mean(data)
            ax.plot(i + 1, mean_val, marker='x', markersize=8, color='black', 
                   markeredgewidth=1.5, zorder=3, label='Mean' if i == 0 else '')
        
        ax.set_ylabel('Gap to Optimum (%)', fontsize=10)
        ax.set_xlabel('Metaheuristic', fontsize=10)
        ax.set_title(f'Relative Error Distribution - Function {funcion}', 
                    fontsize=11, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        filepath = os.path.join(output_dir, 'comparison', f'gap_distribution_{funcion}.png')
        plt.savefig(filepath, dpi=DPI_OUTPUT, bbox_inches='tight')
        plt.close()
        
        print(f"  > Gap distribution saved: {funcion}")


def main():
    """Execute Level 2 plots generation."""
    
    print("\n" + "=" * 80)
    print("LEVEL 2: AGGREGATED STATISTICS & PLOTS FOR CEC2017 BENCHMARKS")
    print("=" * 80 + "\n")
    
    output_dir = ensure_directories()
    print(f"[INFO] Output directory: {output_dir}\n")
    
    # Load data
    data = load_raw_data()
    if data is None:
        return
    
    print("\n[INFO] Generating convergence plots...")
    plot_convergence_by_function(output_dir, data.get('convergence'))
    
    print("\n[INFO] Generating diversity plots...")
    plot_diversity_by_mh(output_dir, data.get('diversity'))
    
    print("\n[INFO] Generating PSO vs PSO_FCS comparisons...")
    plot_pso_vs_psofcs(output_dir, data.get('comparison'), data.get('experiments'))
    
    print("\n[INFO] Generating gap to optimum distributions...")
    plot_gap_distribution(output_dir, data.get('experiments'))
    
    print("\n" + "=" * 80)
    print("[OK] LEVEL 2 AGGREGATION COMPLETED")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
