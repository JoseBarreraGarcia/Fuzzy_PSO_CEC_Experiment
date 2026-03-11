import pandas as pd
from analysis_modules.level1_raw_data import extract_experiments_data

df = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
df_exp = extract_experiments_data(verbose=False)
merged = df.merge(df_exp[['id_experimento','MH']], on='id_experimento')

print("\n=== W Value Distribution by MH ===\n")
for mh in ['PSO','PSO_FCS:A','PSO_FCS:B','PSO_FCS:C','PSO_FCS:D']:
    w_non_na = merged[merged['MH']==mh]['w'].notna().sum()
    tot = len(merged[merged['MH']==mh])
    pct = 100*w_non_na/tot if tot > 0 else 0
    print(f'{mh:15s}: {w_non_na:6d}/{tot:6d} ({pct:5.1f}%)')

print("\n=== Sample w values for each MH ===\n")
for mh in ['PSO','PSO_FCS:A','PSO_FCS:B']:
    sample = merged[merged['MH']==mh]['w'].dropna().head(20).values
    if len(sample) > 0:
        print(f'{mh}:')
        print(f'  First 20 w values: {sample}')
        print(f'  Mean: {sample.mean():.4f}, Min: {sample.min():.4f}, Max: {sample.max():.4f}')
