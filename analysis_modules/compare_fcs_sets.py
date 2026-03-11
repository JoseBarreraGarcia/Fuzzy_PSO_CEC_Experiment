import pandas as pd
import numpy as np
from analysis_modules.level1_raw_data import extract_experiments_data

df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
df_exp = extract_experiments_data(verbose=False)

df_merged = df_iter.merge(
    df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
    on='id_experimento'
)

inst = 41
binariz = 'S4-ELIT'

df_target = df_merged[
    (df_merged['experimento'].astype(str) == str(inst)) & 
    (df_merged['binarizacion'] == binariz)
]

print(f"\n=== Comparación de W entre PSO_FCS:A/B/C/D para {inst} {binariz} ===\n")

output = []
output.append("Iteración | PSO_FCS:A | PSO_FCS:B | PSO_FCS:C | PSO_FCS:D | Diferencia(max-min)")
output.append("----------|-----------|-----------|-----------|-----------|--------------------")

for iter_val in [0, 5, 10, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500]:
    values = {}
    for mh in ['PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']:
        df_mh = df_target[(df_target['MH'] == mh) & (df_target['iter'] == iter_val)]
        w_mean = df_mh['w'].dropna().mean()
        values[mh] = w_mean
    
    diff = max(values.values()) - min(values.values()) if not all(np.isnan(v) for v in values.values()) else np.nan
    
    output.append(f"     {iter_val:3d}  | {values['PSO_FCS:A']:9.6f} | {values['PSO_FCS:B']:9.6f} | {values['PSO_FCS:C']:9.6f} | {values['PSO_FCS:D']:9.6f} | {diff:18.6f}")

with open('compare_fcs_sets.txt', 'w') as f:
    f.write('\n'.join(output))

print('\n'.join(output))
