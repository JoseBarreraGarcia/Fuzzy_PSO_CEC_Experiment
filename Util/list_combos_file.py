import pandas as pd
from analysis_modules.level1_raw_data import extract_experiments_data

df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
df_exp = extract_experiments_data(verbose=False)

df_merged = df_iter.merge(
    df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
    on='id_experimento',
    how='left'
)

output = []
output.append("Combinaciones disponibles:\n")
combos = df_merged[['experimento', 'binarizacion', 'MH']].drop_duplicates().sort_values(['experimento', 'binarizacion', 'MH'])
for _, row in combos.iterrows():
    count = len(df_merged[(df_merged['experimento'] == row['experimento']) & 
                          (df_merged['binarizacion'] == row['binarizacion']) & 
                          (df_merged['MH'] == row['MH'])])
    output.append(f"Instance {int(row['experimento']):2d} {row['binarizacion']:8s} {row['MH']:12s}: {count:5d} filas")

with open('combos_available.txt', 'w') as f:
    f.write('\n'.join(output))

print("Archivo generado: combos_available.txt")
