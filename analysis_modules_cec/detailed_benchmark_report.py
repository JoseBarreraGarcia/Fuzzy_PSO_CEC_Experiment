#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DETAILED BENCHMARK COMPARISON REPORT
=====================================

Análisis visual y tabular de los 31 experimentos con comparativas PSO vs PSO_FCS.
Genera gráficos con formato LNCS para paper de conferencia.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path
import sys

# Import optimal values
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Graficos_Benchmark.graficosBenchmark import OPTIMOS_GLOBALES

# ============================================================================
# CONFIGURATION & LNCS FORMAT
# ============================================================================

class LNCSConfig:
    """LNCS format configuration for publication-quality figures."""
    
    DPI = 300
    FIGURE_WIDTH = 7.5
    FIGURE_HEIGHT = 6.0
    FONT_FAMILY = 'Times New Roman'
    FONT_SIZE_BASE = 9
    FONT_SIZE_LABEL = 10
    FONT_SIZE_TITLE = 11
    FONT_SIZE_LEGEND = 8
    
    COLORS = {
        'PSO': '#FF6B6B',
        'PSO_FCS:A': '#4ECDC4',
        'PSO_FCS:B': '#45B7D1',
        'PSO_FCS:C': '#FFA07A',
        'PSO_FCS:D': '#95E1D3'
    }
    
    @staticmethod
    def apply_style():
        """Apply LNCS style globally."""
        plt.rcParams['font.family'] = LNCSConfig.FONT_FAMILY
        plt.rcParams['font.size'] = LNCSConfig.FONT_SIZE_BASE
        plt.rcParams['figure.dpi'] = LNCSConfig.DPI
        plt.rcParams['savefig.dpi'] = LNCSConfig.DPI
        plt.rcParams['axes.labelsize'] = LNCSConfig.FONT_SIZE_LABEL
        plt.rcParams['axes.titlesize'] = LNCSConfig.FONT_SIZE_TITLE
        plt.rcParams['xtick.labelsize'] = LNCSConfig.FONT_SIZE_BASE
        plt.rcParams['ytick.labelsize'] = LNCSConfig.FONT_SIZE_BASE
        plt.rcParams['legend.fontsize'] = LNCSConfig.FONT_SIZE_LEGEND
        plt.rcParams['figure.autolayout'] = True

# ============================================================================
# DATA LOADING & PREPARATION
# ============================================================================

def load_and_prepare_data():
    """Load and prepare benchmark comparison data."""
    csv_path = 'Resultados/resumen/level1_raw_cec/ben_mh_comparison.csv'
    df = pd.read_csv(csv_path)
    
    # Extract algorithm base
    df['algorithm_base'] = df['MH'].str.extract(r'(PSO[^:]*(?::[A-D])?)')
    
    # Add optimum values
    df['optimo'] = df['funcion'].map(OPTIMOS_GLOBALES)
    
    # Calculate absolute gap
    df['gap_absolute'] = np.abs(df['fitness_min'] - df['optimo'])
    
    return df

# ============================================================================
# VISUALIZATION 1: PSO vs PSO_FCS Fitness Comparison
# ============================================================================

def plot_fitness_comparison(df):
    """Create fitness comparison plot with proper LNCS formatting."""
    LNCSConfig.apply_style()
    
    fig, ax = plt.subplots(figsize=(LNCSConfig.FIGURE_WIDTH, LNCSConfig.FIGURE_HEIGHT))
    
    functions = sorted(df['funcion'].unique())
    x_pos = np.arange(len(functions))
    width = 0.2
    
    # Get best result per algorithm per function
    best_by_algo_func = {}
    for algo in df['algorithm_base'].unique():
        best_by_algo_func[algo] = {}
        algo_data = df[df['algorithm_base'] == algo]
        for func in functions:
            func_data = algo_data[algo_data['funcion'] == func]
            if not func_data.empty:
                best_idx = func_data['fitness_min'].idxmin()
                best_by_algo_func[algo][func] = df.loc[best_idx, 'fitness_min']
    
    # Plot bars for each algorithm
    algorithms = sorted(df['algorithm_base'].unique())
    for i, algo in enumerate(algorithms):
        offset = x_pos + (i - len(algorithms)/2 + 0.5) * width
        fitness_values = [best_by_algo_func[algo].get(f, 0) for f in functions]
        ax.bar(offset, fitness_values, width=width, label=algo, 
               color=LNCSConfig.COLORS.get(algo, '#999999'), alpha=0.8)
    
    ax.set_xlabel('Benchmark Function', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_ylabel('Best Fitness Value', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_title('PSO vs PSO_FCS: Fitness Comparison', fontsize=LNCSConfig.FONT_SIZE_TITLE)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(functions)
    ax.legend(loc='best', frameon=True, fancybox=False, shadow=False)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    output_dir = 'Resultados/resumen/comprehensive_analysis/plots'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_file = os.path.join(output_dir, '01_fitness_comparison.png')
    plt.savefig(output_file, dpi=LNCSConfig.DPI, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

# ============================================================================
# VISUALIZATION 2: Gap to Optimum Comparison
# ============================================================================

def plot_gap_comparison(df):
    """Create gap to optimum comparison plot."""
    LNCSConfig.apply_style()
    
    fig, ax = plt.subplots(figsize=(LNCSConfig.FIGURE_WIDTH, LNCSConfig.FIGURE_HEIGHT))
    
    functions = sorted(df['funcion'].unique())
    x_pos = np.arange(len(functions))
    width = 0.2
    
    # Get best gap per algorithm per function
    best_gap_by_algo_func = {}
    for algo in df['algorithm_base'].unique():
        best_gap_by_algo_func[algo] = {}
        algo_data = df[df['algorithm_base'] == algo]
        for func in functions:
            func_data = algo_data[algo_data['funcion'] == func]
            if not func_data.empty:
                best_idx = func_data['gap_absolute'].idxmin()
                best_gap_by_algo_func[algo][func] = df.loc[best_idx, 'gap_absolute']
    
    # Plot bars for each algorithm
    algorithms = sorted(df['algorithm_base'].unique())
    for i, algo in enumerate(algorithms):
        offset = x_pos + (i - len(algorithms)/2 + 0.5) * width
        gap_values = [best_gap_by_algo_func[algo].get(f, 0) for f in functions]
        ax.bar(offset, gap_values, width=width, label=algo, 
               color=LNCSConfig.COLORS.get(algo, '#999999'), alpha=0.8)
    
    ax.set_xlabel('Benchmark Function', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_ylabel('Absolute Gap to Optimum', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_title('Gap to Optimum: PSO vs PSO_FCS', fontsize=LNCSConfig.FONT_SIZE_TITLE)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(functions)
    ax.legend(loc='best', frameon=True, fancybox=False, shadow=False)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    output_dir = 'Resultados/resumen/comprehensive_analysis/plots'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_file = os.path.join(output_dir, '02_gap_comparison.png')
    plt.savefig(output_file, dpi=LNCSConfig.DPI, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

# ============================================================================
# VISUALIZATION 3: Execution Time Comparison
# ============================================================================

def plot_time_comparison(df):
    """Create execution time comparison plot."""
    LNCSConfig.apply_style()
    
    fig, ax = plt.subplots(figsize=(LNCSConfig.FIGURE_WIDTH, LNCSConfig.FIGURE_HEIGHT))
    
    functions = sorted(df['funcion'].unique())
    x_pos = np.arange(len(functions))
    width = 0.2
    
    # Get average time per algorithm per function
    avg_time_by_algo_func = {}
    for algo in df['algorithm_base'].unique():
        avg_time_by_algo_func[algo] = {}
        algo_data = df[df['algorithm_base'] == algo]
        for func in functions:
            func_data = algo_data[algo_data['funcion'] == func]
            if not func_data.empty:
                avg_time_by_algo_func[algo][func] = func_data['tiempo_medio'].mean()
    
    # Plot bars for each algorithm
    algorithms = sorted(df['algorithm_base'].unique())
    for i, algo in enumerate(algorithms):
        offset = x_pos + (i - len(algorithms)/2 + 0.5) * width
        time_values = [avg_time_by_algo_func[algo].get(f, 0) for f in functions]
        ax.bar(offset, time_values, width=width, label=algo, 
               color=LNCSConfig.COLORS.get(algo, '#999999'), alpha=0.8)
    
    ax.set_xlabel('Benchmark Function', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_ylabel('Execution Time (seconds)', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_title('Computational Time: PSO vs PSO_FCS', fontsize=LNCSConfig.FONT_SIZE_TITLE)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(functions)
    ax.legend(loc='best', frameon=True, fancybox=False, shadow=False)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    output_dir = 'Resultados/resumen/comprehensive_analysis/plots'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_file = os.path.join(output_dir, '03_time_comparison.png')
    plt.savefig(output_file, dpi=LNCSConfig.DPI, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

# ============================================================================
# VISUALIZATION 4: Algorithm Robustness (Box Plot)
# ============================================================================

def plot_robustness_boxplot(df):
    """Create robustness analysis with box plots."""
    LNCSConfig.apply_style()
    
    fig, ax = plt.subplots(figsize=(LNCSConfig.FIGURE_WIDTH, LNCSConfig.FIGURE_HEIGHT))
    
    # Prepare data for box plot
    algorithms = sorted(df['algorithm_base'].unique())
    box_data = [df[df['algorithm_base'] == algo]['fitness_min'].values for algo in algorithms]
    
    bp = ax.boxplot(box_data, labels=algorithms, patch_artist=True)
    
    # Color the boxes
    for patch, algo in zip(bp['boxes'], algorithms):
        patch.set_facecolor(LNCSConfig.COLORS.get(algo, '#999999'))
        patch.set_alpha(0.7)
    
    ax.set_ylabel('Fitness Value', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_xlabel('Algorithm', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_title('Algorithm Robustness: Fitness Distribution', fontsize=LNCSConfig.FONT_SIZE_TITLE)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    
    output_dir = 'Resultados/resumen/comprehensive_analysis/plots'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_file = os.path.join(output_dir, '04_robustness_boxplot.png')
    plt.savefig(output_file, dpi=LNCSConfig.DPI, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

# ============================================================================
# VISUALIZATION 5: Quality vs Time Trade-off
# ============================================================================

def plot_quality_time_tradeoff(df):
    """Create quality vs time trade-off scatter plot."""
    LNCSConfig.apply_style()
    
    fig, ax = plt.subplots(figsize=(LNCSConfig.FIGURE_WIDTH, LNCSConfig.FIGURE_HEIGHT))
    
    algorithms = df['algorithm_base'].unique()
    
    for algo in sorted(algorithms):
        algo_data = df[df['algorithm_base'] == algo]
        
        ax.scatter(algo_data['tiempo_medio'], algo_data['fitness_min'], 
                   label=algo, s=150, alpha=0.7, color=LNCSConfig.COLORS.get(algo, '#999999'))
    
    ax.set_xlabel('Execution Time (seconds)', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_ylabel('Best Fitness', fontsize=LNCSConfig.FONT_SIZE_LABEL)
    ax.set_title('Quality vs Time Trade-off', fontsize=LNCSConfig.FONT_SIZE_TITLE)
    ax.legend(loc='best', frameon=True, fancybox=False, shadow=False)
    ax.grid(True, alpha=0.3, linestyle='--')
    
    output_dir = 'Resultados/resumen/comprehensive_analysis/plots'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    output_file = os.path.join(output_dir, '05_quality_time_tradeoff.png')
    plt.savefig(output_file, dpi=LNCSConfig.DPI, bbox_inches='tight')
    print(f"✓ Saved: {output_file}")
    plt.close()

# ============================================================================
# DETAILED TABULAR REPORT
# ============================================================================

def generate_detailed_report(df):
    """Generate comprehensive tabular report."""
    output_dir = 'Resultados/resumen/comprehensive_analysis'
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Report 1: Full detailed results
    report_file = os.path.join(output_dir, 'detailed_benchmark_results.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*100 + "\n")
        f.write("COMPREHENSIVE BENCHMARK ANALYSIS: DETAILED RESULTS\n")
        f.write("="*100 + "\n\n")
        
        f.write("DATASET OVERVIEW:\n")
        f.write("-" * 100 + "\n")
        f.write(f"Total experiments: {len(df)}\n")
        f.write(f"Benchmark functions: {', '.join(sorted(df['funcion'].unique()))}\n")
        f.write(f"Algorithms tested: {', '.join(sorted(df['algorithm_base'].unique()))}\n")
        f.write(f"Configurations: {', '.join(sorted(df['MH'].unique()))}\n\n")
        
        # Detailed results table
        f.write("DETAILED RESULTS BY CONFIGURATION:\n")
        f.write("-" * 100 + "\n")
        f.write(f"{'Func':<6} {'Config':<20} {'Fitness Min':<15} {'Fitness Mean':<15} {'Fitness Std':<15} {'Gap (Abs)':<15} {'Time (s)':<12}\n")
        f.write("-" * 100 + "\n")
        
        for func in sorted(df['funcion'].unique()):
            func_data = df[df['funcion'] == func]
            for _, row in func_data.iterrows():
                f.write(f"{row['funcion']:<6} {row['MH']:<20} {row['fitness_min']:>14.6e} "
                       f"{row['fitness_mean']:>14.6e} {row['fitness_std']:>14.6e} "
                       f"{row['gap_absolute']:>14.6e} {row['tiempo_medio']:>11.2f}\n")
            f.write("-" * 100 + "\n")
        
        # Summary statistics
        f.write("\nSUMMARY STATISTICS BY ALGORITHM:\n")
        f.write("-" * 100 + "\n")
        
        for algo in sorted(df['algorithm_base'].unique()):
            algo_data = df[df['algorithm_base'] == algo]
            f.write(f"\n{algo}:\n")
            f.write(f"  Mean Fitness: {algo_data['fitness_min'].mean():.6e}\n")
            f.write(f"  Median Fitness: {algo_data['fitness_min'].median():.6e}\n")
            f.write(f"  Std Dev: {algo_data['fitness_min'].std():.6e}\n")
            f.write(f"  Min Fitness: {algo_data['fitness_min'].min():.6e}\n")
            f.write(f"  Max Fitness: {algo_data['fitness_min'].max():.6e}\n")
            f.write(f"  Avg Gap to Optimum: {algo_data['gap_absolute'].mean():.6e}\n")
            f.write(f"  Avg Execution Time: {algo_data['tiempo_medio'].mean():.2f}s\n")
        
        # Win count
        f.write("\n" + "="*100 + "\n")
        f.write("ALGORITHM WIN COUNT:\n")
        f.write("-" * 100 + "\n")
        
        for algo in sorted(df['algorithm_base'].unique()):
            wins = 0
            for func in df['funcion'].unique():
                func_data = df[df['funcion'] == func]
                if func_data.loc[func_data['fitness_min'].idxmin(), 'algorithm_base'] == algo:
                    wins += 1
            f.write(f"{algo:<25} {wins} / {df['funcion'].nunique()} functions\n")
    
    print(f"✓ Saved detailed report: {report_file}")
    
    # Export summary CSV
    summary_file = os.path.join(output_dir, 'benchmark_results_summary.csv')
    summary_df = df[['funcion', 'MH', 'fitness_min', 'fitness_mean', 'fitness_std', 
                     'gap_absolute', 'tiempo_medio', 'algorithm_base']].copy()
    summary_df.to_csv(summary_file, index=False)
    print(f"✓ Saved summary CSV: {summary_file}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute comprehensive visualization and reporting pipeline."""
    print("\n" + "="*100)
    print("GENERATING DETAILED BENCHMARK COMPARISON REPORT WITH VISUALIZATIONS")
    print("="*100 + "\n")
    
    # Load data
    print("[1] Loading benchmark data...")
    df = load_and_prepare_data()
    print(f"✓ Loaded {len(df)} experiment results\n")
    
    # Apply LNCS style globally
    LNCSConfig.apply_style()
    
    # Generate visualizations
    print("[2] Generating LNCS-formatted visualizations...\n")
    plot_fitness_comparison(df)
    plot_gap_comparison(df)
    plot_time_comparison(df)
    plot_robustness_boxplot(df)
    plot_quality_time_tradeoff(df)
    
    # Generate reports
    print("\n[3] Generating detailed tabular reports...\n")
    generate_detailed_report(df)
    
    print("\n" + "="*100)
    print("[OK] COMPREHENSIVE ANALYSIS COMPLETED")
    print("="*100)
    print("\nOutput directory: Resultados/resumen/comprehensive_analysis/")
    print("Files generated:")
    print("  - plots/01_fitness_comparison.png")
    print("  - plots/02_gap_comparison.png")
    print("  - plots/03_time_comparison.png")
    print("  - plots/04_robustness_boxplot.png")
    print("  - plots/05_quality_time_tradeoff.png")
    print("  - detailed_benchmark_results.txt")
    print("  - benchmark_results_summary.csv")

if __name__ == '__main__':
    main()
