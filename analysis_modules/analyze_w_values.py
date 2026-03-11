import pandas as pd
import numpy as np
from analysis_modules.level1_raw_data import extract_experiments_data

df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
df_exp = extract_experiments_data(verbose=False)

df_merged = df_iter.merge(
    df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
    on='id_experimento'
)

# Filtrar para una instancia y binarización específicas
inst = 41
binariz = 'S4-ELIT'

df_target = df_merged[
    (df_merged['experimento'].astype(str) == str(inst)) & 
    (df_merged['binarizacion'] == binariz)
]

print(f"\n=== Análisis de W para Instance {inst} {binariz} ===\n")

output = []
for mh in ['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']:
    df_mh = df_target[df_target['MH'] == mh]
    
    w_values = df_mh['w'].dropna()
    
    # Estadísticas
    output.append(f"\n{mh}:")
    output.append(f"  Total filas: {len(df_mh)}")
    output.append(f"  W no-NaN: {len(w_values)}")
    output.append(f"  W min: {w_values.min():.6f}, max: {w_values.max():.6f}, mean: {w_values.mean():.6f}, std: {w_values.std():.6f}")
    output.append(f"  W unique values: {w_values.nunique()}")
    
    # W promedio por iteración (primeros 20 y últimos 20)
    w_by_iter = df_mh.groupby('iter')['w'].agg(['mean', 'std', 'min', 'max'])
    output.append(f"\n  W por iteración (muestra):")
    output.append(f"    iter  | mean    | std     | min     | max")
    output.append(f"    ------|---------|---------|---------|--------")
    for idx in [0, 5, 10, 50, 100, 200, 300, 400, 500]:
        if idx in w_by_iter.index:
            row = w_by_iter.loc[idx]
            output.append(f"    {idx:4d} | {row['mean']:.6f} | {row['std']:.6f} | {row['min']:.6f} | {row['max']:.6f}")

with open('w_analysis.txt', 'w') as f:
    f.write('\n'.join(output))

print('\n'.join(output))
