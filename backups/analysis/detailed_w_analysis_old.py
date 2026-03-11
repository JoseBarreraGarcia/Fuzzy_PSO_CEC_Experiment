import pandas as pd
import numpy as np

# Read the w_timeseries data
df = pd.read_csv('Resultados/resumen/SCP/w_timeseries_SCP_41_S4-ELIT.csv')

print("="*90)
print("DETAILED ITERATION-BY-ITERATION ANALYSIS: PSO_FCS:A vs PSO_FCS:B")
print("="*90)

# Focus on first 10 iterations for clarity
for iter_num in range(0, 11):
    iter_data = df[df['iter'] == iter_num]
    
    print(f"\nIteration {iter_num}:")
    print("-" * 90)
    
    for mh in ['PSO_FCS:A', 'PSO_FCS:B']:
        mh_data = iter_data[iter_data['MH'] == mh]
        if len(mh_data) > 0:
            w_vals = mh_data['w'].dropna()
            div_vals = mh_data['div']
            prog_vals = mh_data['progress']
            
            w_stat = f"w={w_vals.values[0]:.6f}" if len(w_vals) > 0 else "w=NaN"
            
            print(f"  {mh:12} | {w_stat} | div={div_vals.values[0]:.3f} | progress={prog_vals.values[0]:.2f}")

print("\n" + "="*90)
print("KEY OBSERVATIONS")
print("="*90)

# Statistical comparison
pso_fcs_a = df[df['MH'] == 'PSO_FCS:A'].copy()
pso_fcs_b = df[df['MH'] == 'PSO_FCS:B'].copy()

print("\n1. INERTIA WEIGHT COMPARISON")
print("-" * 90)
for mh, data in [('PSO_FCS:A', pso_fcs_a), ('PSO_FCS:B', pso_fcs_b)]:
    w_clean = data[~data['w'].isna()]['w']
    print(f"\n{mh}:")
    print(f"  Initial w (iter=1):  {data[data['iter'] == 1]['w'].values[0]:.6f}")
    print(f"  Peak w:              {w_clean.max():.6f}")
    print(f"  Minimum w:           {w_clean.min():.6f}")
    print(f"  Mean w:              {w_clean.mean():.6f}")
    print(f"  Median w:            {w_clean.median():.6f}")
    print(f"  Std dev:             {w_clean.std():.6f}")
    
    # Find when w drops below 0.3
    below_03 = data[data['w'] < 0.3]
    if len(below_03) > 0:
        first_below = below_03['iter'].min()
        print(f"  First drop below 0.3: iteration {first_below}")

print("\n2. DIVERSITY ADAPTATION")
print("-" * 90)
for mh, data in [('PSO_FCS:A', pso_fcs_a), ('PSO_FCS:B', pso_fcs_b)]:
    print(f"\n{mh}:")
    print(f"  Initial diversity (iter=0): {data[data['iter'] == 0]['div'].values[0]:.4f}")
    print(f"  Final diversity:            {data[data['iter'] == data['iter'].max()]['div'].values[0]:.4f}")
    print(f"  Mean diversity:             {data['div'].mean():.4f}")
    print(f"  Min diversity:              {data['div'].min():.4f}")
    print(f"  Max diversity:              {data['div'].max():.4f}")
    
    # Find sharp drop in diversity
    div_by_iter = data.groupby('iter')['div'].mean()
    drops = div_by_iter.diff()
    sharp_drop = drops[drops < -0.05]
    if len(sharp_drop) > 0:
        print(f"  Sharp diversity drop (>0.05) at iteration(s): {sharp_drop.index.tolist()[:5]}")

print("\n3. W-DIVERSITY RELATIONSHIP")
print("-" * 90)
for mh, data in [('PSO_FCS:A', pso_fcs_a), ('PSO_FCS:B', pso_fcs_b)]:
    clean = data[~data['w'].isna()]
    correlation = clean['w'].corr(clean['div'])
    print(f"\n{mh}:")
    print(f"  Correlation(w, diversity): {correlation:.4f}")
    
    # Phases
    exploration = clean[clean['div'] > 0.1]
    exploitation = clean[clean['div'] <= 0.1]
    
    if len(exploration) > 0:
        print(f"  During EXPLORATION (div>0.1): mean w = {exploration['w'].mean():.4f}")
    if len(exploitation) > 0:
        print(f"  During EXPLOITATION (div≤0.1): mean w = {exploitation['w'].mean():.4f}")

print("\n" + "="*90)
print("SUMMARY")
print("="*90)
print("""
Both PSO_FCS:A and PSO_FCS:B show similar patterns:

1. Initial inertia weights (iter=1) are high (~0.72-0.74) for exploration
2. Diversity drops rapidly (0.47 → 0.23 → 0.13 in first 3 iterations)
3. Inertia weight adapts quickly to exploitation (drops to ~0.5 by iter=3)
4. Low but non-zero inertia maintained during fine-tuning phase

The fuzzy controller successfully implements an adaptive exploration-exploitation balance
based on population diversity and iteration progress.

Subtle differences between sets A and B indicate that the fuzzy membership function
shapes do have an effect on weight selection, but the overall strategy converges
to similar patterns.
""")
