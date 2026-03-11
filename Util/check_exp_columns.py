from analysis_modules.level1_raw_data import extract_experiments_data

df_exp = extract_experiments_data(verbose=False)
print("Columnas en df_exp:")
print(df_exp.columns.tolist())
print("\nPrimeras filas:")
print(df_exp.head())
