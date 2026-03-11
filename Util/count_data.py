import pandas as pd
from analysis_modules.level1_raw_data import extract_experiments_data

df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
df_exp = extract_experiments_data(verbose=False)

print(f"Total filas en xpl_xpt_iterations.csv: {len(df_iter)}")
print(f"Total experimentos en DB: {len(df_exp)}")

# Merge
df_merged = df_iter.merge(
    df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
    on='id_experimento',
    how='left'
)

print(f"\nDistribución de datos por MH:")
print(df_merged['MH'].value_counts().sort_index())

print(f"\nCombinaciones únicas (instancia, binarización, MH):")
combos = df_merged[['experimento', 'binarizacion', 'MH']].drop_duplicates()
print(f"Total: {len(combos)}")

# Ver un ejemplo específico
inst = 41
binariz = 'S4-ELIT'

print(f"\n\nDatos para instancia {inst} {binariz}:")
for mh in ['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']:
    count = len(df_merged[(df_merged['experimento'] == inst) & 
                          (df_merged['binarizacion'] == binariz) & 
                          (df_merged['MH'] == mh)])
    print(f"  {mh:12s}: {count:6d} filas")
