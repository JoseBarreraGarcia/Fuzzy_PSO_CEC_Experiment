"""
Comparative analysis: 3 vs 5 linguistic labels in fuzzy inertia weight controllers.
Generates LNCS-formatted visualizations for publication.

Language: English
Format: LNCS (Lecture Notes in Computer Science)
Font: Times New Roman, 10-11pt
DPI: 300
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os

# LNCS formatting configuration
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 10
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 11
plt.rcParams['lines.linewidth'] = 1.2

from FUZZY.fuzzy_controller_w import FuzzyInertiaController, tri
from FUZZY.fuzzy_controller_w_5labels import FuzzyInertiaController_5labels

def plot_membership_functions():
    """Generate membership function visualizations for 3 and 5 labels (LNCS format)."""
    
    os.makedirs('FUZZY/plots', exist_ok=True)
    sets = ['A', 'B', 'C', 'D']
    
    # Create figure with subplots for outputs
    fig, axes = plt.subplots(2, 4, figsize=(7.5, 5.5))
    fig.suptitle('Comparison of Inertia Weight Membership Functions: 3 vs. 5 Linguistic Labels', 
                 fontsize=11, fontweight='bold', y=0.98)
    
    for col_idx, w_set in enumerate(sets):
        # Instantiate controllers
        ctrl3 = FuzzyInertiaController(w_set=w_set)
        ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
        
        # === ROW 0: Output w membership functions 3 labels ===
        ax = axes[0, col_idx]
        
        x = np.linspace(ctrl3.wMin, ctrl3.wMax, 500)
        colors_3 = ['#0072B2', '#009E73', '#D55E00']  # colorblind-friendly
        for label, color in zip(['low', 'medium', 'high'], colors_3):
            a, b, c = ctrl3.w_mf[label]
            y = [tri(val, a, b, c) for val in x]
            ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=2.5, color=color, linewidth=1.2)
        
        ax.set_title(f'Set {w_set}: Three Labels', fontweight='bold', fontsize=10)
        ax.set_xlabel('Inertia Weight $w$', fontsize=10)
        ax.set_ylabel('Membership', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(fontsize=8, loc='upper right', framealpha=0.95)
        ax.set_xlim([-0.05, 1.05])
        ax.set_ylim([0, 1.15])
        
        # === ROW 1: Output w membership functions 5 labels ===
        ax = axes[1, col_idx]
        
        x = np.linspace(ctrl5.wMin, ctrl5.wMax, 500)
        labels_5 = ['very_low', 'low', 'medium', 'high', 'very_high']
        colors_5 = ['#4C72B0', '#0072B2', '#009E73', '#D55E00', '#A63A42']  # colorblind-friendly
        labels_display = ['very low', 'low', 'medium', 'high', 'very high']
        
        for label_key, label_display, color in zip(labels_5, labels_display, colors_5):
            a, b, c = ctrl5.w_mf[label_key]
            y = [tri(val, a, b, c) for val in x]
            ax.plot(x, y, 'o-', label=label_display, alpha=0.8, markersize=2.5, color=color, linewidth=1.2)
        
        ax.set_title(f'Set {w_set}: Five Labels', fontweight='bold', fontsize=10)
        ax.set_xlabel('Inertia Weight $w$', fontsize=10)
        ax.set_ylabel('Membership', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(fontsize=7, loc='upper right', framealpha=0.95, ncol=1)
        ax.set_xlim([-0.05, 1.05])
        ax.set_ylim([0, 1.15])
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('FUZZY/plots/01_comparison_membership_functions.png', dpi=300, bbox_inches='tight')
    print("[OK] Saved: FUZZY/plots/01_comparison_membership_functions.png")
    plt.close()

def test_controller_responses():
    """Compare controller responses at specific input points."""
    
    test_points = [
        (0.1, 0.1, "Low diversity, early iteration (urgent exploration)"),
        (0.5, 0.1, "Medium diversity, early iteration"),
        (0.9, 0.1, "High diversity, early iteration"),
        (0.1, 0.5, "Low diversity, mid-iteration"),
        (0.5, 0.5, "Medium diversity, mid-iteration"),
        (0.9, 0.5, "High diversity, mid-iteration"),
        (0.1, 0.9, "Low diversity, late iteration"),
        (0.5, 0.9, "Medium diversity, late iteration (exploitation)"),
        (0.9, 0.9, "High diversity, late iteration"),
    ]
    
    results = []
    
    print("\n" + "="*130)
    print("CONTROLLER RESPONSE COMPARISON: 3 vs. 5 Linguistic Labels")
    print("="*130)
    
    for diversity, progress, description in test_points:
        print(f"\nCondition: diversity={diversity:.1f}, progress={progress:.1f}")
        print(f"Description: {description}")
        print("-" * 130)
        print(f"{'Set':<5} {'3-label $w$':<18} {'5-label $w$':<18} {'Difference':<18} {'% Change':<18}")
        print("-" * 130)
        
        for w_set in ['A', 'B', 'C', 'D']:
            ctrl3 = FuzzyInertiaController(w_set=w_set)
            ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
            
            w3 = ctrl3.compute_w(diversity, progress)
            w5 = ctrl5.compute_w(diversity, progress)
            
            diff = w5 - w3
            pct_change = ((w5 - w3) / abs(w3) * 100) if w3 != 0 else 0.0
            
            print(f"{w_set:<5} {w3:<18.6f} {w5:<18.6f} {diff:<+18.6f} {pct_change:<+18.1f}%")
            
            results.append({
                'diversity': diversity,
                'progress': progress,
                'w_set': w_set,
                'w_3labels': w3,
                'w_5labels': w5,
                'diff': diff,
                'description': description
            })
    
    print("\n" + "="*130)
    return results

def create_comparative_plot():
    """Create bar charts comparing inertia weights at critical points (LNCS format)."""
    
    test_points_simple = [
        (0.1, 0.1, "Low Diversity\n(Early)"),
        (0.5, 0.5, "Medium Diversity\n(Mid)"),
        (0.9, 0.9, "High Diversity\n(Late)"),
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(7.5, 2.8))
    fig.suptitle('Inertia Weight Comparison at Critical Operating Points', 
                 fontsize=11, fontweight='bold', y=0.98)
    
    for idx, (diversity, progress, title) in enumerate(test_points_simple):
        ax = axes[idx]
        
        sets = ['A', 'B', 'C', 'D']
        x_pos = np.arange(len(sets))
        w3_values = []
        w5_values = []
        
        for w_set in sets:
            ctrl3 = FuzzyInertiaController(w_set=w_set)
            ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
            w3_values.append(ctrl3.compute_w(diversity, progress))
            w5_values.append(ctrl5.compute_w(diversity, progress))
        
        width = 0.35
        bars1 = ax.bar(x_pos - width/2, w3_values, width, label='3 Labels', 
                       alpha=0.85, color='#0072B2', edgecolor='black', linewidth=0.8)
        bars2 = ax.bar(x_pos + width/2, w5_values, width, label='5 Labels', 
                       alpha=0.85, color='#D55E00', edgecolor='black', linewidth=0.8)
        
        ax.set_xlabel('Fuzzy Set', fontsize=10)
        ax.set_ylabel('Inertia Weight $w$', fontsize=10)
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(sets)
        ax.set_ylim([0, 1.0])
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(fontsize=9, loc='upper right', framealpha=0.95)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('FUZZY/plots/02_comparison_bar_charts.png', dpi=300, bbox_inches='tight')
    print("[OK] Saved: FUZZY/plots/02_comparison_bar_charts.png")
    plt.close()

if __name__ == '__main__':
    print("\n" + "="*130)
    print("GENERATING COMPARATIVE VISUALIZATIONS: 3 vs. 5 LINGUISTIC LABELS")
    print("Format: LNCS (Lecture Notes in Computer Science)")
    print("Language: English | Font: Times New Roman | DPI: 300")
    print("="*130)
    
    os.makedirs('FUZZY/plots', exist_ok=True)
    
    # 1. Membership functions plots
    print("\n[1/3] Generating membership function visualizations...")
    plot_membership_functions()
    
    # 2. Response comparison at test points
    print("\n[2/3] Comparing controller responses at test points...")
    results = test_controller_responses()
    
    # 3. Bar chart comparisons
    print("\n[3/3] Generating comparative bar charts...")
    create_comparative_plot()
    
    print("\n" + "="*130)
    print("VISUALIZATION GENERATION COMPLETED")
    print("="*130)
    print("\nGenerated figures (LNCS format, 300 DPI, English):")
    print("  - FUZZY/plots/01_comparison_membership_functions.png")
    print("  - FUZZY/plots/02_comparison_bar_charts.png")
    print("\nNext steps:")
    print("  1. Run: python reiniciarDB.py")
    print("  2. Run: python poblarDB.py")
    print("  3. Run: python main.py")
    print("  4. Run: python analisis.py")
    print("\nThis will generate 8 PSO_FCS configurations (4 sets × 2 label counts)")
    print("="*130 + "\n")
