import pandas as pd
import numpy as np
from analysis_modules.level1_raw_data import extract_experiments_data

# Leer CSV
df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')

# Obtener mapeo de exp_id -> MH
df_exp = extract_experiments_data(verbose=False)
id_to_mh = dict(zip(df_exp['id_experimento'], df_exp['MH']))

# Agregar MH a iteraciones
df_iter['MH'] = df_iter['id_experimento'].map(id_to_mh)

print("=== Verificación de W importados desde BD ===\n")

# Analizar diferentes MH
for mh_type in ['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']:
    df_mh = df_iter[df_iter['MH'] == mh_type]
    
    # Get first few experiments
    exp_ids = df_mh['id_experimento'].unique()[:3]
    
    print(f"\n{mh_type}:")
    for exp_id in exp_ids:
        df_exp_iter = df_mh[df_mh['id_experimento'] == exp_id].sort_values('iter')
        w_vals = df_exp_iter['w'].dropna().values
        
        # Check variation
        if len(w_vals) > 1:
            w_diffs = np.diff(w_vals)
            unique_diffs = len(np.unique(w_diffs))
            unique_vals = len(np.unique(w_vals))
            
            print(f"  Exp {exp_id}:")
            print(f"    W sample (10 primeras): {w_vals[:10]}")
            print(f"    Valores únicos: {unique_vals}/{len(w_vals)}")
            print(f"    Diferencias únicas: {unique_diffs}")
