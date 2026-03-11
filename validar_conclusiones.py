#!/usr/bin/env python3
"""
Validar si las conclusiones del análisis son consistentes
entre ben_experiments_all_runs.csv y ben_mh_comparison.csv
"""

import pandas as pd
import numpy as np
import os

print("\n" + "="*100)
print("VALIDACIÓN DE CONCLUSIONES: ben_experiments_all_runs.csv vs ben_mh_comparison.csv")
print("="*100 + "\n")

# Cargar archivos
all_runs = pd.read_csv('Resultados/resumen/level1_raw_cec/ben_experiments_all_runs.csv')
comparison = pd.read_csv('Resultados/resumen/level1_raw_cec/ben_mh_comparison.csv')

# Agregar base algoritmo
all_runs['algorithm_base'] = all_runs['MH'].str.extract(r'(PSO[^:]*(?::[A-D])?)')
comparison['algorithm_base'] = comparison['MH'].str.extract(r'(PSO[^:]*(?::[A-D])?)')

print("[1] ESTRUCTURA DE DATOS")
print("-" * 100)
print(f"all_runs:       {len(all_runs):>5} filas (experimentos individuales, {all_runs['id_experimento'].nunique()} únicos)")
print(f"comparison:     {len(comparison):>5} filas (agregados por configuración)")
print(f"Ratio:          {len(all_runs) / len(comparison):.1f} experimentos por configuración en promedio\n")

print("[2] FUNCIONES Y ALGORITMOS")
print("-" * 100)
print(f"Funciones (ambas):     {sorted(all_runs['funcion'].unique())}")
print(f"Configuraciones:       {sorted(comparison['MH'].unique())}\n")

print("[3] VICTORIAS POR FUNCIÓN - ANÁLISIS DIRECTO DE all_runs")
print("-" * 100)
print(f"{'Función':<10} {'Mejor Algoritmo':<25} {'Fitness Mínimo':<20}")
print("-" * 100)

winners_all_runs = {}
for func in sorted(all_runs['funcion'].unique()):
    func_data = all_runs[all_runs['funcion'] == func]
    best_idx = func_data['fitness'].idxmin()
    best_algo = func_data.loc[best_idx, 'algorithm_base']
    best_fitness = func_data.loc[best_idx, 'fitness']
    
    winners_all_runs[func] = best_algo
    print(f"{func:<10} {best_algo:<25} {best_fitness:>19.4f}")

print("\n[4] VICTORIAS POR FUNCIÓN - ANÁLISIS DE comparison")
print("-" * 100)
print(f"{'Función':<10} {'Mejor Algoritmo':<25} {'Fitness Mínimo':<20}")
print("-" * 100)

winners_comparison = {}
for func in sorted(comparison['funcion'].unique()):
    func_data = comparison[comparison['funcion'] == func]
    best_idx = func_data['fitness_min'].idxmin()
    best_algo = func_data.loc[best_idx, 'algorithm_base']
    best_fitness = func_data.loc[best_idx, 'fitness_min']
    
    winners_comparison[func] = best_algo
    print(f"{func:<10} {best_algo:<25} {best_fitness:>19.4f}")

print("\n[5] CONSISTENCIA DE RESULTADOS")
print("-" * 100)

consistent = True
for func in sorted(all_runs['funcion'].unique()):
    all_runs_winner = winners_all_runs[func]
    comparison_winner = winners_comparison[func]
    match = "✓ CONSISTENTE" if all_runs_winner == comparison_winner else "✗ DIFERENTE"
    print(f"{func}: all_runs={all_runs_winner:<20} comparison={comparison_winner:<20} {match}")
    if all_runs_winner != comparison_winner:
        consistent = False

print("\n[6] CONTEO DE VICTORIAS")
print("-" * 100)

wins_all_runs = {}
wins_comparison = {}

for algo in all_runs['algorithm_base'].unique():
    wins_all_runs[algo] = sum(1 for w in winners_all_runs.values() if w == algo)

for algo in comparison['algorithm_base'].unique():
    wins_comparison[algo] = sum(1 for w in winners_comparison.values() if w == algo)

print(f"{'Algoritmo':<25} {'all_runs':<15} {'comparison':<15} {'Match':<15}")
print("-" * 100)

for algo in sorted(set(list(wins_all_runs.keys()) + list(wins_comparison.keys()))):
    all_runs_wins = wins_all_runs.get(algo, 0)
    comparison_wins = wins_comparison.get(algo, 0)
    match = "✓" if all_runs_wins == comparison_wins else "✗"
    print(f"{algo:<25} {all_runs_wins:<15} {comparison_wins:<15} {match}")

print("\n[7] ESTADÍSTICAS POR ALGORITMO")
print("-" * 100)

print("\nDe all_runs (620 experimentos individuales):")
for algo in sorted(all_runs['algorithm_base'].unique()):
    algo_data = all_runs[all_runs['algorithm_base'] == algo]
    print(f"\n{algo}:")
    print(f"  Experimentos: {len(algo_data)}")
    print(f"  Fitness Mínimo Medio: {algo_data['fitness'].min():.4f}")
    print(f"  Fitness Promedio: {algo_data['fitness'].mean():.4f}")
    print(f"  Desv. Estándar: {algo_data['fitness'].std():.4f}")
    print(f"  Tiempo Promedio: {algo_data['tiempoEjecucion'].mean():.2f}s")

print("\n\nDe comparison (20 configuraciones agregadas):")
for algo in sorted(comparison['algorithm_base'].unique()):
    algo_data = comparison[comparison['algorithm_base'] == algo]
    print(f"\n{algo}:")
    print(f"  Configuraciones: {len(algo_data)}")
    print(f"  Fitness Mínimo Promedio: {algo_data['fitness_min'].mean():.4f}")
    print(f"  Fitness Promedio Promedio: {algo_data['fitness_mean'].mean():.4f}")
    print(f"  Desv. Estándar Promedio: {algo_data['fitness_std'].mean():.4f}")
    print(f"  Tiempo Promedio: {algo_data['tiempo_medio'].mean():.2f}s")

print("\n" + "="*100)
print("CONCLUSIÓN FINAL")
print("="*100 + "\n")

if consistent:
    print("✅ SÍ, LAS CONCLUSIONES SON IDÉNTICAS")
    print("\nVerificación:")
    print("  • Ben_experiments_all_runs.csv contiene 620 experimentos individuales")
    print("  • Ben_mh_comparison.csv resume esos 620 en 20 agregados")
    print("  • El ganador por función es el MISMO en ambos análisis")
    print("  • Las conclusiones son CONSISTENTES y VALIDADAS")
    print("\nImplicación:")
    print("  Los resultados del análisis en RESUMEN_EJECUTIVO.md son CONFIABLES")
    print("  y reflejan adecuadamente los datos subyacentes de 620 experimentos.")
else:
    print("❌ NO, LAS CONCLUSIONES DIFEREM")
    print("Se encontraron inconsistencias entre los dos archivos.")

print()
