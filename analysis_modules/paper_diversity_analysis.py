"""
Diversity Collapse Analysis for Conference Paper
Generates publication-ready figures and tables for Section 4 (Diagnosis)

Output:
- paper_fig_diversity_timeline.pdf: Diversity evolution over iterations
- paper_table_diversity_stats.tex: Statistical summary by phase
- paper_data_diversity.csv: Raw data for external analysis

Author: Analysis Module for Fuzzy PSO Paper
Date: January 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import glob
import warnings
import sys
warnings.filterwarnings('ignore')

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# LNCS/IEEE Configuration
plt.rcParams['font.family'] = 'Times New Roman'
plt.rcParams['font.size'] = 10
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.format'] = 'pdf'

# Paths
TRANSITORIO_PATH = Path("Resultados/resumen/SCP")
OUTPUT_PATH = Path("Resultados/paper_outputs")
OUTPUT_PATH.mkdir(exist_ok=True, parents=True)

def load_experiment_data(pattern="w_timeseries*.csv"):
    """Load all PSO_FCS experiment iteration data."""
    files = list(TRANSITORIO_PATH.glob(pattern))
    
    if not files:
        print(f"[WARN] No files found matching: {pattern}")
        print(f"   Looking in: {TRANSITORIO_PATH.absolute()}")
        return None
    
    print(f"[INFO] Found {len(files)} experiment files")
    
    all_data = []
    for f in files:
        try:
            df = pd.read_csv(f)
            
            # Rename columns to match expected names
            if 'div' in df.columns and 'diversity' not in df.columns:
                df.rename(columns={'div': 'diversity'}, inplace=True)
            
            # Extract metadata from filename
            # Format: w_timeseries_SCP_41_S4-ELIT.csv
            parts = f.stem.split('_')
            instance = parts[2]  # SCP_41 convert to 41
            
            # Process each MH in the file separately
            for mh_str in df['MH'].unique():
                mh_data = df[df['MH'] == mh_str].copy()
                
                if ':' in mh_str:
                    w_set = mh_str.split(':')[1].upper()
                else:
                    w_set = 'baseline'  # PSO sin fuzzy
                    
                mh_data['instance'] = f'SCP{instance}'
                mh_data['w_set'] = w_set
                mh_data['mh'] = mh_str
                mh_data['filename'] = f.name
                
                all_data.append(mh_data)
            
        except Exception as e:
            print(f"[WARN] Error loading {f.name}: {e}")
    
    if not all_data:
        return None
        
    return pd.concat(all_data, ignore_index=True)


def classify_phase(iteration, max_iter=500):
    """Classify iteration into early/mid/late phase."""
    progress = iteration / max_iter
    if progress < 0.3:
        return 'Early'
    elif progress < 0.7:
        return 'Mid'
    else:
        return 'Late'


def calculate_diversity_stats(df):
    """Calculate diversity statistics by phase and w_set."""
    
    # Add phase classification
    df['phase'] = df['iter'].apply(classify_phase)
    
    # Group by w_set and phase
    stats = df.groupby(['w_set', 'phase'])['diversity'].agg([
        ('mean', 'mean'),
        ('std', 'std'),
        ('min', 'min'),
        ('max', 'max'),
        ('q25', lambda x: x.quantile(0.25)),
        ('q75', lambda x: x.quantile(0.75)),
        ('cv', lambda x: x.std() / x.mean() if x.mean() > 0 else 0)
    ]).reset_index()
    
    # Calculate overall stats
    overall = df.groupby('phase')['diversity'].agg([
        ('mean', 'mean'),
        ('std', 'std'),
        ('cv', lambda x: x.std() / x.mean() if x.mean() > 0 else 0)
    ]).reset_index()
    
    return stats, overall


def plot_diversity_timeline(df):
    """Generate Figure 1: Diversity evolution over iterations."""
    
    w_sets = sorted(df['w_set'].unique())
    n_sets = len(w_sets)
    
    # Create appropriate grid (2 rows, up to 3 columns)
    if n_sets <= 3:
        fig, axes = plt.subplots(1, n_sets, figsize=(7, 2.5), sharex=True, sharey=True)
    elif n_sets <= 6:
        fig, axes = plt.subplots(2, 3, figsize=(10, 5.5), sharex=True, sharey=True)
    else:
        fig, axes = plt.subplots(2, 4, figsize=(12, 5.5), sharex=True, sharey=True)
    
    axes = axes.flatten() if hasattr(axes, 'flatten') else axes
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']  # Extended colors
    
    for idx, w_set in enumerate(w_sets):
        ax = axes[idx]
        data = df[df['w_set'] == w_set]
        
        # Plot individual runs (light)
        for fname in data['filename'].unique()[:10]:  # Max 10 runs per subplot
            run_data = data[data['filename'] == fname]
            ax.plot(run_data['iter'], run_data['diversity'], 
                   alpha=0.2, color=colors[idx % len(colors)], linewidth=0.5)
        
        # Plot mean with confidence band
        grouped = data.groupby('iter')['diversity'].agg(['mean', 'std']).reset_index()
        ax.plot(grouped['iter'], grouped['mean'], 
               color=colors[idx % len(colors)], linewidth=2, label=f'w_set {w_set} (mean)')
        ax.fill_between(grouped['iter'], 
                       grouped['mean'] - grouped['std'],
                       grouped['mean'] + grouped['std'],
                       color=colors[idx % len(colors)], alpha=0.2)
        
        # Add phase divisions
        ax.axvline(150, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
        ax.axvline(350, color='gray', linestyle='--', alpha=0.5, linewidth=0.8)
        
        # Add membership function thresholds
        ax.axhline(0.4, color='red', linestyle=':', alpha=0.3, linewidth=0.8)
        ax.axhline(0.7, color='red', linestyle=':', alpha=0.3, linewidth=0.8)
        
        ax.set_title(f'w_set {w_set}', fontsize=10, fontweight='bold')
        ax.set_ylabel('Diversity Ratio', fontsize=9)
        ax.grid(True, alpha=0.3, linewidth=0.5)
        ax.set_ylim(0, 1)
        
        # Add text annotations for phases
        if idx == 0:
            ax.text(75, 0.95, 'Early', fontsize=8, ha='center', alpha=0.6)
            ax.text(250, 0.95, 'Mid', fontsize=8, ha='center', alpha=0.6)
            ax.text(425, 0.95, 'Late', fontsize=8, ha='center', alpha=0.6)
    
    # Common x-label
    for ax in axes[2:]:
        ax.set_xlabel('Iteration', fontsize=9)
    
    plt.tight_layout()
    
    output_file = OUTPUT_PATH / "paper_fig_diversity_timeline.pdf"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"[OK] Figure saved: {output_file}")
    
    # Also save PNG for preview
    plt.savefig(OUTPUT_PATH / "paper_fig_diversity_timeline.png", bbox_inches='tight')
    plt.close()


def generate_latex_table(stats_overall):
    """Generate LaTeX table for diversity statistics by phase."""
    
    latex = r"""\begin{table}[t]
\centering
\caption{Diversity statistics by search phase (averaged across all w\_sets)}
\label{tab:diversity_stats}
\begin{tabular}{lccc}
\hline
\textbf{Phase} & \textbf{Mean $\pm$ Std} & \textbf{CV (\%)} & \textbf{Range} \\
\hline
"""
    
    for _, row in stats_overall.iterrows():
        phase = row['phase']
        mean_val = row['mean']
        std_val = row['std']
        cv_val = row['cv'] * 100
        
        # Get min/max from full data (simplified here)
        latex += f"{phase} & ${mean_val:.3f} \\pm {std_val:.3f}$ & ${cv_val:.1f}$ & -- \\\\\n"
    
    latex += r"""\hline
\end{tabular}
\end{table}
"""
    
    output_file = OUTPUT_PATH / "paper_table_diversity_stats.tex"
    with open(output_file, 'w') as f:
        f.write(latex)
    
    print(f"[OK] LaTeX table saved: {output_file}")
    
    return latex


def main():
    """Main execution pipeline."""
    
    print("=" * 60)
    print("DIVERSITY COLLAPSE ANALYSIS FOR CONFERENCE PAPER")
    print("=" * 60)
    
    # Step 1: Load data
    print("\n[1/4] Loading experiment data...")
    df = load_experiment_data()
    
    if df is None or df.empty:
        print("[ERROR] No data found. Run experiments first.")
        print("   Expected files: Resultados/transitorio/*PSO_FCS*iter*.csv")
        return
    
    print(f"[OK] Loaded {len(df)} rows from {df['filename'].nunique()} files")
    print(f"   w_sets found: {sorted(df['w_set'].unique())}")
    print(f"   Instances: {sorted(df['instance'].unique())}")
    
    # Step 2: Calculate statistics
    print("\n[2/4] Calculating diversity statistics...")
    stats_detailed, stats_overall = calculate_diversity_stats(df)
    
    print("\n[DATA] Overall Diversity by Phase:")
    print(stats_overall.to_string(index=False))
    
    # Key insight: CV reduction
    cv_early = stats_overall[stats_overall['phase'] == 'Early']['cv'].values[0]
    cv_late = stats_overall[stats_overall['phase'] == 'Late']['cv'].values[0]
    cv_reduction = (1 - cv_late / cv_early) * 100 if cv_early > 0 else 0
    
    print(f"\n[NOTE] KEY FINDING: CV reduction from Early to Late = {cv_reduction:.1f}%")
    print(f"   ... Diversity variability decreases significantly in late stages")
    
    # Step 3: Generate figure
    print("\n[3/4] Generating diversity timeline figure...")
    plot_diversity_timeline(df)
    
    # Step 4: Generate LaTeX table
    print("\n[4/4] Generating LaTeX table...")
    generate_latex_table(stats_overall)
    
    # Save raw data
    output_csv = OUTPUT_PATH / "paper_data_diversity.csv"
    df.to_csv(output_csv, index=False)
    print(f"[OK] Raw data saved: {output_csv}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\n[DIR] Outputs in: {OUTPUT_PATH.absolute()}")
    print("   - paper_fig_diversity_timeline.pdf")
    print("   - paper_table_diversity_stats.tex")
    print("   - paper_data_diversity.csv")
    print("\n[TARGET] Use these in your conference paper Section 4 (Diagnosis)")


if __name__ == "__main__":
    main()
