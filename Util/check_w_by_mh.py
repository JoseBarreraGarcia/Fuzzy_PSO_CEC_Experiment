import pandas as pd
import numpy as np
from analysis_modules.level1_raw_data import extract_experiments_data

# Leer CSV de iteraciones
df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')

# Obtener info de experimentos
df_exp = extract_experiments_data(verbose=False)

# Merge para tener MH en cada fila
df_merged = df_iter.merge(df_exp[['id_experimento','MH']], on='id_experimento')

print("\n=== Análisis de W por Tipo de MH ===\n")

for mh_type in ['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']:
    df_mh = df_merged[df_merged['MH'] == mh_type]
    
    # Ver experimentos únicos para este MH
    exp_ids = df_mh['id_experimento'].unique()
    
    # Analizar primeros 2 experimentos
    print(f"\n{mh_type} (Total experimentos: {len(exp_ids)}):")
    
    for exp_id in exp_ids[:2]:
        df_exp_data = df_mh[df_mh['id_experimento'] == exp_id]
        w_vals = df_exp_data['w'].values
        
        # Ver si tiene variabilidad en w o es siempre la fórmula lineal
        w_diffs = np.diff(w_vals)
        
        # Contar valores únicos de w
        unique_w = len(np.unique(w_vals))
        
        print(f"  Exp {exp_id}:")
        print(f"    W valores únicos: {unique_w}/{len(w_vals)}")
        print(f"    W sample: {w_vals[:5]}")
        
        # Verificar si es la fórmula PSO estándar
        iter_vals = df_exp_data['iter'].values
        expected_w = 0.9 - iter_vals * (0.8 / 500)
        match = np.allclose(w_vals, expected_w, atol=1e-4)
        print(f"    Coincide fórmula PSO: {match}")
        
        if not match:
            diff = np.abs(w_vals - expected_w)
            print(f"    Max diferencia: {diff.max():.6f}")
            # Mostrar los primeros valores que no coinciden
            first_diff_idx = np.where(diff > 1e-4)[0]
            if len(first_diff_idx) > 0:
                idx = first_diff_idx[0]
                print(f"    Primer diferencia en iter {idx}: actual={w_vals[idx]:.6f}, esperado={expected_w[idx]:.6f}")
