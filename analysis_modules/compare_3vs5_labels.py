"""
Comparative analysis: 3 vs 5 linguistic labels in fuzzy inertia weight controllers.
Generates LNCS-formatted visualizations for publication.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import os

# LNCS formatting
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
        labels_5 = ['very low', 'low', 'medium', 'high', 'very high']
        colors_5 = ['#4C72B0', '#0072B2', '#009E73', '#D55E00', '#A63A42']  # colorblind-friendly
        
        for label, color in zip(labels_5, colors_5):
            a, b, c = ctrl5.w_mf[label]
            y = [tri(val, a, b, c) for val in x]
            ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=2.5, color=color, linewidth=1.2)
        
        ax.set_title(f'Set {w_set}: Five Labels', fontweight='bold', fontsize=10)
        ax.set_xlabel('Inertia Weight $w$', fontsize=10)
        ax.set_ylabel('Membership', fontsize=10)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(fontsize=7, loc='upper right', framealpha=0.95, ncol=1)
        ax.set_xlim([-0.05, 1.05])
        ax.set_ylim([0, 1.15])
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('FUZZY/plots/01_comparison_membership_functions.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: FUZZY/plots/01_comparison_membership_functions.png")
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
    print("✓ Saved: FUZZY/plots/02_comparison_bar_charts.png")
    plt.close()

if __name__ == '__main__':
    print("\n" + "="*130)
    print("GENERATING COMPARATIVE VISUALIZATIONS: 3 vs. 5 LINGUISTIC LABELS")
    print("Format: LNCS (Lecture Notes in Computer Science)")
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
    print("✓ VISUALIZATION GENERATION COMPLETED")
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
    """Genera gráficos comparativos de funciones de membresía."""
    
    os.makedirs('FUZZY/plots', exist_ok=True)
    sets = ['A', 'B', 'C', 'D']
    
    # Crear figura con subplots para outputs
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle('Comparación: 3 vs 5 Etiquetas Lingüísticas\nFuzzy Inertia Weight Controller (Output: w)', 
                 fontsize=14, fontweight='bold')
    
    for col_idx, w_set in enumerate(sets):
        # Instanciar controllers
        ctrl3 = FuzzyInertiaController(w_set=w_set)
        ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
        
        # === ROW 0: Output w membership functions 3 labels ===
        ax = axes[0, col_idx]
        
        x = np.linspace(ctrl3.wMin, ctrl3.wMax, 500)
        for label in ['low', 'medium', 'high']:
            a, b, c = ctrl3.w_mf[label]
            y = [tri(val, a, b, c) for val in x]
            ax.plot(x, y, 'o-', label=f'{label}', alpha=0.7, markersize=3)
        
        ax.set_title(f'Set {w_set}: 3 Etiquetas\nw ∈ [0.0, 1.0]', fontweight='bold')
        ax.set_xlabel('Inertia Weight w')
        ax.set_ylabel('Membership')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=9)
        ax.set_xlim([-0.05, 1.05])
        ax.set_ylim([0, 1.1])
        
        # === ROW 1: Output w membership functions 5 labels ===
        ax = axes[1, col_idx]
        
        x = np.linspace(ctrl5.wMin, ctrl5.wMax, 500)
        labels_5 = ['very_low', 'low', 'medium', 'high', 'very_high']
        colors_5 = ['darkblue', 'blue', 'green', 'orange', 'red']
        
        for label, color in zip(labels_5, colors_5):
            a, b, c = ctrl5.w_mf[label]
            y = [tri(val, a, b, c) for val in x]
            ax.plot(x, y, 'o-', label=f'{label}', alpha=0.7, markersize=3, color=color)
        
        ax.set_title(f'Set {w_set}: 5 Etiquetas\nw ∈ [0.0, 1.0]', fontweight='bold')
        ax.set_xlabel('Inertia Weight w')
        ax.set_ylabel('Membership')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc='upper right')
        ax.set_xlim([-0.05, 1.05])
        ax.set_ylim([0, 1.1])
    
    plt.tight_layout()
    plt.savefig('FUZZY/plots/comparison_3vs5_labels_output.png', dpi=300, bbox_inches='tight')
    print("✓ Guardado: FUZZY/plots/comparison_3vs5_labels_output.png")
    plt.close()

def test_controller_responses():
    """Compara las respuestas de los controllers con inputs específicos."""
    
    test_points = [
        (0.1, 0.1, "Baja div., temprana (exploración)"),
        (0.5, 0.1, "Media div., temprana"),
        (0.9, 0.1, "Alta div., temprana"),
        (0.1, 0.5, "Baja div., mitad"),
        (0.5, 0.5, "Media div., mitad"),
        (0.9, 0.5, "Alta div., mitad"),
        (0.1, 0.9, "Baja div., tardía"),
        (0.5, 0.9, "Media div., tardía (explotación)"),
        (0.9, 0.9, "Alta div., tardía"),
    ]
    
    results = []
    
    print("\n" + "="*120)
    print("COMPARACIÓN DE RESPUESTAS: 3 vs 5 Etiquetas Lingüísticas")
    print("="*120)
    
    for diversity, progress, description in test_points:
        print(f"\nCondición: diversity={diversity:.1f}, progress={progress:.1f} → {description}")
        print("-" * 120)
        print(f"{'Set':<5} {'3-labels w':<15} {'5-labels w':<15} {'Diferencia':<15} {'% Cambio':<15}")
        print("-" * 120)
        
        for w_set in ['A', 'B', 'C', 'D']:
            ctrl3 = FuzzyInertiaController(w_set=w_set)
            ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
            
            w3 = ctrl3.compute_w(diversity, progress)
            w5 = ctrl5.compute_w(diversity, progress)
            
            diff = w5 - w3
            pct_change = ((w5 - w3) / abs(w3) * 100) if w3 != 0 else 0.0
            
            print(f"{w_set:<5} {w3:<15.6f} {w5:<15.6f} {diff:<+15.6f} {pct_change:<+15.1f}%")
            
            results.append({
                'diversity': diversity,
                'progress': progress,
                'w_set': w_set,
                'w_3labels': w3,
                'w_5labels': w5,
                'diff': diff,
                'description': description
            })
    
    print("\n" + "="*120)
    return results

def create_comparative_plot():
    """Crea gráficos de comparación en puntos específicos."""
    
    test_points_simple = [
        (0.1, 0.1, "Baja Div.\nTemprana"),
        (0.5, 0.5, "Media Div.\nMitad"),
        (0.9, 0.9, "Alta Div.\nTardía"),
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    fig.suptitle('Comparación de w en Puntos Críticos: 3 vs 5 Etiquetas', fontweight='bold')
    
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
        ax.bar(x_pos - width/2, w3_values, width, label='3 Labels', alpha=0.8, color='steelblue')
        ax.bar(x_pos + width/2, w5_values, width, label='5 Labels', alpha=0.8, color='coral')
        
        ax.set_xlabel('Fuzzy Set')
        ax.set_ylabel('Inertia Weight w')
        ax.set_title(title)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(sets)
        ax.set_ylim([0, 1.0])
        ax.grid(axis='y', alpha=0.3)
        ax.legend()
    
    plt.tight_layout()
    plt.savefig('FUZZY/plots/comparison_3vs5_labels_bars.png', dpi=300, bbox_inches='tight')
    print("✓ Guardado: FUZZY/plots/comparison_3vs5_labels_bars.png")
    plt.close()

if __name__ == '__main__':
    print("\n" + "="*120)
    print("GENERANDO COMPARATIVAS: 3 vs 5 ETIQUETAS LINGÜÍSTICAS")
    print("="*120)
    
    os.makedirs('FUZZY/plots', exist_ok=True)
    
    # 1. Gráficos de membresías
    print("\n[1/3] Generando gráficos de funciones de membresía...")
    plot_membership_functions()
    
    # 2. Comparación de respuestas en puntos específicos
    print("\n[2/3] Comparando respuestas en puntos de prueba...")
    results = test_controller_responses()
    
    # 3. Gráficos de barras comparativos
    print("\n[3/3] Generando gráficos de barras...")
    create_comparative_plot()
    
    print("\n" + "="*120)
    print("✓ COMPARACIÓN COMPLETADA")
    print("="*120)
    print("\nGráficos generados:")
    print("  - FUZZY/plots/comparison_3vs5_labels_output.png")
    print("  - FUZZY/plots/comparison_3vs5_labels_bars.png")
    print("\nPróximos pasos:")
    print("  1. Ejecutar: python reiniciarDB.py")
    print("  2. Ejecutar: python poblarDB.py")
    print("  3. Ejecutar: python main.py")
    print("  4. Ejecutar: python analisis.py")
    print("\nEsto generará 8 configuraciones PSO_FCS (4 sets × 2 num_labels) por función")
    print("  - PSO_FCS:A,3 / PSO_FCS:A,5 / etc.")
    print("="*120 + "\n")
    """Genera gráficos comparativos de funciones de membresía."""
    
    sets = ['A', 'B', 'C', 'D']
    
    # Crear figura con subplots para inputs y outputs
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    fig.suptitle('Comparación: 3 vs 5 Etiquetas Lingüísticas\nFuzzy Inertia Weight Controller', 
                 fontsize=14, fontweight='bold')
    
    for col_idx, w_set in enumerate(sets):
        # Instanciar controllers
        ctrl3 = FuzzyInertiaController(w_set=w_set)
        ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
        
        # === ROW 0: Output w membership functions ===
        ax = axes[0, col_idx]
        
        # Plotear membresías de 3 labels
        x = np.linspace(ctrl3.wMin, ctrl3.wMax, 500)
        for label in ['low', 'medium', 'high']:
            a, b, c = ctrl3.w_mf[label]
            y = [tri(val, a, b, c) for val in x]
            ax.plot(x, y, 'o-', label=f'{label}(3)', alpha=0.6, markersize=4)
        
        ax.set_title(f'Set {w_set}: 3 Etiquetas\nw ∈ [{ctrl3.wMin}, {ctrl3.wMax}]', fontweight='bold')
        ax.set_xlabel('Inertia Weight w')
        ax.set_ylabel('Membership')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
        ax.set_xlim([ctrl3.wMin - 0.05, ctrl3.wMax + 0.05])
        
        # === ROW 1: Output w membership functions 5 labels ===
        ax = axes[1, col_idx]
        
        # Plotear membresías de 5 labels
        x = np.linspace(ctrl5.wMin, ctrl5.wMax, 500)
        labels_5 = ['very_low', 'low', 'medium', 'high', 'very_high']
        colors_5 = ['blue', 'cyan', 'green', 'orange', 'red']
        
        for label, color in zip(labels_5, colors_5):
            a, b, c = ctrl5.w_mf[label]
            y = [tri(val, a, b, c) for val in x]
            ax.plot(x, y, 'o-', label=f'{label}(5)', alpha=0.6, markersize=4, color=color)
        
        ax.set_title(f'Set {w_set}: 5 Etiquetas\nw ∈ [{ctrl5.wMin}, {ctrl5.wMax}]', fontweight='bold')
        ax.set_xlabel('Inertia Weight w')
        ax.set_ylabel('Membership')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc='upper right')
        ax.set_xlim([ctrl5.wMin - 0.05, ctrl5.wMax + 0.05])
    
    plt.tight_layout()
    plt.savefig('FUZZY/plots/comparison_3vs5_labels_output.png', dpi=300, bbox_inches='tight')
    print("✓ Guardado: FUZZY/plots/comparison_3vs5_labels_output.png")
    plt.close()

def test_controller_responses():
    """Compara las respuestas de los controllers con inputs específicos."""
    
    test_points = [
        (0.1, 0.1, "Baja diversidad, iteración temprana (exploración urgente)"),
        (0.5, 0.1, "Media diversidad, iteración temprana"),
        (0.9, 0.1, "Alta diversidad, iteración temprana"),
        (0.1, 0.5, "Baja diversidad, mitad de iteraciones"),
        (0.5, 0.5, "Media diversidad, mitad"),
        (0.9, 0.5, "Alta diversidad, mitad"),
        (0.1, 0.9, "Baja diversidad, iteración tardía"),
        (0.5, 0.9, "Media diversidad, iteración tardía (explotación)"),
        (0.9, 0.9, "Alta diversidad, iteración tardía"),
    ]
    
    results = []
    
    print("\n" + "="*100)
    print("COMPARACIÓN DE RESPUESTAS: 3 vs 5 Etiquetas")
    print("="*100)
    
    for diversity, progress, description in test_points:
        print(f"\nCondición: d={diversity:.1f}, t={progress:.1f} → {description}")
        print("-" * 100)
        
        for w_set in ['A', 'B', 'C', 'D']:
            ctrl3 = FuzzyInertiaController(w_set=w_set)
            ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
            
            w3 = ctrl3.compute_w(diversity, progress)
            w5 = ctrl5.compute_w(diversity, progress)
            
            diff = w5 - w3
            pct_change = ((w5 - w3) / w3 * 100) if w3 != 0 else float('nan')
            
            print(f"  Set {w_set:1s}:  3-labels: w={w3:.4f}  |  5-labels: w={w5:.4f}  |  Δ={diff:+.4f} ({pct_change:+.1f}%)")
            
            results.append({
                'diversity': diversity,
                'progress': progress,
                'w_set': w_set,
                'w_3labels': w3,
                'w_5labels': w5,
                'diff': diff,
                'description': description
            })
    
    print("\n" + "="*100)
    return results

def create_3d_comparison():
    """Crea superficies 3D comparativas para Set A."""
    
    from mpl_toolkits.mplot3d import Axes3D
    
    div_range = np.linspace(0.01, 0.99, 50)
    prog_range = np.linspace(0.01, 0.99, 50)
    DIV, PROG = np.meshgrid(div_range, prog_range)
    
    ctrl3 = FuzzyInertiaController(w_set='A')
    ctrl5 = FuzzyInertiaController_5labels(w_set='A')
    
    W3 = np.zeros_like(DIV)
    W5 = np.zeros_like(DIV)
    
    for i in range(DIV.shape[0]):
        for j in range(DIV.shape[1]):
            W3[i, j] = ctrl3.compute_w(DIV[i, j], PROG[i, j])
            W5[i, j] = ctrl5.compute_w(DIV[i, j], PROG[i, j])
    
    fig = plt.figure(figsize=(14, 5))
    
    # 3D Surface para 3 labels
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.plot_surface(DIV, PROG, W3, cmap='viridis', alpha=0.8)
    ax1.set_xlabel('Diversity Ratio')
    ax1.set_ylabel('Progress (iter/maxIter)')
    ax1.set_zlabel('Inertia Weight w')
    ax1.set_title('Set A: 3 Etiquetas\nw ∈ [0.0, 1.0]')
    
    # 3D Surface para 5 labels
    ax2 = fig.add_subplot(132, projection='3d')
    ax2.plot_surface(DIV, PROG, W5, cmap='viridis', alpha=0.8)
    ax2.set_xlabel('Diversity Ratio')
    ax2.set_ylabel('Progress (iter/maxIter)')
    ax2.set_zlabel('Inertia Weight w')
    ax2.set_title('Set A: 5 Etiquetas\nw ∈ [0.0, 1.0]')
    
    # Diferencia
    ax3 = fig.add_subplot(133)
    diff = W5 - W3
    contour = ax3.contourf(DIV, PROG, diff, levels=20, cmap='RdBu_r')
    ax3.set_xlabel('Diversity Ratio')
    ax3.set_ylabel('Progress (iter/maxIter)')
    ax3.set_title('Diferencia: 5-labels minus 3-labels')
    plt.colorbar(contour, ax=ax3)
    
    plt.tight_layout()
    plt.savefig('FUZZY/plots/comparison_3d_surfaces.png', dpi=300, bbox_inches='tight')
    print("✓ Guardado: FUZZY/plots/comparison_3d_surfaces.png")
    plt.close()

if __name__ == '__main__':
    print("\n" + "="*100)
    print("GENERANDO COMPARATIVAS: 3 vs 5 ETIQUETAS LINGÜÍSTICAS")
    print("="*100)
    
    # Crear directorio de plots si no existe
    import os
    os.makedirs('FUZZY/plots', exist_ok=True)
    
    # 1. Gráficos de membresías
    print("\n[1/3] Generando gráficos de funciones de membresía...")
    plot_membership_functions()
    
    # 2. Comparación de respuestas en puntos específicos
    print("\n[2/3] Comparando respuestas en puntos de prueba...")
    results = test_controller_responses()
    
    # 3. Superficies 3D
    print("\n[3/3] Generando superficies 3D comparativas...")
    create_3d_comparison()
    
    print("\n" + "="*100)
    print("✓ COMPARACIÓN COMPLETADA")
    print("="*100)
    print("\nPróximos pasos:")
    print("1. Ejecutar: python reiniciarDB.py")
    print("2. Ejecutar: python poblarDB.py")
    print("3. Ejecutar: python main.py")
    print("4. Ejecutar: python analisis.py")
    print("\nEsto generará 8 configuraciones PSO_FCS (4 sets × 2 num_labels) por función")
    print("="*100 + "\n")
