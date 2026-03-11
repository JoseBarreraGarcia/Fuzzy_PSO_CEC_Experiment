import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Read the w_timeseries data
df = pd.read_csv('Resultados/resumen/SCP/w_timeseries_SCP_41_S4-ELIT.csv')

# Get unique metaheuristics and runs
mhs = df['MH'].unique()
print(f"Metaheuristics found: {sorted(mhs)}")
print(f"Total rows: {len(df)}")
print(f"\nSample data:")
print(df.head(10))

# Create comparison plot for PSO_FCS variants
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Filter for PSO_FCS:A and PSO_FCS:B
pso_fcs_a = df[df['MH'] == 'PSO_FCS:A'].copy()
pso_fcs_b = df[df['MH'] == 'PSO_FCS:B'].copy()

print(f"\nPSO_FCS:A rows: {len(pso_fcs_a)}")
print(f"PSO_FCS:B rows: {len(pso_fcs_b)}")

# Plot 1: w evolution comparison
ax = axes[0, 0]
for mh, data in [('PSO_FCS:A', pso_fcs_a), ('PSO_FCS:B', pso_fcs_b)]:
    # Average per iteration
    w_per_iter = data.groupby('iter')['w'].agg(['mean', 'std'])
    ax.plot(w_per_iter.index, w_per_iter['mean'], label=mh, marker='o', markersize=3, linewidth=2)
    ax.fill_between(w_per_iter.index, 
                     w_per_iter['mean'] - w_per_iter['std'],
                     w_per_iter['mean'] + w_per_iter['std'],
                     alpha=0.2)
ax.set_xlabel('Iteration')
ax.set_ylabel('Inertia Weight (w)')
ax.set_title('Inertia Weight Evolution: PSO_FCS:A vs PSO_FCS:B')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 2: Diversity evolution comparison
ax = axes[0, 1]
for mh, data in [('PSO_FCS:A', pso_fcs_a), ('PSO_FCS:B', pso_fcs_b)]:
    div_per_iter = data.groupby('iter')['div'].mean()
    ax.plot(div_per_iter.index, div_per_iter.values, label=mh, marker='s', markersize=3, linewidth=2)
ax.set_xlabel('Iteration')
ax.set_ylabel('Diversity')
ax.set_title('Population Diversity Evolution')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 3: w vs diversity scatter
ax = axes[1, 0]
for mh, data, color in [('PSO_FCS:A', pso_fcs_a, 'blue'), ('PSO_FCS:B', pso_fcs_b, 'orange')]:
    # Remove nan values
    clean_data = data[~data['w'].isna()]
    ax.scatter(clean_data['div'], clean_data['w'], alpha=0.5, s=20, label=mh, color=color)
ax.set_xlabel('Diversity')
ax.set_ylabel('Inertia Weight (w)')
ax.set_title('w vs Diversity Relationship')
ax.legend()
ax.grid(True, alpha=0.3)

# Plot 4: Progress vs w
ax = axes[1, 1]
for mh, data, color in [('PSO_FCS:A', pso_fcs_a, 'blue'), ('PSO_FCS:B', pso_fcs_b, 'orange')]:
    clean_data = data[~data['w'].isna()]
    ax.scatter(clean_data['progress'], clean_data['w'], alpha=0.5, s=20, label=mh, color=color)
ax.set_xlabel('Progress (Iteration Rate)')
ax.set_ylabel('Inertia Weight (w)')
ax.set_title('w vs Progress (Exploration → Exploitation)')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('Resultados/resumen/SCP/comparison_PSO_FCS_fuzzy_sets.png', dpi=150, bbox_inches='tight')
print("\nPlot saved to: Resultados/resumen/SCP/comparison_PSO_FCS_fuzzy_sets.png")

# Generate summary statistics
print("\n" + "="*70)
print("SUMMARY STATISTICS: PSO_FCS:A vs PSO_FCS:B")
print("="*70)

for mh, data in [('PSO_FCS:A', pso_fcs_a), ('PSO_FCS:B', pso_fcs_b)]:
    print(f"\n{mh}:")
    clean_w = data[~data['w'].isna()]['w']
    print(f"  w - Mean: {clean_w.mean():.6f}, Std: {clean_w.std():.6f}")
    print(f"  w - Min: {clean_w.min():.6f}, Max: {clean_w.max():.6f}")
    print(f"  w - Median: {clean_w.median():.6f}")
    print(f"  Diversity - Mean: {data['div'].mean():.6f}")
    print(f"  Diversity - Std: {data['div'].std():.6f}")
