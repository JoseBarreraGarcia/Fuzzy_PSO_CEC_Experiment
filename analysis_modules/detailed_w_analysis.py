"""
Detailed iteration-by-iteration analysis module

Analyzes inertia weight adaptation across iterations
Detects fuzzy set behavior patterns and transitions
"""

import pandas as pd
import numpy as np
import os


def load_w_timeseries():
    """Load and concatenate all w_timeseries CSVs from database analysis"""
    import glob
    csv_files = glob.glob('Resultados/resumen/SCP/w_timeseries_SCP_*.csv')
    if not csv_files:
        raise FileNotFoundError("No w_timeseries_SCP_*.csv files found in Resultados/resumen/SCP/")
    df_list = [pd.read_csv(f) for f in csv_files]
    df = pd.concat(df_list, ignore_index=True)
    return df


def analyze_detailed(verbose=False):
    """Run detailed iteration-by-iteration analysis

    If `verbose` is False, minimal terminal output is shown and detailed
    statistics are written to CSV files in Resultados/resumen/SCP/.
    """
    VERBOSE = bool(verbose)

    if VERBOSE:
        print("[*] Loading w_timeseries data...")
    df = load_w_timeseries()
    
    mhs = sorted(df['MH'].unique())
    if VERBOSE:
        print(f"[*] Analyzing fuzzy sets: {mhs}")
    
    if VERBOSE:
        print("\n" + "=" * 90)
        print("DETAILED ITERATION-BY-ITERATION ANALYSIS: FUZZY SETS".center(90))
        print("=" * 90)
    
    # Show iterations 0-10 for clarity
    max_iter = min(10, df['iter'].max())
    
    for iter_num in range(0, max_iter + 1):
        iter_data = df[df['iter'] == iter_num]
        if len(iter_data) == 0:
            continue
        
        if VERBOSE:
            print(f"\nIteration {iter_num}:")
            print("-" * 90)
        
        for mh in mhs:
            mh_data = iter_data[iter_data['MH'] == mh]
            if len(mh_data) > 0:
                w_vals = mh_data['w'].dropna()
                div_vals = mh_data['div']
                prog_vals = mh_data['progress']
                
                if len(w_vals) > 0:
                    w_stat = f"w={w_vals.values[0]:8.6f}"
                else:
                    w_stat = "w=    NaN"
                
                div_stat = f"div={div_vals.values[0]:6.3f}"
                prog_stat = f"progress={prog_vals.values[0]:5.2f}"
                
                if VERBOSE:
                    print(f"  {mh:12} | {w_stat} | {div_stat} | {prog_stat}")
    
    # Statistical analysis
    # Statistical analysis (write to CSV)
    analyze_inertia_weight(df, mhs, verbose=VERBOSE)
    analyze_diversity_adaptation(df, mhs, verbose=VERBOSE)
    analyze_w_diversity_relationship(df, mhs, verbose=VERBOSE)


def analyze_inertia_weight(df, mhs, verbose=False):
    """Analyze inertia weight statistics and save CSV summary."""
    VERBOSE = bool(verbose)
    if VERBOSE:
        print("\n1. INERTIA WEIGHT STATISTICS")
        print("-" * 90)

    rows = []
    for mh in mhs:
        mh_data = df[df['MH'] == mh].copy()
        if len(mh_data) == 0:
            continue
        
        w_clean = mh_data[~mh_data['w'].isna()]['w']
        if len(w_clean) == 0:
            continue

        first_iter = mh_data[mh_data['iter'] == 1]
        initial_w = first_iter['w'].values[0] if len(first_iter) > 0 else np.nan

        # Ranges
        below_03 = w_clean[w_clean < 0.3]
        below_05 = w_clean[w_clean < 0.5]
        above_07 = w_clean[w_clean > 0.7]

        rows.append({
            'MH': mh,
            'initial_w': initial_w,
            'mean_w': w_clean.mean(),
            'median_w': w_clean.median(),
            'std_w': w_clean.std(),
            'min_w': w_clean.min(),
            'max_w': w_clean.max(),
            'count_below_03': len(below_03),
            'pct_below_03': (len(below_03) / len(w_clean) * 100) if len(w_clean)>0 else np.nan,
            'count_below_05': len(below_05),
            'count_above_07': len(above_07),
            'first_below_03': int(mh_data[mh_data['w'] < 0.3]['iter'].min()) if len(mh_data[mh_data['w'] < 0.3])>0 else np.nan
        })

    # Save CSV
    out_dir = os.path.join('Resultados', 'resumen', 'SCP')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'detailed_inertia_stats_SCP.csv')
    if rows:
        pd.DataFrame(rows).to_csv(out_path, index=False)
        if VERBOSE:
            print(f"[OK] Inertia weight stats CSV written: {out_path}")


def analyze_diversity_adaptation(df, mhs, verbose=False):
    """Analyze diversity pattern adaptation and save CSV."""
    VERBOSE = bool(verbose)
    if VERBOSE:
        print("\n2. DIVERSITY ADAPTATION")
        print("-" * 90)

    rows = []
    for mh in mhs:
        mh_data = df[df['MH'] == mh].copy()
        if len(mh_data) == 0:
            continue

        first = mh_data[mh_data['iter'] == 0]
        last = mh_data[mh_data['iter'] == mh_data['iter'].max()]
        div_by_iter = mh_data.groupby('iter')['div'].mean()
        drops = div_by_iter.diff()
        sharp_drops = drops[drops < -0.05]

        rows.append({
            'MH': mh,
            'initial_div': first['div'].values[0] if len(first)>0 else np.nan,
            'final_div': last['div'].values[0] if len(last)>0 else np.nan,
            'mean_div': mh_data['div'].mean(),
            'min_div': mh_data['div'].min(),
            'max_div': mh_data['div'].max(),
            'sharp_drop_iters': ";".join(map(str, sharp_drops.index.tolist())) if len(sharp_drops)>0 else ''
        })

    out_dir = os.path.join('Resultados', 'resumen', 'SCP')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'detailed_diversity_stats_SCP.csv')
    if rows:
        pd.DataFrame(rows).to_csv(out_path, index=False)
        if VERBOSE:
            print(f"[OK] Diversity stats CSV written: {out_path}")


def analyze_w_diversity_relationship(df, mhs, verbose=False):
    """Analyze relationship between w and diversity and save CSV."""
    VERBOSE = bool(verbose)
    rows = []
    for mh in mhs:
        mh_data = df[df['MH'] == mh].copy()
        if len(mh_data) == 0:
            continue
        clean = mh_data[~mh_data['w'].isna()]
        if len(clean) < 2:
            continue
        correlation = clean['w'].corr(clean['div'])
        w_vals = clean['w']
        phases = []
        if w_vals.max() > 0.7:
            phases.append('A')
        if (w_vals >= 0.4).any() and (w_vals <= 0.7).any():
            phases.append('B')
        if (w_vals < 0.4).any():
            phases.append('C')

        rows.append({
            'MH': mh,
            'correlation_w_div': correlation,
            'phases': ";".join(phases)
        })

    out_dir = os.path.join('Resultados', 'resumen', 'SCP')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'detailed_w_diversity_relationship_SCP.csv')
    if rows:
        pd.DataFrame(rows).to_csv(out_path, index=False)
        if VERBOSE:
            print(f"[OK] W-Diversity relationship CSV written: {out_path}")


if __name__ == '__main__':
    analyze_detailed()
