from analysis_modules.level1_raw_data import extract_experiments_data
import pandas as pd

df_exp = extract_experiments_data(verbose=False)

print("Instancias y binarizaciones disponibles:")
print(df_exp[['experimento', 'binarizacion']].drop_duplicates().sort_values(['experimento', 'binarizacion']))

print(f"\nTotal: {len(df_exp[['experimento', 'binarizacion']].drop_duplicates())} combinaciones")
