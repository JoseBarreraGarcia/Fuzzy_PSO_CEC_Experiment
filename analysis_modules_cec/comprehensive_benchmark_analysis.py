#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMPREHENSIVE BENCHMARK ANALYSIS: 31 CEC2017 EXPERIMENTS
=========================================================

Análisis integral de los 31 experimentos de optimización sobre 23 funciones benchmark CEC2017.
Compara PSO vs PSO_FCS (variantes A, B, C, D) con múltiples configuraciones.

Structure:
  - Level 1: Estadísticas descriptivas por metaheurística y función
  - Level 2: Análisis de desempeño relativo (gaps, rankings)
  - Level 3: Análisis de escalabilidad y complejidad funcional
  - Level 4: Recomendaciones y conclusiones
"""

import pandas as pd
import numpy as np
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Import optimal values
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Graficos_Benchmark.graficosBenchmark import OPTIMOS_GLOBALES

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration for comprehensive analysis."""
    
    LEVEL1_DIR = 'Resultados/resumen/level1_raw_cec'
    OUTPUT_DIR = 'Resultados/resumen/comprehensive_analysis'
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    
    # CEC2017 Functions
    FUNCTIONS = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10',
                 'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18', 'F19', 'F20',
                 'F21', 'F22', 'F23']
    
    FUNCTION_TYPES = {
        'unimodal': ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7'],
        'multimodal': ['F8', 'F9', 'F10', 'F11', 'F12', 'F13'],
        'composition': ['F14', 'F15', 'F16', 'F17', 'F18', 'F19', 'F20', 'F21', 'F22', 'F23']
    }
    
    # Algorithm definitions
    ALGORITHMS = {
        'PSO': 'PSO (Standard)',
        'PSO_FCS:A': 'PSO_FCS Set A (Conservative)',
        'PSO_FCS:B': 'PSO_FCS Set B (Balanced)',
        'PSO_FCS:C': 'PSO_FCS Set C (Exploratory)',
        'PSO_FCS:D': 'PSO_FCS Set D (Aggressive)'
    }

# ============================================================================
# LEVEL 1: DATA LOADING & DESCRIPTIVE STATISTICS
# ============================================================================

def load_benchmark_data():
    """Load CEC2017 benchmark comparison results."""
    csv_path = os.path.join(Config.LEVEL1_DIR, 'ben_mh_comparison.csv')
    df = pd.read_csv(csv_path)
    return df

def compute_gap_absolute(df):
    """Calculate absolute gap to optimum for each function."""
    df['optimo'] = df['funcion'].map(OPTIMOS_GLOBALES)
    df['gap_absolute'] = np.abs(df['fitness_min'] - df['optimo'])
    df['gap_absolute_pct'] = (df['gap_absolute'] / np.abs(df['optimo']) * 100).replace([np.inf, -np.inf], np.nan)
    return df

def extract_algorithm_variant(mh_string):
    """Extract base algorithm and variant (e.g., 'PSO_FCS:A:5' -> 'PSO_FCS:A', '5')."""
    parts = str(mh_string).split(':')
    if len(parts) >= 2:
        base = ':'.join(parts[:2])  # 'PSO_FCS:A'
        variant = ':'.join(parts[2:]) if len(parts) > 2 else None
        return base, variant
    return mh_string, None

def level1_descriptive_stats(df):
    """Generate Level 1: Descriptive statistics."""
    print("\n" + "="*90)
    print("LEVEL 1: DESCRIPTIVE STATISTICS & DETAILED RESULTS")
    print("="*90)
    
    # Summary statistics by algorithm
    print("\n[1.1] OVERALL PERFORMANCE BY ALGORITHM")
    print("-" * 90)
    summary = df.groupby('algorithm_base').agg({
        'fitness_min': ['count', 'mean', 'median', 'std', 'min', 'max'],
        'gap_absolute': ['mean', 'median', 'std'],
        'tiempo_medio': ['mean', 'median', 'std']
    }).round(6)
    print(summary)
    
    # Best/Worst per function
    print("\n[1.2] BEST & WORST PERFORMANCE PER FUNCTION")
    print("-" * 90)
    print(f"{'Function':<10} {'Best Algo':<25} {'Best Fitness':<15} {'Worst Algo':<25} {'Worst Fitness':<15}")
    print("-" * 90)
    
    for func in sorted(df['funcion'].unique()):
        func_data = df[df['funcion'] == func]
        best_idx = func_data['fitness_min'].idxmin()
        worst_idx = func_data['fitness_min'].idxmax()
        
        best_algo = func_data.loc[best_idx, 'MH']
        best_fit = func_data.loc[best_idx, 'fitness_min']
        worst_algo = func_data.loc[worst_idx, 'MH']
        worst_fit = func_data.loc[worst_idx, 'fitness_min']
        
        print(f"{func:<10} {best_algo:<25} {best_fit:>14.4e} {worst_algo:<25} {worst_fit:>14.4e}")
    
    # Function complexity ranking (by optimo distance)
    print("\n[1.3] FUNCTION DIFFICULTY RANKING")
    print("-" * 90)
    print(f"{'Function':<10} {'Optimum':<15} {'Mean Gap':<15} {'Std Gap':<15} {'Difficulty':<15}")
    print("-" * 90)
    
    func_difficulty = []
    for func in sorted(df['funcion'].unique()):
        func_data = df[df['funcion'] == func]
        
        optimo = OPTIMOS_GLOBALES[func]
        mean_gap = func_data['gap_absolute'].mean()
        std_gap = func_data['gap_absolute'].std()
        
        func_difficulty.append({
            'funcion': func,
            'optimo': optimo,
            'mean_gap': mean_gap,
            'std_gap': std_gap
        })
        
        difficulty_score = mean_gap / (std_gap + 1e-10)
        print(f"{func:<10} {optimo:>14.4e} {mean_gap:>14.4e} {std_gap:>14.4e} {difficulty_score:>14.4f}")
    
    return df, pd.DataFrame(func_difficulty)

# ============================================================================
# LEVEL 2: RELATIVE PERFORMANCE ANALYSIS
# ============================================================================

def level2_relative_performance(df, func_difficulty):
    """Generate Level 2: Relative performance and rankings."""
    print("\n" + "="*90)
    print("LEVEL 2: RELATIVE PERFORMANCE & RANKINGS")
    print("="*90)
    
    # Overall winning algorithm
    print("\n[2.1] ALGORITHM WIN COUNT (Number of functions where each algorithm is best)")
    print("-" * 90)
    
    win_count = {}
    for algo in df['algorithm_base'].unique():
        win_count[algo] = 0
    
    all_functions = sorted(df['funcion'].unique())
    for func in all_functions:
        func_data = df[df['funcion'] == func]
        best_algo = func_data.loc[func_data['fitness_min'].idxmin(), 'algorithm_base']
        win_count[best_algo] += 1
    
    for algo in sorted(win_count.keys(), key=lambda x: win_count[x], reverse=True):
        print(f"{algo:<25} {win_count[algo]:>3} / {len(all_functions)} functions")
    
    # PSO vs PSO_FCS direct comparison
    print("\n[2.2] PSO vs PSO_FCS DIRECT COMPARISON")
    print("-" * 90)
    
    pso_df = df[df['algorithm_base'] == 'PSO'].set_index('funcion')
    fcs_algorithms = df[df['algorithm_base'].str.contains('PSO_FCS')]['algorithm_base'].unique()
    
    comparison_data = []
    for func in all_functions:
        pso_fitness = pso_df.loc[func, 'fitness_min'] if func in pso_df.index else None
        
        best_fcs_fitness = np.inf
        best_fcs_algo = None
        for algo in fcs_algorithms:
            algo_data = df[(df['funcion'] == func) & (df['algorithm_base'] == algo)]
            if not algo_data.empty:
                best_fitness = algo_data['fitness_min'].min()
                if best_fitness < best_fcs_fitness:
                    best_fcs_fitness = best_fitness
                    best_fcs_algo = algo
        
        if pso_fitness is not None and best_fcs_fitness != np.inf:
            improvement = ((pso_fitness - best_fcs_fitness) / np.abs(pso_fitness) * 100) if pso_fitness != 0 else 0
            winner = 'PSO_FCS' if best_fcs_fitness < pso_fitness else 'PSO'
            comparison_data.append({
                'funcion': func,
                'PSO': pso_fitness,
                'Best_PSO_FCS': best_fcs_fitness,
                'Best_PSO_FCS_Algo': best_fcs_algo,
                'Improvement_%': improvement,
                'Winner': winner
            })
    
    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))
    
    # Fuzzy set performance comparison
    print("\n[2.3] PSO_FCS FUZZY SET PERFORMANCE RANKING")
    print("-" * 90)
    
    fcs_sets = df[df['algorithm_base'].str.contains('PSO_FCS')]['algorithm_base'].unique()
    fcs_performance = []
    
    for fcs_set in sorted(fcs_sets):
        set_data = df[df['algorithm_base'] == fcs_set]
        if not set_data.empty:
            fcs_performance.append({
                'Fuzzy_Set': fcs_set,
                'Avg_Fitness': set_data['fitness_min'].mean(),
                'Median_Fitness': set_data['fitness_min'].median(),
                'Avg_Gap': set_data['gap_absolute'].mean(),
                'Avg_Time': set_data['tiempo_medio'].mean(),
                'N_Functions': len(set_data)
            })
    
    fcs_perf_df = pd.DataFrame(fcs_performance).sort_values('Avg_Fitness')
    print(fcs_perf_df.to_string(index=False))
    
    return comparison_df, fcs_perf_df

# ============================================================================
# LEVEL 3: SCALABILITY & COMPLEXITY ANALYSIS
# ============================================================================

def level3_scalability_analysis(df, func_difficulty):
    """Generate Level 3: Scalability by function type and complexity."""
    print("\n" + "="*90)
    print("LEVEL 3: SCALABILITY & COMPLEXITY ANALYSIS")
    print("="*90)
    
    all_functions = sorted(df['funcion'].unique())
    
    # Performance by algorithm (since we have limited functions)
    print("\n[3.1] PERFORMANCE BY ALGORITHM")
    print("-" * 90)
    
    for algo in sorted(df['algorithm_base'].unique()):
        algo_data = df[df['algorithm_base'] == algo]
        print(f"\n{algo}:")
        print(f"  Functions analyzed: {', '.join(sorted(algo_data['funcion'].unique()))}")
        print(f"  Mean Fitness: {algo_data['fitness_min'].mean():>12.4e}")
        print(f"  Std Fitness: {algo_data['fitness_min'].std():>12.4e}")
        print(f"  Avg Gap to Optimum: {algo_data['gap_absolute'].mean():>12.4e}")
        print(f"  Avg Execution Time: {algo_data['tiempo_medio'].mean():>12.2f}s")
    
    # Algorithm advantage per function
    print("\n[3.2] ALGORITHM ADVANTAGE BY FUNCTION")
    print("-" * 90)
    
    for func in all_functions:
        func_data = df[df['funcion'] == func]
        best_algo = func_data.loc[func_data['fitness_min'].idxmin(), 'algorithm_base']
        best_fitness = func_data['fitness_min'].min()
        
        print(f"\n{func}:")
        print(f"  Winner: {best_algo}")
        print(f"  Best Fitness: {best_fitness:>12.4e}")
        
        for algo in sorted(func_data['algorithm_base'].unique()):
            algo_data = func_data[func_data['algorithm_base'] == algo]
            mean_fitness = algo_data['fitness_min'].mean()
            gap_from_best = ((mean_fitness - best_fitness) / np.abs(best_fitness) * 100) if best_fitness != 0 else 0
            print(f"    {algo:<25} Mean: {mean_fitness:>12.4e}  Gap: {gap_from_best:>+7.2f}%")
    
    # Efficiency: Fitness vs Execution Time
    print("\n[3.3] COMPUTATIONAL EFFICIENCY ANALYSIS (Quality vs Runtime)")
    print("-" * 90)
    
    efficiency_data = []
    for algo in df['algorithm_base'].unique():
        algo_data = df[df['algorithm_base'] == algo]
        
        # Efficiency metric: lower fitness with lower time is better
        avg_fitness = algo_data['fitness_min'].mean()
        avg_time = algo_data['tiempo_medio'].mean()
        efficiency_ratio = avg_fitness / avg_time  # Lower is better
        
        efficiency_data.append({
            'Algorithm': algo,
            'Avg_Fitness': avg_fitness,
            'Avg_Time_s': avg_time,
            'Fitness_per_Second': efficiency_ratio
        })
    
    efficiency_df = pd.DataFrame(efficiency_data).sort_values('Fitness_per_Second')
    print(efficiency_df.to_string(index=False))
    
    return efficiency_df

# ============================================================================
# LEVEL 4: CONCLUSIONS & RECOMMENDATIONS
# ============================================================================

def level4_conclusions(df, func_difficulty, comparison_df, fcs_perf_df, efficiency_df):
    """Generate Level 4: Key findings and recommendations."""
    print("\n" + "="*90)
    print("LEVEL 4: KEY FINDINGS & RECOMMENDATIONS")
    print("="*90)
    
    print("\n[4.1] OVERALL WINNER")
    print("-" * 90)
    
    # Best overall algorithm
    best_algo = df.groupby('algorithm_base')['fitness_min'].mean().idxmin()
    best_fitness = df[df['algorithm_base'] == best_algo]['fitness_min'].mean()
    
    print(f"Best Overall Algorithm: {best_algo}")
    print(f"Average Fitness across all functions: {best_fitness:.4e}")
    
    # PSO vs PSO_FCS verdict
    pso_mean = df[df['algorithm_base'] == 'PSO']['fitness_min'].mean()
    fcs_variants = df[df['algorithm_base'].str.contains('PSO_FCS')]
    fcs_mean = fcs_variants['fitness_min'].mean()
    
    improvement_pct = ((pso_mean - fcs_mean) / np.abs(pso_mean)) * 100 if pso_mean != 0 else 0
    
    print(f"\nPSO Mean Fitness: {pso_mean:.4e}")
    print(f"PSO_FCS Mean Fitness: {fcs_mean:.4e}")
    print(f"PSO_FCS vs PSO Change: {improvement_pct:+.2f}%")
    
    if fcs_mean < pso_mean:
        print("✓ VERDICT: PSO_FCS shows IMPROVEMENT over standard PSO")
    else:
        print("✗ VERDICT: PSO outperforms PSO_FCS variants")
    
    print("\n[4.2] BEST PERFORMING FUZZY SET")
    print("-" * 90)
    
    if not fcs_perf_df.empty:
        best_fcs = fcs_perf_df.iloc[0]
        print(f"Best Set: {best_fcs['Fuzzy_Set']}")
        print(f"  Average Fitness: {best_fcs['Avg_Fitness']:.4e}")
        print(f"  Average Gap to Optimum: {best_fcs['Avg_Gap']:.4e}")
        print(f"  Average Execution Time: {best_fcs['Avg_Time']:.2f}s")
    
    print("\n[4.3] FUNCTION-SPECIFIC RECOMMENDATIONS")
    print("-" * 90)
    
    # Identify where each algorithm excels
    algo_strengths = {}
    all_functions = sorted(df['funcion'].unique())
    
    for algo in df['algorithm_base'].unique():
        wins = 0
        strong_functions = []
        for func in all_functions:
            func_data = df[df['funcion'] == func]
            if not func_data.empty:
                best = func_data.loc[func_data['fitness_min'].idxmin(), 'algorithm_base']
                if best == algo:
                    wins += 1
                    strong_functions.append(func)
        if wins > 0:
            algo_strengths[algo] = {'wins': wins, 'functions': strong_functions}
    
    for algo in sorted(algo_strengths.keys(), key=lambda x: algo_strengths[x]['wins'], reverse=True):
        strength_info = algo_strengths[algo]
        print(f"\n{algo}:")
        print(f"  Excels on {strength_info['wins']} functions:")
        print(f"  {', '.join(strength_info['functions'])}")
    
    print("\n[4.4] COMPUTATIONAL COST ANALYSIS")
    print("-" * 90)
    
    for algo in sorted(efficiency_df['Algorithm'].unique()):
        algo_info = efficiency_df[efficiency_df['Algorithm'] == algo].iloc[0]
        print(f"{algo:<25} {algo_info['Avg_Time_s']:>8.2f}s")
    
    print("\n[4.5] FINAL RECOMMENDATIONS")
    print("-" * 90)
    
    print("""
1. For general purpose optimization: Use the best overall algorithm for balanced performance
2. For function-specific needs: See section [4.3] for algorithm strengths by function
3. For time-critical applications: Consider faster algorithms even if slightly lower quality
4. For research purposes: PSO_FCS fuzzy inertia weight control shows promise on specific functions
    """)

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Execute comprehensive analysis pipeline."""
    print("\n" + "="*90)
    print("COMPREHENSIVE BENCHMARK ANALYSIS: 31 CEC2017 EXPERIMENTS")
    print("="*90)
    
    # Load data
    print("\n[LOADING DATA]")
    df = load_benchmark_data()
    df = compute_gap_absolute(df)
    
    # Extract algorithm base
    df[['algorithm_base', 'algorithm_variant']] = df['MH'].apply(
        lambda x: pd.Series(extract_algorithm_variant(x))
    )
    
    print(f"✓ Loaded {len(df)} experiment results")
    print(f"✓ Covering {df['funcion'].nunique()} benchmark functions")
    print(f"✓ {df['algorithm_base'].nunique()} algorithm variants")
    
    # Level 1
    df, func_difficulty = level1_descriptive_stats(df)
    
    # Level 2
    comparison_df, fcs_perf_df = level2_relative_performance(df, func_difficulty)
    
    # Level 3
    efficiency_df = level3_scalability_analysis(df, func_difficulty)
    
    # Level 4
    level4_conclusions(df, func_difficulty, comparison_df, fcs_perf_df, efficiency_df)
    
    # Save summary reports
    print("\n" + "="*90)
    print("SAVING DETAILED REPORTS")
    print("="*90)
    
    summary_output = os.path.join(Config.OUTPUT_DIR, 'comprehensive_analysis_summary.csv')
    comparison_df.to_csv(summary_output, index=False)
    print(f"✓ Saved comparison report: {summary_output}")
    
    fcs_output = os.path.join(Config.OUTPUT_DIR, 'fcs_fuzzy_sets_performance.csv')
    fcs_perf_df.to_csv(fcs_output, index=False)
    print(f"✓ Saved fuzzy sets ranking: {fcs_output}")
    
    efficiency_output = os.path.join(Config.OUTPUT_DIR, 'computational_efficiency.csv')
    efficiency_df.to_csv(efficiency_output, index=False)
    print(f"✓ Saved efficiency analysis: {efficiency_output}")
    
    print("\n[OK] COMPREHENSIVE ANALYSIS COMPLETED")

if __name__ == '__main__':
    main()
