"""
Rule Activation Frequency Analysis for Conference Paper
Diagnoses which fuzzy rules dominate during PSO execution

Output:
- paper_fig_rule_activation_heatmap.pdf: 3×3 heatmap of activation %
- paper_table_rule_frequency.tex: LaTeX table with statistics
- paper_data_rules.csv: Detailed activation logs

Author: Analysis Module for Fuzzy PSO Paper
Date: January 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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

# Fuzzy membership function thresholds (from fuzzy_controller_w.py)
DIV_THRESHOLDS = {
    'low': (0.0, 0.2, 0.4),
    'medium': (0.3, 0.5, 0.7),
    'high': (0.6, 0.8, 1.0)
}

IT_THRESHOLDS = {
    'early': (0.0, 0.2, 0.4),
    'mid': (0.3, 0.5, 0.7),
    'late': (0.6, 0.8, 1.0)
}

# Rule base (from fuzzy_controller_w.py lines 55-64)
RULES = {
    ('low', 'early'): 'medium',
    ('medium', 'early'): 'high',
    ('high', 'early'): 'high',
    ('low', 'mid'): 'low',
    ('medium', 'mid'): 'medium',
    ('high', 'mid'): 'high',
    ('low', 'late'): 'low',
    ('medium', 'late'): 'low',
    ('high', 'late'): 'low'
}


def tri_membership(x, a, b, c):
    """Triangular membership function (shoulder-enabled)."""
    x = float(x)
    if a == b and x <= b:
        return 1.0
    if b == c and x >= b:
        return 1.0
    if x <= a or x >= c:
        return 0.0
    if a < x < b:
        return (x - a) / (b - a + 1e-12)
    if b < x < c:
        return (c - x) / (c - b + 1e-12)
    return 1.0 if x == b else 0.0


def classify_input(diversity, progress):
    """Classify inputs and compute fuzzy membership degrees."""
    
    # Diversity classification
    mu_div = {label: tri_membership(diversity, *params) 
              for label, params in DIV_THRESHOLDS.items()}
    
    # Progress classification
    mu_it = {label: tri_membership(progress, *params)
             for label, params in IT_THRESHOLDS.items()}
    
    # Find dominant labels (max membership)
    div_label = max(mu_div, key=mu_div.get)
    it_label = max(mu_it, key=mu_it.get)
    
    # Calculate firing strength
    firing_strength = min(mu_div[div_label], mu_it[it_label])
    
    return div_label, it_label, firing_strength, RULES[(div_label, it_label)]


def load_and_classify_data():
    """Load experiment data and classify each iteration's rule activation."""
    
    files = list(TRANSITORIO_PATH.glob("w_timeseries*.csv"))
    
    if not files:
        print(f"[WARN] No files found in {TRANSITORIO_PATH}")
        return None
    
    print(f"[INFO] Found {len(files)} experiment files")
    
    all_classifications = []
    
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
                mh_data = df[df['MH'] == mh_str]
                
                if ':' not in mh_str:
                    w_set = 'baseline'
                else:
                    w_set = mh_str.split(':')[1].upper()
                
                # Classify each iteration
                for _, row in mh_data.iterrows():
                    diversity = row.get('diversity', 0)
                    progress = row.get('progress', row['iter'] / 500.0)  # Assuming max_iter=500
                    
                    div_label, it_label, firing, w_output = classify_input(diversity, progress)
                    
                    all_classifications.append({
                        'instance': instance,
                        'w_set': w_set,
                        'iter': row['iter'],
                        'diversity': diversity,
                        'progress': progress,
                        'div_label': div_label,
                        'it_label': it_label,
                        'rule': f"{div_label}+{it_label}",
                        'w_output': w_output,
                        'firing_strength': firing
                    })
        
        except Exception as e:
            print(f"[WARN] Error processing {f.name}: {e}")
    
    if not all_classifications:
        return None
    
    return pd.DataFrame(all_classifications)


def calculate_activation_frequencies(df):
    """Calculate rule activation frequencies."""
    
    # Count activations per rule
    rule_counts = df['rule'].value_counts()
    total = len(df)
    
    # Create 3×3 matrix
    div_labels = ['low', 'medium', 'high']
    it_labels = ['early', 'mid', 'late']
    
    matrix = np.zeros((3, 3))
    
    for i, div_label in enumerate(div_labels):
        for j, it_label in enumerate(it_labels):
            rule = f"{div_label}+{it_label}"
            count = rule_counts.get(rule, 0)
            matrix[i, j] = (count / total) * 100  # Percentage
    
    return matrix, rule_counts, total


def plot_activation_heatmap(matrix):
    """Generate Figure 2: Rule activation frequency heatmap."""
    
    fig, ax = plt.subplots(figsize=(6, 4.5))
    
    div_labels = ['Low', 'Medium', 'High']
    it_labels = ['Early', 'Mid', 'Late']
    
    # Create heatmap
    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=30)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Activation Frequency (%)', rotation=270, labelpad=20, fontsize=9)
    
    # Set ticks
    ax.set_xticks(np.arange(3))
    ax.set_yticks(np.arange(3))
    ax.set_xticklabels(it_labels, fontsize=9)
    ax.set_yticklabels(div_labels, fontsize=9)
    
    # Labels
    ax.set_xlabel('Iteration Progress', fontsize=10, fontweight='bold')
    ax.set_ylabel('Diversity', fontsize=10, fontweight='bold')
    ax.set_title('Fuzzy Rule Activation Frequency', fontsize=11, fontweight='bold', pad=10)
    
    # Add text annotations with values and w_output
    for i in range(3):
        for j in range(3):
            div_label = ['low', 'medium', 'high'][i]
            it_label = ['early', 'mid', 'late'][j]
            w_output = RULES[(div_label, it_label)]
            
            text = f"{matrix[i, j]:.1f}%\n>>> w:{w_output}"
            color = 'white' if matrix[i, j] > 15 else 'black'
            ax.text(j, i, text, ha='center', va='center', 
                   color=color, fontsize=8, fontweight='bold')
    
    plt.tight_layout()
    
    output_file = OUTPUT_PATH / "paper_fig_rule_activation_heatmap.pdf"
    plt.savefig(output_file, bbox_inches='tight')
    print(f"[OK] Figure saved: {output_file}")
    
    plt.savefig(OUTPUT_PATH / "paper_fig_rule_activation_heatmap.png", bbox_inches='tight')
    plt.close()


def generate_latex_table(rule_counts, total):
    """Generate LaTeX table of rule activation frequencies."""
    
    latex = r"""\begin{table}[t]
\centering
\caption{Fuzzy rule activation frequency during PSO execution}
\label{tab:rule_activation}
\small
\begin{tabular}{llccc}
\hline
\textbf{Diversity} & \textbf{Progress} & \textbf{w Output} & \textbf{Count} & \textbf{\%} \\
\hline
"""
    
    div_labels = ['low', 'medium', 'high']
    it_labels = ['early', 'mid', 'late']
    
    for div_label in div_labels:
        for it_label in it_labels:
            rule = f"{div_label}+{it_label}"
            w_output = RULES[(div_label, it_label)]
            count = rule_counts.get(rule, 0)
            percentage = (count / total) * 100
            
            latex += f"{div_label.capitalize()} & {it_label.capitalize()} & {w_output} & {count} & {percentage:.1f}\\\\\n"
    
    latex += r"""\hline
\textbf{Total} & & & """ + f"{total}" + r""" & 100.0\\
\hline
\end{tabular}
\end{table}
"""
    
    output_file = OUTPUT_PATH / "paper_table_rule_frequency.tex"
    with open(output_file, 'w') as f:
        f.write(latex)
    
    print(f"[OK] LaTeX table saved: {output_file}")


def main():
    """Main execution pipeline."""
    
    print("=" * 60)
    print("RULE ACTIVATION FREQUENCY ANALYSIS")
    print("=" * 60)
    
    # Step 1: Load and classify data
    print("\n[1/4] Loading and classifying experiment data...")
    df = load_and_classify_data()
    
    if df is None or df.empty:
        print("[ERROR] No data found. Run experiments first.")
        return
    
    print(f"[OK] Classified {len(df)} iterations from {df['instance'].nunique()} instances")
    
    # Step 2: Calculate frequencies
    print("\n[2/4] Calculating rule activation frequencies...")
    matrix, rule_counts, total = calculate_activation_frequencies(df)
    
    print("\n[DATA] Rule Activation Summary:")
    print(f"   Total iterations analyzed: {total}")
    print("\n   Top 5 most activated rules:")
    for rule, count in rule_counts.head(5).items():
        percentage = (count / total) * 100
        div, it = rule.split('+')
        w_out = RULES[(div, it)]
        print(f"   - {rule:15s} >>> w={w_out:6s} : {count:6d} ({percentage:5.1f}%)")
    
    # Key insight: Imbalance
    w_output_counts = df['w_output'].value_counts()
    print("\n[NOTE] KEY FINDING: w Output Distribution")
    for w_label, count in w_output_counts.items():
        percentage = (count / total) * 100
        print(f"   - w={w_label:6s}: {percentage:5.1f}%")
    
    imbalance_ratio = w_output_counts.max() / w_output_counts.min()
    print(f"   - Imbalance ratio: {imbalance_ratio:.2f}:1")
    print(f"   ... System biased towards certain w outputs")
    
    # Step 3: Generate heatmap
    print("\n[3/4] Generating rule activation heatmap...")
    plot_activation_heatmap(matrix)
    
    # Step 4: Generate LaTeX table
    print("\n[4/4] Generating LaTeX table...")
    generate_latex_table(rule_counts, total)
    
    # Save raw data
    output_csv = OUTPUT_PATH / "paper_data_rules.csv"
    df.to_csv(output_csv, index=False)
    print(f"[OK] Raw data saved: {output_csv}")
    
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"\n[DIR] Outputs in: {OUTPUT_PATH.absolute()}")
    print("   - paper_fig_rule_activation_heatmap.pdf")
    print("   - paper_table_rule_frequency.tex")
    print("   - paper_data_rules.csv")


if __name__ == "__main__":
    main()
