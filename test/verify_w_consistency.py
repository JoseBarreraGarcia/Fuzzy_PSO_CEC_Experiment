import pandas as pd
import numpy as np

# Leer el CSV
df = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')

print("\n=== Análisis de Consistencia de W por Experimento ===\n")

# Agrupar por id_experimento
grouped = df.groupby('id_experimento')

# Analizar primeros 10 experimentos
for exp_id, group in list(grouped)[0:10]:
    w_vals = group['w'].values
    iter_vals = group['iter'].values
    
    # Verificar si w sigue patrón lineal decreciente
    w_diffs = np.diff(w_vals)
    
    print(f"\nExperimento {exp_id}:")
    print(f"  Total iteraciones: {len(group)}")
    print(f"  W sample (primeros 10): {w_vals[:10]}")
    print(f"  W diferencias (delta entre iters): {w_diffs[:9]}")
    print(f"  W decrecimiento consistente: {np.allclose(w_diffs, w_diffs[0])}")  # ¿Todas las diffs iguales?
    print(f"  W min: {w_vals.min():.6f}, max: {w_vals.max():.6f}")
    
    # Ver si la fórmula lineal coincide
    # PSO normal: w = 0.9 - iter * (0.8/500)
    expected_w = 0.9 - iter_vals * (0.8 / 500)
    match = np.allclose(w_vals, expected_w, atol=1e-4)
    print(f"  Coincide con fórmula PSO (0.9 - iter*0.8/500): {match}")
    
    if not match:
        diff = np.abs(w_vals - expected_w)
        print(f"    Max diferencia: {diff.max():.6f}")
