import pandas as pd
import numpy as np
from analysis_modules.level1_raw_data import extract_experiments_data

# Leer datos
df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
df_exp = extract_experiments_data(verbose=False)

# Merge
df_merged = df_iter.merge(
    df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
    on='id_experimento'
)

# Filtrar para una instancia y binarización específicas
inst = 41
binariz = 'S4-ELIT'

df_target = df_merged[
    (df_merged['experimento'] == inst) & 
    (df_merged['binarizacion'] == binariz)
]

print(f"\n=== Análisis de datos para Instance {inst} {binariz} ===\n")

for mh in ['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']:
    df_mh = df_target[df_target['MH'] == mh]
    
    print(f"\n{mh}:")
    print(f"  Total filas: {len(df_mh)}")
    
    # Estadísticas de w
    w_values = df_mh['w'].dropna()
    print(f"  W (no-NaN): {len(w_values)} valores")
    print(f"  W min: {w_values.min():.6f}, max: {w_values.max():.6f}, mean: {w_values.mean():.6f}")
    print(f"  W unique values: {w_values.nunique()}")
    
    # Ver si hay variabilidad entre experimentos
    exp_ids = df_mh['id_experimento'].unique()
    print(f"  Experimentos: {len(exp_ids)}")
    
    # Calcular w promedio por iteración
    w_by_iter = df_mh.groupby('iter')['w'].mean()
    print(f"  W promedio en iter 0: {w_by_iter.iloc[0]:.6f}")
    print(f"  W promedio en iter 100: {w_by_iter.iloc[100]:.6f}")
    print(f"  W promedio en iter 200: {w_by_iter.iloc[200]:.6f}")
    print(f"  W promedio en iter 500: {w_by_iter.iloc[min(500, len(w_by_iter)-1)]:.6f}")
    
    # Ver primeros 10 valores únicos
    unique_w = sorted(w_values.unique())[:10]
    print(f"  Primeros 10 w únicos: {[f'{x:.6f}' for x in unique_w]}")

# Comparación directa: w para iter 0 vs iter 500
print(f"\n\n=== Comparación de W entre MHs para iters específicas ===\n")
for iter_check in [0, 100, 200, 500]:
    print(f"\nIteración {iter_check}:")
    for mh in ['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']:
        df_mh = df_target[(df_target['MH'] == mh) & (df_target['iter'] == iter_check)]
        w_vals = df_mh['w'].dropna()
        if len(w_vals) > 0:
            print(f"  {mh:12s}: mean={w_vals.mean():.6f}, std={w_vals.std():.6f}, min={w_vals.min():.6f}, max={w_vals.max():.6f}")
        else:
            print(f"  {mh:12s}: NO DATA")
