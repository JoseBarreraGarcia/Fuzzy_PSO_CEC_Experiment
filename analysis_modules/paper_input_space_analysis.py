"""
Input Space Coverage Analysis for Conference Paper
Visualizes which regions of (diversity, progress) space are explored

Output:
- paper_fig_input_space_coverage.pdf: Scatter plot with rule regions
- paper_table_quadrant_coverage.tex: Coverage statistics by region
- paper_data_inputspace.csv: All (diversity, progress) points

Author: Analysis Module for Fuzzy PSO Paper
Date: January 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path
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

# Paths
TRANSITORIO_PATH = Path("Resultados/resumen/SCP")
OUTPUT_PATH = Path("Resultados/paper_outputs")
OUTPUT_PATH.mkdir(exist_ok=True, parents=True)


def load_input_space_data():
    """Load diversity and progress data from all experiments."""
    
    files = list(TRANSITORIO_PATH.glob("w_timeseries*.csv"))
    
    if not files:
        print(f"[WARN] No files found in {TRANSITORIO_PATH}")
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
            parts = f.stem.split('_')
            instance = parts[2]  # SCP_41 -> 41
            
            # Process each MH in the file separately
            for mh_str in df['MH'].unique():
                mh_data = df[df['MH'] == mh_str].copy()
                
                if ':' not in mh_str:
                    w_set = 'baseline'
                else:
                    w_set = mh_str.split(':')[1].upper()
                
                mh_data['instance'] = instance
                mh_data['w_set'] = w_set
                if 'progress' not in mh_data.columns:
                    mh_data['progress'] = mh_data['iter'] / 500.0  # Assuming max_iter=500
                
                all_data.append(mh_data[['instance', 'w_set', 'iter', 'diversity', 'progress']])
        
        except Exception as e:
            print(f"[WARN] Error loading {f.name}: {e}")
    
    if not all_data:
        return None
    
    return pd.concat(all_data, ignore_index=True)


def classify_region(diversity, progress):
    """Classify (diversity, progress) into fuzzy rule region."""
    
    # Simple classification based on MF centers
    if diversity < 0.4:
        div_label = 'low'
    elif diversity < 0.7:
        div_label = 'medium'
    else:
        div_label = 'high'
    
    if progress < 0.4:
        it_label = 'early'
    elif progress < 0.7:
        it_label = 'mid'
    else:
        it_label = 'late'
    
    return f"{div_label}+{it_label}"


def calculate_coverage_statistics(df):
    """Calculate coverage statistics for each rule region."""
    
    # Classify all points
    df['region'] = df.apply(lambda row: classify_region(row['diversity'], row['progress']), axis=1)
    
    # Count points per region
    region_counts = df['region'].value_counts()
    total = len(df)
    
    coverage_stats = []
    for region, count in region_counts.items():
        percentage = (count / total) * 100
        coverage_stats.append({
            'region': region,
            'count': count,
            'percentage': percentage
        })
    
    return pd.DataFrame(coverage_stats).sort_values('percentage', ascending=False)


def plot_input_space_coverage(df):
    """Generate Figure 3: Input space coverage with rule regions."""
    
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # Define rule region boundaries
    div_boundaries = [0.4, 0.7]
    it_boundaries = [0.4, 0.7]
    
    # Draw grid for rule regions
    for div_b in div_boundaries:
        ax.axhline(div_b, color='gray', linestyle='--', alpha=0.4, linewidth=1)
    for it_b in it_boundaries:
        ax.axvline(it_b, color='gray', linestyle='--', alpha=0.4, linewidth=1)
    
    # Add region labels
    regions = [
        (0.2, 0.2, 'low+early'),
        (0.5, 0.2, 'low+mid'),
        (0.85, 0.2, 'low+late'),
        (0.2, 0.55, 'medium+early'),
        (0.5, 0.55, 'medium+mid'),
        (0.85, 0.55, 'medium+late'),
        (0.2, 0.85, 'high+early'),
        (0.5, 0.85, 'high+mid'),
        (0.85, 0.85, 'high+late'),
    ]
    
    for x, y, label in regions:
        ax.text(x, y, label.replace('+', '\n'), 
               ha='center', va='center', fontsize=7, 
               alpha=0.3, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.5))
    
    # Sample points for visualization (too many points = slow rendering)
    sample_size = min(5000, len(df))
    df_sample = df.sample(n=sample_size, random_state=42)
    
    # Create scatter plot colored by iteration
    scatter = ax.scatter(df_sample['progress'], df_sample['diversity'],
                        c=df_sample['iter'], cmap='viridis', 
                        alpha=0.3, s=10, edgecolors='none')
    
    # Add colorbar
    cbar = plt.colorbar(scatter, ax=ax)
    cbar.set_label('Iteration', rotation=270, labelpad=20, fontsize=9)
    
    # Create density contours
    from scipy.stats import gaussian_kde
    try:
        xy = np.vstack([df_sample['progress'], df_sample['diversity']])
        z = gaussian_kde(xy)(xy)
        
        # Sort by density for proper layering
        idx = z.argsort()
        x, y, z = df_sample['progress'].values[idx], df_sample['diversity'].values[idx], z[idx]
        
        ax.scatter(x, y, c=z, s=15, cmap='Greys', alpha=0.1, edgecolors='none')
    except:
        pass  # Skip if KDE fails
    
    # Styling
    ax.set_xlabel('Iteration Progress', fontsize=10, fontweight='bold')
    ax.set_ylabel('Diversity Ratio', fontsize=10, fontweight='bold')
    ax.set_title('Input Space Coverage During PSO Execution', 
                fontsize=11, fontweight='bold', pad=10)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.grid(True, alpha=0.2, linewidth=0.5)
    
    plt.tight_layout()
    
    output_file = OUTPUT_PATH / "paper_fig_input_space_coverage.pdf"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"[OK] Figure saved: {output_file}")
    
    plt.savefig(OUTPUT_PATH / "paper_fig_input_space_coverage.png", bbox_inches='tight')
    plt.close()


def generate_latex_table(coverage_stats):
    """Generate LaTeX table of coverage statistics."""
    
    latex = r"""\begin{table}[t]
\centering
\caption{Input space coverage by fuzzy rule region}
\label{tab:input_coverage}
\begin{tabular}{lcc}
\hline
\textbf{Rule Region} & \textbf{Iterations} & \textbf{Coverage (\%)} \\
\hline
"""
    
    for _, row in coverage_stats.iterrows():
        region = row['region'].replace('+', ' + ')
        count = int(row['count'])
        percentage = row['percentage']
        latex += f"{region} & {count:,} & {percentage:.1f} \\\\\n"
    
    total = coverage_stats['count'].sum()
    latex += r"""\hline
\textbf{Total} & """ + f"{total:,}" + r""" & 100.0 \\
\hline
\end{tabular}
\end{table}
"""
    
    output_file = OUTPUT_PATH / "paper_table_quadrant_coverage.tex"
    with open(output_file, 'w') as f:
        f.write(latex)
    
    print(f"[OK] LaTeX table saved: {output_file}")


def main():
    """Main execution pipeline."""
    
    print("=" * 60)
    print("INPUT SPACE COVERAGE ANALYSIS")
    print("=" * 60)
    
    # Step 1: Load data
    print("\n[1/4] Loading input space data...")
    df = load_input_space_data()
    
    if df is None or df.empty:
        print("[ERROR] No data found. Run experiments first.")
        return
    
    print(f"[OK] Loaded {len(df)} (diversity, progress) points")
    print(f"   From {df['instance'].nunique()} instances")
    print(f"   w_sets: {sorted(df['w_set'].unique())}")
    
    # Step 2: Calculate coverage statistics
    print("\n[2/4] Calculating coverage statistics...")
    coverage_stats = calculate_coverage_statistics(df)
    
    print("\n[DATA] Input Space Coverage:")
    print(coverage_stats.to_string(index=False))
    
    # Key insights
    top_region = coverage_stats.iloc[0]
    top3_coverage = coverage_stats.head(3)['percentage'].sum()
    
    print(f"\n[NOTE] KEY FINDINGS:")
    print(f"   - Most visited region: {top_region['region']} ({top_region['percentage']:.1f}%)")
    print(f"   - Top 3 regions cover: {top3_coverage:.1f}% of execution")
    print(f"   - {len(coverage_stats)} out of 9 regions visited")
    
    if len(coverage_stats) < 9:
        missing = 9 - len(coverage_stats)
        print(f"   [WARN] {missing} regions never visited (0% coverage)")
    
    # Step 3: Generate figure
    print("\n[3/4] Generating input space coverage plot...")
    plot_input_space_coverage(df)
    
    # Step 4: Generate LaTeX table
    print("\n[4/4] Generating LaTeX table...")
    generate_latex_table(coverage_stats)
    
    # Save raw data
    output_csv = OUTPUT_PATH / "paper_data_inputspace.csv"
    df.to_csv(output_csv, index=False)
    print(f"[OK] Raw data saved: {output_csv}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\n[DIR] Outputs in: {OUTPUT_PATH.absolute()}")
    print("   - paper_fig_input_space_coverage.pdf")
    print("   - paper_table_quadrant_coverage.tex")
    print("   - paper_data_inputspace.csv")


if __name__ == "__main__":
    main()
