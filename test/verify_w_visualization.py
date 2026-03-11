import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from analysis_modules.level1_raw_data import extract_experiments_data

# Leer iteraciones
df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')

# Obtener info de experimentos
df_exp = extract_experiments_data(verbose=False)
df_merged = df_iter.merge(df_exp[['id_experimento','MH', 'experimento', 'binarizacion']], on='id_experimento')

# Filtrar para una instancia y binarización específicas
target_inst = 41
target_bin = 'S4-ELIT'

df_target = df_merged[(df_merged['experimento'] == target_inst) & 
                       (df_merged['binarizacion'] == target_bin)]

print(f"\nDatos para {target_inst} {target_bin}:")
print(f"Total filas: {len(df_target)}")
print(f"Experimentos únicos: {df_target['id_experimento'].nunique()}")
print(f"MH tipos: {df_target['MH'].unique()}")

# Crear figura con evolución de w
fig, axes = plt.subplots(1, 5, figsize=(20, 4))
fig.suptitle(f'Evolución de W (Inertia Weight) - SCP {target_inst} {target_bin}', fontsize=14)

for idx, mh in enumerate(['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']):
    ax = axes[idx]
    
    df_mh = df_target[df_target['MH'] == mh]
    
    # Graficar primeros 10 experimentos de este MH
    exp_ids = df_mh['id_experimento'].unique()[:10]
    
    for exp_id in exp_ids:
        df_exp_data = df_mh[df_mh['id_experimento'] == exp_id].sort_values('iter')
        w_vals = df_exp_data['w'].dropna()
        iters = df_exp_data[df_exp_data['w'].notna()]['iter'].values
        
        ax.plot(iters, w_vals.values, alpha=0.6, linewidth=1)
    
    ax.set_xlabel('Iteración')
    ax.set_ylabel('W value')
    ax.set_title(mh)
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, 1])

plt.tight_layout()
plt.savefig('Resultados/resumen/level2_aggregated/plots/w/test_w_verification.png', dpi=150)
print(f"\n✓ Gráfico guardado: Resultados/resumen/level2_aggregated/plots/w/test_w_verification.png")

# Mostrar estadísticas de w
print("\n=== Estadísticas de W por MH ===\n")
for mh in ['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']:
    df_mh = df_target[df_target['MH'] == mh]
    w_vals = df_mh['w'].dropna()
    
    print(f"{mh}:")
    print(f"  Count: {len(w_vals)}")
    print(f"  Mean: {w_vals.mean():.4f}, Std: {w_vals.std():.4f}")
    print(f"  Min: {w_vals.min():.4f}, Max: {w_vals.max():.4f}")
    print(f"  Unique values: {w_vals.nunique()}")
    print()
