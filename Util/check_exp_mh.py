import pandas as pd
from analysis_modules.level1_raw_data import extract_experiments_data

# Obtener info de experimentos
df_exp = extract_experiments_data(verbose=False)

print("\n=== MH Type para Experimentos 1-30 ===\n")
for exp_id in range(1, 31):
    mh = df_exp[df_exp['id_experimento'] == exp_id]['MH'].values
    if len(mh) > 0:
        print(f"Exp {exp_id:2d}: {mh[0]}")
    else:
        print(f"Exp {exp_id:2d}: NOT FOUND")

print("\n\nTotal experimentos en DB:", len(df_exp))
print("\nMH distribution:")
print(df_exp['MH'].value_counts())
