import pandas as pd

print('='*80)
print('ANÁLISIS DETALLADO DE DATOS POR FUNCIÓN')
print('='*80)

df = pd.read_csv('Resultados/resumen/level1_raw_cec/ben_best_per_config.csv')

for funcion in sorted(df['funcion'].unique()):
    print(f'\n[{funcion}]')
    df_func = df[df['funcion'] == funcion].sort_values('fitness_mean')
    
    for idx, row in df_func.iterrows():
        print(f"  {row['MH']:15} | Mean: {row['fitness_mean']:10.4f} | Std: {row['fitness_std']:10.4f} | Gap: {row['gap_medio_pct']:8.2f}%")
