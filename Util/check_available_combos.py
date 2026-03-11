import pandas as pd
from analysis_modules.level1_raw_data import extract_experiments_data

df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
df_exp = extract_experiments_data(verbose=False)

df_merged = df_iter.merge(
    df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
    on='id_experimento'
)

print("Combinaciones disponibles:")
combos = df_merged[['experimento', 'binarizacion', 'MH']].drop_duplicates().sort_values(['experimento', 'binarizacion', 'MH'])
for _, row in combos.iterrows():
    print(f"  Instance {row['experimento']:2d} {row['binarizacion']:8s} {row['MH']:12s}")

# Contar datos por MH
print("\n\nTotal de filas por MH:")
print(df_merged['MH'].value_counts().sort_index())
