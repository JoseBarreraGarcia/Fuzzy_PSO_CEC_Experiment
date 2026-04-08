"""
Fuzzy Set Visualization Module

Genera gráficos de las funciones de membresía (fuzzy sets) para documentación y reportes.
Visualiza:
  - Entrada 1: Diversity (low, medium, high)
  - Entrada 2: Iteration Progress (early, mid, late)
  - Salida: Inertia Weight w (low, medium, high) para cada w_set (A, B, C, D...)

Se guarda en FUZZY/plots/
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from mpl_toolkits.mplot3d import Axes3D

# Ensure the parent directory is in the path so imports work from anywhere
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fuzzy_controller_w import FuzzyInertiaController, tri

# Fix encoding issues in Windows
if sys.platform == 'win32':
    import matplotlib
    matplotlib.rcParams['axes.unicode_minus'] = False
    # Use a PDF-friendly backend on Windows
    try:
        mpl.use('Agg')
    except:
        pass

# LNCS style configuration
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.size'] = 10
mpl.rcParams['axes.labelsize'] = 11
mpl.rcParams['axes.titlesize'] = 12
# Ensure we don't use problematic Unicode characters
mpl.rcParams['mathtext.default'] = 'regular'


def ensure_plots_directory():
    """Create FUZZY/plots directory if it doesn't exist."""
    plots_dir = './FUZZY/plots'
    os.makedirs(plots_dir, exist_ok=True)
    return plots_dir


def plot_fuzzy_input_diversity():
    """
    Plot fuzzy sets for Diversity input (both 3 and 5 labels).
    Gets membership functions dynamically from FuzzyInertiaController.
    Returns: dict with '3labels' and '5labels' paths
    """
    plots_dir = ensure_plots_directory()
    results = {}
    
    # ===== 3-LABEL VERSION =====
    try:
        controller3 = FuzzyInertiaController(w_set='A')
        div_mf = controller3.div_mf
        
        diversity = np.linspace(0, 1, 200)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = {'low': '#1f77b4', 'medium': '#ff7f0e', 'high': '#2ca02c'}
        
        for label, (a, b, c) in div_mf.items():
            mu = [tri(d, a, b, c) for d in diversity]
            ax.plot(diversity, mu, label=f'{label} ({a:.1f}, {b:.1f}, {c:.1f})', 
                    linewidth=2.5, color=colors[label])
            ax.fill_between(diversity, mu, alpha=0.2, color=colors[label])
        
        ax.set_xlabel('Diversity Ratio (0=convergence, 1=exploration)', fontsize=11)
        ax.set_ylabel('Membership Degree', fontsize=11)
        ax.set_title('Fuzzy Input Sets: Diversity (3 Labels)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=10)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
        
        plt.tight_layout()
        output_path_3 = os.path.join(plots_dir, '01_fuzzy_input_diversity_3labels.png')
        plt.savefig(output_path_3, dpi=300, bbox_inches='tight', format='png')
        plt.close(fig)
        results['3labels'] = output_path_3
    except Exception as e:
        print(f"[WARN] Failed to generate 3-label diversity plot: {e}")
        results['3labels'] = None
    
    # ===== 5-LABEL VERSION =====
    try:
        from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
        controller5 = FuzzyInertiaController_5labels(w_set='A')
        div_mf = controller5.div_mf
        
        diversity = np.linspace(0, 1, 200)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors_5 = {'very_low': '#0072B2', 'low': '#1f77b4', 'medium': '#ff7f0e', 
                    'high': '#2ca02c', 'very_high': '#d62728'}
        
        for label, (a, b, c) in div_mf.items():
            mu = [tri(d, a, b, c) for d in diversity]
            ax.plot(diversity, mu, label=f'{label} ({a:.1f}, {b:.1f}, {c:.1f})', 
                    linewidth=2.5, color=colors_5[label])
            ax.fill_between(diversity, mu, alpha=0.2, color=colors_5[label])
        
        ax.set_xlabel('Diversity Ratio (0=convergence, 1=exploration)', fontsize=11)
        ax.set_ylabel('Membership Degree', fontsize=11)
        ax.set_title('Fuzzy Input Sets: Diversity (5 Labels)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=10)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
        
        plt.tight_layout()
        output_path_5 = os.path.join(plots_dir, '01_fuzzy_input_diversity_5labels.png')
        plt.savefig(output_path_5, dpi=300, bbox_inches='tight', format='png')
        plt.close(fig)
        results['5labels'] = output_path_5
    except Exception as e:
        print(f"[WARN] Failed to generate 5-label diversity plot: {e}")
        results['5labels'] = None
    
    return results


def plot_fuzzy_input_progress():
    """
    Plot fuzzy sets for Iteration Progress input (both 3 and 5 labels).
    Gets membership functions dynamically from FuzzyInertiaController.
    Returns: dict with '3labels' and '5labels' paths
    """
    plots_dir = ensure_plots_directory()
    results = {}
    
    # ===== 3-LABEL VERSION =====
    try:
        controller3 = FuzzyInertiaController(w_set='A')
        it_mf = controller3.it_mf
        
        progress = np.linspace(0, 1, 200)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = {'early': '#d62728', 'mid': '#9467bd', 'late': '#17becf'}
        
        for label, (a, b, c) in it_mf.items():
            mu = [tri(p, a, b, c) for p in progress]
            ax.plot(progress, mu, label=f'{label} ({a:.1f}, {b:.1f}, {c:.1f})', 
                    linewidth=2.5, color=colors[label])
            ax.fill_between(progress, mu, alpha=0.2, color=colors[label])
        
        ax.set_xlabel('Iteration Progress (0=start, 1=end)', fontsize=11)
        ax.set_ylabel('Membership Degree', fontsize=11)
        ax.set_title('Fuzzy Input Sets: Progress (3 Labels)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=10)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
        
        plt.tight_layout()
        output_path_3 = os.path.join(plots_dir, '02_fuzzy_input_progress_3labels.png')
        plt.savefig(output_path_3, dpi=300, bbox_inches='tight', format='png')
        plt.close(fig)
        results['3labels'] = output_path_3
    except Exception as e:
        print(f"[WARN] Failed to generate 3-label progress plot: {e}")
        results['3labels'] = None
    
    # ===== 5-LABEL VERSION =====
    try:
        from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
        controller5 = FuzzyInertiaController_5labels(w_set='A')
        it_mf = controller5.it_mf
        
        progress = np.linspace(0, 1, 200)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors_5 = {'very_early': '#8B0000', 'early': '#d62728', 'mid': '#9467bd', 
                    'late': '#17becf', 'very_late': '#1f77b4'}
        
        for label, (a, b, c) in it_mf.items():
            mu = [tri(p, a, b, c) for p in progress]
            ax.plot(progress, mu, label=f'{label} ({a:.1f}, {b:.1f}, {c:.1f})', 
                    linewidth=2.5, color=colors_5[label])
            ax.fill_between(progress, mu, alpha=0.2, color=colors_5[label])
        
        ax.set_xlabel('Iteration Progress (0=start, 1=end)', fontsize=11)
        ax.set_ylabel('Membership Degree', fontsize=11)
        ax.set_title('Fuzzy Input Sets: Progress (5 Labels)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=10)
        ax.set_xlim([0, 1])
        ax.set_ylim([0, 1.05])
        
        plt.tight_layout()
        output_path_5 = os.path.join(plots_dir, '02_fuzzy_input_progress_5labels.png')
        plt.savefig(output_path_5, dpi=300, bbox_inches='tight', format='png')
        plt.close(fig)
        results['5labels'] = output_path_5
    except Exception as e:
        print(f"[WARN] Failed to generate 5-label progress plot: {e}")
        results['5labels'] = None
    
    return results
    
    return output_path


def plot_fuzzy_output_w_set(w_set):
    """
    Plot fuzzy sets for Inertia Weight w output for a specific w_set.
    Generates plots for BOTH 3-label and 5-label controllers.
    
    Args:
        w_set: 'A', 'B', 'C', or 'D'
    
    Returns:
        dict with keys '3labels' and '5labels' pointing to generated PNG paths
    """
    plots_dir = ensure_plots_directory()
    
    # Import both controllers
    from fuzzy_controller_w import FuzzyInertiaController, tri
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
    results = {}
    
    # ===== Generate 3-LABEL plot =====
    try:
        controller3 = FuzzyInertiaController(w_set)
        w_norm = np.linspace(0, 1, 200)
        w_mf = controller3.w_mf
        wMin = controller3.wMin
        wMax = controller3.wMax
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors_3 = {'low': '#0072B2', 'medium': '#009E73', 'high': '#D55E00'}
        
        for label in ['low', 'medium', 'high']:
            a, b, c = w_mf[label]
            mu = [tri(w, a, b, c) for w in w_norm]
            w_scaled = wMin + w_norm * (wMax - wMin)
            ax.plot(w_scaled, mu, label=f'{label} ({a:.2f}, {b:.2f}, {c:.2f})', 
                    linewidth=2.5, color=colors_3[label])
            ax.fill_between(w_scaled, mu, alpha=0.2, color=colors_3[label])
        
        ax.set_xlabel(f'Inertia Weight $w$ [{wMin:.2f}, {wMax:.2f}]', fontsize=11)
        ax.set_ylabel('Membership Degree', fontsize=11)
        ax.set_title(f'Fuzzy Output Sets (3 Labels): Inertia Weight - Set {w_set}', 
                     fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(loc='upper right', fontsize=10)
        ax.set_ylim([0, 1.05])
        
        plt.tight_layout()
        output_path_3 = os.path.join(plots_dir, f'03_fuzzy_output_w_set_{w_set}_3labels.png')
        plt.savefig(output_path_3, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        results['3labels'] = output_path_3
    except Exception as e:
        print(f"[ERROR] Could not generate 3-label plot for Set {w_set}: {e}")
        results['3labels'] = None
    
    # ===== Generate 5-LABEL plot =====
    try:
        controller5 = FuzzyInertiaController_5labels(w_set)
        w_norm = np.linspace(0, 1, 200)
        w_mf = controller5.w_mf
        wMin = controller5.wMin
        wMax = controller5.wMax
        
        fig, ax = plt.subplots(figsize=(10, 6))
        colors_5 = {
            'very_low': '#4C72B0',
            'low': '#0072B2',
            'medium': '#009E73',
            'high': '#D55E00',
            'very_high': '#A63A42'
        }
        
        for label in ['very_low', 'low', 'medium', 'high', 'very_high']:
            a, b, c = w_mf[label]
            mu = [tri(w, a, b, c) for w in w_norm]
            w_scaled = wMin + w_norm * (wMax - wMin)
            ax.plot(w_scaled, mu, label=f'{label} ({a:.2f}, {b:.2f}, {c:.2f})', 
                    linewidth=2.5, color=colors_5[label])
            ax.fill_between(w_scaled, mu, alpha=0.2, color=colors_5[label])
        
        ax.set_xlabel(f'Inertia Weight $w$ [{wMin:.2f}, {wMax:.2f}]', fontsize=11)
        ax.set_ylabel('Membership Degree', fontsize=11)
        ax.set_title(f'Fuzzy Output Sets (5 Labels): Inertia Weight - Set {w_set}', 
                     fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(loc='upper right', fontsize=9, ncol=2)
        ax.set_ylim([0, 1.05])
        
        plt.tight_layout()
        output_path_5 = os.path.join(plots_dir, f'03_fuzzy_output_w_set_{w_set}_5labels.png')
        plt.savefig(output_path_5, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        results['5labels'] = output_path_5
    except Exception as e:
        print(f"[ERROR] Could not generate 5-label plot for Set {w_set}: {e}")
        results['5labels'] = None
    
    # Return both paths, or for backward compatibility, return 3labels path as primary
    return results


def plot_fuzzy_rules_heatmap():
    """
    Plot the fuzzy rule base as a heatmap for BOTH 3-label and 5-label controllers.
    Shows: For each (Diversity, Progress) combination, what output w level is activated.
    Returns dict with paths to both variants: {'3labels': path1, '5labels': path2}
    """
    plots_dir = ensure_plots_directory()
    
    results = {}
    
    # ===== 3-LABEL VERSION =====
    from fuzzy_controller_w import FuzzyInertiaController
    
    controller3 = FuzzyInertiaController('A')
    
    # Diversity labels and Progress labels (3-label)
    diversity_labels_3 = ['low', 'medium', 'high']
    progress_labels_3 = ['early', 'mid', 'late']
    output_labels_3 = {'low': 0, 'medium': 1, 'high': 2}
    
    # Create rule matrix (3-labels)
    rule_matrix_3 = np.zeros((len(diversity_labels_3), len(progress_labels_3)))
    
    for i, div_lab in enumerate(diversity_labels_3):
        for j, prog_lab in enumerate(progress_labels_3):
            output_lab = controller3.rules.get((div_lab, prog_lab), 'unknown')
            rule_matrix_3[i, j] = output_labels_3.get(output_lab, -1)
    
    # Create 3-label heatmap
    fig, ax = plt.subplots(figsize=(5, 4))
    
    im = ax.imshow(rule_matrix_3, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=2)
    
    # Set ticks and labels
    ax.set_xticks(range(len(progress_labels_3)))
    ax.set_yticks(range(len(diversity_labels_3)))
    ax.set_xticklabels(progress_labels_3)
    ax.set_yticklabels(diversity_labels_3)
    
    # Add text annotations
    output_text_3 = {0: 'L. w', 1: 'M. w', 2: 'H. w'}
    for i in range(len(diversity_labels_3)):
        for j in range(len(progress_labels_3)):
            text = ax.text(j, i, output_text_3[int(rule_matrix_3[i, j])],
                          ha="center", va="center", color="black", fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Iteration Progress', fontsize=16)
    ax.set_ylabel('Diversity Ratio', fontsize=16)
    ax.set_title('Fuzzy Rule Base - 3 Labels', fontsize=16, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax, ticks=[0, 1, 2])
    cbar.set_label('Output w Level', fontsize=16)
    cbar.ax.set_yticklabels(['Low (L.)', 'Medium (M.)', 'High (H.)'])
    
    plt.tight_layout()
    output_path_3 = os.path.join(plots_dir, '04_fuzzy_rules_heatmap_3labels.png')
    plt.savefig(output_path_3, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    results['3labels'] = output_path_3
    
    # ===== 5-LABEL VERSION =====
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
    controller5 = FuzzyInertiaController_5labels('A')
    
    # Diversity labels and Progress labels (5-label inputs)
    diversity_labels_5 = ['very_low', 'low', 'medium', 'high', 'very_high']
    progress_labels_5 = ['very_early', 'early', 'mid', 'late', 'very_late']
    # Output labels for 5-label system
    output_labels_5 = {'very_low': 0, 'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}
    
    # Create rule matrix (5-labels output)
    rule_matrix_5 = np.zeros((len(diversity_labels_5), len(progress_labels_5)))
    
    for i, div_lab in enumerate(diversity_labels_5):
        for j, prog_lab in enumerate(progress_labels_5):
            output_lab = controller5.rules.get((div_lab, prog_lab), 'unknown')
            rule_matrix_5[i, j] = output_labels_5.get(output_lab, -1)
    
    # Create 5-label heatmap
    fig, ax = plt.subplots(figsize=(5, 4))
    
    im = ax.imshow(rule_matrix_5, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=4)
    
    # Set ticks and labels
    ax.set_xticks(range(len(progress_labels_5)))
    ax.set_yticks(range(len(diversity_labels_5)))
    ax.set_xticklabels(progress_labels_5)
    ax.set_yticklabels(diversity_labels_5)
    
    # Add text annotations
    output_text_5 = {0: 'V.L. w', 1: 'L. w', 2: 'M. w', 3: 'H. w', 4: 'V.H. w'}
    for i in range(len(diversity_labels_5)):
        for j in range(len(progress_labels_5)):
            text = ax.text(j, i, output_text_5[int(rule_matrix_5[i, j])],
                          ha="center", va="center", color="black", fontsize=10, fontweight='bold')
    
    ax.set_xlabel('Iteration Progress', fontsize=16)
    ax.set_ylabel('Diversity Ratio', fontsize=16)
    ax.set_title('Fuzzy Rule Base - 5 Labels', fontsize=16, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax, ticks=[0, 1, 2, 3, 4])
    cbar.set_label('Output w Level', fontsize=16)
    cbar.ax.set_yticklabels(['V.Low (V.L.)', 'Low (L.)', 'Medium (M.)', 'High (H.)', 'V.High (V.H.)'])
    
    plt.tight_layout()
    output_path_5 = os.path.join(plots_dir, '04_fuzzy_rules_heatmap_5labels.png')
    plt.savefig(output_path_5, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    results['5labels'] = output_path_5
    
    return results


def _get_available_w_sets(controller_class):
    """
    Dynamically get available w_sets from controller class.
    Creates a dummy instance to access W_SETS dictionary.
    """
    try:
        # Try with each letter until we find available sets
        available = []
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            try:
                controller_class(letter)
                available.append(letter)
            except ValueError:
                pass
        return available if available else ['A', 'B']
    except Exception:
        return ['A', 'B']


def _calculate_grid_dims(num_sets):
    """
    Calculate optimal grid dimensions for subplots based on number of sets.
    Returns (rows, cols, figsize)
    """
    if num_sets == 1:
        return 1, 1, (7, 5)
    elif num_sets == 2:
        return 1, 2, (14, 5)
    elif num_sets == 3:
        return 1, 3, (18, 5)
    elif num_sets == 4:
        return 2, 2, (14, 10)
    elif num_sets == 5:
        return 2, 3, (18, 10)
    elif num_sets == 6:
        return 2, 3, (18, 10)
    else:  # num_sets >= 7
        cols = int(np.ceil(np.sqrt(num_sets)))
        rows = int(np.ceil(num_sets / cols))
        figsize = (7 * cols, 5 * rows)
        return rows, cols, figsize


def plot_all_w_sets_comparison():
    """
    Create comparison plots showing all available w_sets side by side for BOTH 3-label and 5-label.
    Dynamically adjusts grid layout based on number of available sets.
    Shows how output w varies for each set.
    Returns dict with paths to both variants: {'3labels': path1, '5labels': path2}
    """
    plots_dir = ensure_plots_directory()
    
    results = {}
    
    # ===== 3-LABEL VERSION =====
    from fuzzy_controller_w import FuzzyInertiaController
    
    # Dynamically get available w_sets
    w_sets = _get_available_w_sets(FuzzyInertiaController)
    rows, cols, figsize = _calculate_grid_dims(len(w_sets))
    
    fig, axes = plt.subplots(rows, cols, figsize=figsize, dpi=100)
    
    # Handle single subplot case (axes is not a 2D array)
    if rows == 1 and cols == 1:
        axes = np.array([[axes]])
    elif rows == 1 or cols == 1:
        axes = axes.reshape(rows, cols)
    else:
        axes = axes.flatten().reshape(rows, cols)
    
    axes_flat = axes.flatten()
    
    colors_3 = {'low': '#1f77b4', 'medium': '#ff7f0e', 'high': '#2ca02c'}
    
    for idx, w_set in enumerate(w_sets):
        try:
            controller = FuzzyInertiaController(w_set)
        except ValueError:
            axes_flat[idx].text(0.5, 0.5, f'Set {w_set} not defined', 
                               ha='center', va='center', fontsize=12)
            axes_flat[idx].axis('off')
            continue
        
        ax = axes_flat[idx]
        w_norm = np.linspace(0, 1, 100)
        w_mf = controller.w_mf
        wMin = controller.wMin
        wMax = controller.wMax
        
        for label, (a, b, c) in w_mf.items():
            mu = [tri(w, a, b, c) for w in w_norm]
            w_scaled = wMin + w_norm * (wMax - wMin)
            ax.plot(w_scaled, mu, label=label, linewidth=2.5, color=colors_3[label])
            ax.fill_between(w_scaled, mu, alpha=0.15, color=colors_3[label])
        
        ax.set_title(f'Set {w_set}', fontsize=16, fontweight='bold')
        ax.set_xlabel(f'w [{wMin:.2f}, {wMax:.2f}]', fontsize=16)
        ax.set_ylabel('Membership Degree', fontsize=16)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1.05])
        ax.legend(fontsize=16)
    
    # Hide unused subplots
    for idx in range(len(w_sets), len(axes_flat)):
        axes_flat[idx].axis('off')
    
    sets_str = ", ".join(w_sets)
    fig.suptitle(f'Fuzzy Inertia Weight Sets Comparison - 3 Labels ({sets_str})', 
                 fontsize=13, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    output_path_3 = os.path.join(plots_dir, '05_fuzzy_w_sets_comparison_3labels.png')
    plt.savefig(output_path_3, dpi=300, bbox_inches='tight', format='png')
    plt.close(fig)
    
    results['3labels'] = output_path_3
    
    # ===== 5-LABEL VERSION =====
    try:
        from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
        
        # Dynamically get available w_sets
        w_sets_5 = _get_available_w_sets(FuzzyInertiaController_5labels)
        rows_5, cols_5, figsize_5 = _calculate_grid_dims(len(w_sets_5))
        
        fig, axes = plt.subplots(rows_5, cols_5, figsize=figsize_5, dpi=100)
        
        # Handle single subplot case
        if rows_5 == 1 and cols_5 == 1:
            axes = np.array([[axes]])
        elif rows_5 == 1 or cols_5 == 1:
            axes = axes.reshape(rows_5, cols_5)
        else:
            axes = axes.flatten().reshape(rows_5, cols_5)
        
        axes_flat = axes.flatten()
        
        colors_5 = {
            'very_low': '#1f77b4', 
            'low': '#4fa3ff', 
            'medium': '#ff7f0e', 
            'high': '#2ca02c',
            'very_high': '#17ad17'
        }
        
        for idx, w_set in enumerate(w_sets_5):
            try:
                controller = FuzzyInertiaController_5labels(w_set)
            except ValueError:
                axes_flat[idx].text(0.5, 0.5, f'Set {w_set} not defined', 
                                   ha='center', va='center', fontsize=16)
                axes_flat[idx].axis('off')
                continue
            
            ax = axes_flat[idx]
            w_norm = np.linspace(0, 1, 100)
            w_mf = controller.w_mf
            wMin = controller.wMin
            wMax = controller.wMax
            
            for label, (a, b, c) in w_mf.items():
                mu = [tri(w, a, b, c) for w in w_norm]
                w_scaled = wMin + w_norm * (wMax - wMin)
                ax.plot(w_scaled, mu, label=label, linewidth=2.5, color=colors_5[label])
                ax.fill_between(w_scaled, mu, alpha=0.15, color=colors_5[label])
            
            ax.set_title(f'Set {w_set}', fontsize=16, fontweight='bold')
            ax.set_xlabel(f'w [{wMin:.2f}, {wMax:.2f}]', fontsize=16)
            ax.set_ylabel('Membership Degree', fontsize=16)
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 1.05])
            ax.legend(fontsize=16, loc='upper right')
        
        # Hide unused subplots
        for idx in range(len(w_sets_5), len(axes_flat)):
            axes_flat[idx].axis('off')
        
        sets_str_5 = ", ".join(w_sets_5)
        fig.suptitle(f'Fuzzy Inertia Weight Sets Comparison - 5 Labels ({sets_str_5})', 
                     fontsize=13, fontweight='bold', y=0.995)
        plt.tight_layout()
        
        output_path_5 = os.path.join(plots_dir, '05_fuzzy_w_sets_comparison_5labels.png')
        plt.savefig(output_path_5, dpi=300, bbox_inches='tight', format='png')
        plt.close(fig)
        
        results['5labels'] = output_path_5
    except ImportError:
        print("Warning: FuzzyInertiaController_5labels not found, skipping 5-label version")
    
    return results


def plot_output_w_comparison_membership_functions():
    """
    Generate comparison of OUTPUT (w) membership functions for 3 and 5 labels across fuzzy sets.
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w import FuzzyInertiaController
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
    # Dynamically detect available w_sets
    sets = _get_available_w_sets(FuzzyInertiaController)
    if not sets:
        sets = ['A']  # Fallback to A if nothing available
    
    # Calculate dynamic figsize and gridspec based on number of sets (REDUCED WIDTH)
    num_sets = len(sets)
    if num_sets <= 2:
        figsize = (3.5 * num_sets + 2, 11)
    elif num_sets == 3:
        figsize = (11, 11)
    else:
        figsize = (3.5 * num_sets + 2, 11)
    
    # Create figure with GridSpec for better control
    # Layout: [num_sets subplots 3-labels] [legend 3-labels] [num_sets subplots 5-labels] [legend 5-labels]
    fig = plt.figure(figsize=figsize)
    gs = fig.add_gridspec(4, num_sets, height_ratios=[2, 0.3, 2, 0.3], hspace=0.35, wspace=0.35)
    
    #fig.suptitle('Comparison of Inertia Weight Membership Functions: 3 vs. 5 Linguistic Labels', 
    #             fontsize=16, fontweight='bold', y=0.995)
    
    # Prepare legend data
    handles_3 = []
    labels_3_list = []
    handles_5 = []
    labels_5_list = []
    
    # ===== ROW 0-1: 3-LABEL PLOTS AND LEGEND =====
    axes_3 = []
    for col_idx, w_set in enumerate(sets):
        ctrl3 = FuzzyInertiaController(w_set=w_set)
        ax = fig.add_subplot(gs[0, col_idx])
        axes_3.append(ax)
        
        x = np.linspace(ctrl3.wMin, ctrl3.wMax, 500)
        colors_3 = ['#4C72B0', '#009E73', '#A63A42']
        
        for label, color in zip(['low', 'medium', 'high'], colors_3):
            a, b, c = ctrl3.w_mf[label]
            y = [tri(w, a, b, c) for w in x]
            line, = ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=3, color=color, linewidth=2.5)
            if col_idx == 0:
                handles_3.append(line)
                labels_3_list.append(label)
        
        ax.set_title(f'Set {w_set} (3 Labels)', fontweight='bold', fontsize=16)
        ax.set_xlabel('w', fontsize=16)
        ax.set_ylabel('Membership', fontsize=16)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
        ax.set_xlim([-0.05, 1.05])
        ax.set_ylim([0, 1.15])
        ax.tick_params(labelsize=14)
    
    # Add 3-label legend below the first group
    ax_legend_3 = fig.add_subplot(gs[1, :])
    ax_legend_3.axis('off')
    ax_legend_3.legend(handles_3, labels_3_list, loc='center', ncol=3, fontsize=16, 
                       #frameon=True, title='3-Label Linguistic Terms', title_fontsize=14, 
                       framealpha=0.95, edgecolor='black')
    
    # ===== ROW 2-3: 5-LABEL PLOTS AND LEGEND =====
    axes_5 = []
    for col_idx, w_set in enumerate(sets):
        ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
        ax = fig.add_subplot(gs[2, col_idx])
        axes_5.append(ax)
        
        x = np.linspace(ctrl5.wMin, ctrl5.wMax, 500)
        labels_5 = ['very_low', 'low', 'medium', 'high', 'very_high']
        colors_5 = ['#4C72B0', '#0072B2', '#009E73', '#D55E00', '#A63A42']
        labels_display = ['very low', 'low', 'medium', 'high', 'very high']
        
        for label_key, label_display, color in zip(labels_5, labels_display, colors_5):
            a, b, c = ctrl5.w_mf[label_key]
            y = [tri(w, a, b, c) for w in x]
            line, = ax.plot(x, y, 'o-', label=label_display, alpha=0.8, markersize=3, color=color, linewidth=2.5)
            if col_idx == 0:
                handles_5.append(line)
                labels_5_list.append(label_display)
        
        ax.set_title(f'Set {w_set} (5 Labels)', fontweight='bold', fontsize=16)
        ax.set_xlabel('w', fontsize=16)
        ax.set_ylabel('Membership', fontsize=16)
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
        ax.set_xlim([-0.05, 1.05])
        ax.set_ylim([0, 1.15])
        ax.tick_params(labelsize=14)
    
    # Add 5-label legend below the second group
    ax_legend_5 = fig.add_subplot(gs[3, :])
    ax_legend_5.axis('off')
    ax_legend_5.legend(handles_5, labels_5_list, loc='center', ncol=5, fontsize=16, 
                       #frameon=True, title='5-Label Linguistic Terms', title_fontsize=14,
                       framealpha=0.95, edgecolor='black')
    
    output_path = os.path.join(plots_dir, '06_output_w_comparison_membership_functions.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def plot_input_diversity_comparison_membership_functions():
    """
    Generate comparison of INPUT (Diversity) membership functions for 3 and 5 labels.
    Single figure showing 3-label vs 5-label comparison (NOT multiple fuzzy sets).
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w import FuzzyInertiaController
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
    # Create figure with 2 subplots: 3-label on top, 5-label on bottom
    fig, axes = plt.subplots(2, 1, figsize=(8, 10))
    
    # ===== TOP: 3-LABEL VERSION =====
    ax = axes[0]
    ctrl3 = FuzzyInertiaController(w_set='A')  # Use set A (input MFs are the same for all sets)
    
    x = np.linspace(0, 1, 500)
    colors_3 = ['#349E84', '#3F719B', '#042EAD']
    labels_3 = ['low', 'medium', 'high']
    
    for label, color in zip(labels_3, colors_3):
        a, b, c = ctrl3.div_mf[label]
        y = [tri(d, a, b, c) for d in x]
        ax.plot(x, y, 'o-', label=label, 
                alpha=0.8, markersize=4, color=color, linewidth=2.5)
    
    ax.set_xlabel('Diversity Ratio', fontsize=16, fontweight='bold')
    ax.set_ylabel('Membership', fontsize=16, fontweight='bold')
    #ax.set_title('3-Label Linguistic Terms', fontweight='bold', fontsize=16)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_xlim([-0.05, 1.05])
    ax.set_ylim([0, 1.15])
    ax.tick_params(labelsize=14)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=15, framealpha=0.95, edgecolor='black')
    
    # ===== BOTTOM: 5-LABEL VERSION =====
    ax = axes[1]
    ctrl5 = FuzzyInertiaController_5labels(w_set='A')  # Use set A (input MFs are the same for all sets)
    
    x = np.linspace(0, 1, 500)
    colors_5 = ["#349E84", "#4C8496", "#3F719B", "#253E57", "#042EAD"]
    labels_5 = ['very_low', 'low', 'medium', 'high', 'very_high']
    labels_display_5 = ['very low', 'low', 'medium', 'high', 'very high']
    
    for label_key, label_display, color in zip(labels_5, labels_display_5, colors_5):
        a, b, c = ctrl5.div_mf[label_key]
        y = [tri(d, a, b, c) for d in x]
        ax.plot(x, y, 'o-', label=label_display, 
                alpha=0.8, markersize=3, color=color, linewidth=2)
    
    ax.set_xlabel('Diversity Ratio', fontsize=16, fontweight='bold')
    ax.set_ylabel('Membership', fontsize=16, fontweight='bold')
    #ax.set_title('5-Label Linguistic Terms', fontweight='bold', fontsize=16)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_xlim([-0.05, 1.05])
    ax.set_ylim([0, 1.15])
    ax.tick_params(labelsize=14)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5, fontsize=15, framealpha=0.95, edgecolor='black')
    
    plt.tight_layout(pad=0.1, w_pad=0.05, h_pad=0.4)
    output_path = os.path.join(plots_dir, '06_input_diversity_comparison_membership_functions.png')
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    return output_path


def plot_input_progress_comparison_membership_functions():
    """
    Generate comparison of INPUT (Progress) membership functions for 3 and 5 labels.
    Single figure showing 3-label vs 5-label comparison (NOT multiple fuzzy sets).
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w import FuzzyInertiaController
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
    # Create figure with 2 subplots: 3-label on top, 5-label on bottom
    fig, axes = plt.subplots(2, 1, figsize=(8, 10))
    
    # ===== TOP: 3-LABEL VERSION =====
    ax = axes[0]
    ctrl3 = FuzzyInertiaController(w_set='A')  # Use set A (input MFs are the same for all sets)
    
    x = np.linspace(0, 1, 500)
    colors_3 = ['#4E4A45', '#BDA262', '#B87509']
    labels_3 = ['early', 'mid', 'late']
    
    for label, color in zip(labels_3, colors_3):
        a, b, c = ctrl3.it_mf[label]
        y = [tri(d, a, b, c) for d in x]
        ax.plot(x, y, 'o-', label=label, 
                alpha=0.8, markersize=4, color=color, linewidth=2.5)

    ax.set_xlabel('Progress', fontsize=16, fontweight='bold')    
    ax.set_ylabel('Membership', fontsize=16, fontweight='bold')
    #ax.set_title('3-Label Linguistic Terms', fontweight='bold', fontsize=16)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_xlim([-0.05, 1.05])
    ax.set_ylim([0, 1.15])
    ax.tick_params(labelsize=14)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3, fontsize=16, framealpha=0.95, edgecolor='black')
    
    # ===== BOTTOM: 5-LABEL VERSION =====
    ax = axes[1]
    ctrl5 = FuzzyInertiaController_5labels(w_set='A')  # Use set A (input MFs are the same for all sets)
    
    x = np.linspace(0, 1, 500)
    colors_5 = ["#4E4A45", "#8E7F5F", "#BDA262", "#B18A2F", "#B87509"]
    labels_5 = ['very_early', 'early', 'mid', 'late', 'very_late']
    labels_display_5 = ['very early', 'early', 'mid', 'late', 'very late']
    
    for label_key, label_display, color in zip(labels_5, labels_display_5, colors_5):
        a, b, c = ctrl5.it_mf[label_key]
        y = [tri(d, a, b, c) for d in x]
        ax.plot(x, y, 'o-', label=label_display, 
                alpha=0.8, markersize=3, color=color, linewidth=2)
    
    ax.set_xlabel('Progress', fontsize=16, fontweight='bold')
    ax.set_ylabel('Membership', fontsize=16, fontweight='bold')
    #ax.set_title('5-Label Linguistic Terms', fontweight='bold', fontsize=16)
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
    ax.set_xlim([-0.05, 1.05])
    ax.set_ylim([0, 1.15])
    ax.tick_params(labelsize=14)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=5, fontsize=16, framealpha=0.95, edgecolor='black')
    
    plt.tight_layout(pad=0.1, w_pad=0.05, h_pad=0.4)
    output_path = os.path.join(plots_dir, '06_input_progress_comparison_membership_functions.png')
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    return output_path


def plot_comparison_critical_points():
    """
    Create bar charts comparing inertia weights at critical points (3 vs 5 labels).
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w import FuzzyInertiaController
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
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
        
        # Dynamically detect available w_sets
        sets = _get_available_w_sets(FuzzyInertiaController)
        if not sets:
            sets = ['A']  # Fallback
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
        ax.set_ylabel('Inertia Weight w', fontsize=10)
        ax.set_title(title, fontsize=10, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(sets)
        ax.set_ylim([0, 1.0])
        ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.5)
        ax.legend(fontsize=9, loc='upper right', framealpha=0.95)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    output_path = os.path.join(plots_dir, '07_comparison_critical_points.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def plot_3d_comparison():
    """
    Create 3D surface comparison between 3-label and 5-label controllers for all available sets.
    Generates one plot per set.
    Each plot includes: 3D 3-labels, 3D 5-labels, and difference contour.
    Returns list of paths to the 3D comparison plots.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w import FuzzyInertiaController
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
    # Dynamically detect available w_sets
    sets = _get_available_w_sets(FuzzyInertiaController)
    if not sets:
        sets = ['A']  # Fallback
    div_range = np.linspace(0.01, 0.99, 40)
    prog_range = np.linspace(0.01, 0.99, 40)
    DIV, PROG = np.meshgrid(div_range, prog_range)
    
    output_paths = []
    
    for w_set in sets:
        ctrl3 = FuzzyInertiaController(w_set=w_set)
        ctrl5 = FuzzyInertiaController_5labels(w_set=w_set)
        
        W3 = np.zeros_like(DIV)
        W5 = np.zeros_like(DIV)
        
        # Compute surfaces
        for i in range(DIV.shape[0]):
            for j in range(DIV.shape[1]):
                W3[i, j] = ctrl3.compute_w(DIV[i, j], PROG[i, j])
                W5[i, j] = ctrl5.compute_w(DIV[i, j], PROG[i, j])
        
        # Create figure for this set
        fig = plt.figure(figsize=(14, 4.5))
        fig.suptitle(f'3D Surface Comparison: Set {w_set} (3-Label vs 5-Label)', 
                     fontsize=12, fontweight='bold', y=0.98)
        
        # 3D Surface para 3 labels
        ax1 = fig.add_subplot(131, projection='3d')
        ax1.plot_surface(DIV, PROG, W3, cmap='viridis', alpha=0.8, edgecolor='none')
        ax1.set_xlabel('Diversity Ratio', fontsize=10)
        ax1.set_ylabel('Progress (Iteration)', fontsize=10)
        ax1.set_zlabel('Inertia Weight w', fontsize=10)
        ax1.set_title(f'Set {w_set}: 3 Labels', fontsize=11, fontweight='bold')
        ax1.tick_params(labelsize=9)
        
        # 3D Surface para 5 labels
        ax2 = fig.add_subplot(132, projection='3d')
        ax2.plot_surface(DIV, PROG, W5, cmap='plasma', alpha=0.8, edgecolor='none')
        ax2.set_xlabel('Diversity Ratio', fontsize=10)
        ax2.set_ylabel('Progress (Iteration)', fontsize=10)
        ax2.set_zlabel('Inertia Weight w', fontsize=10)
        ax2.set_title(f'Set {w_set}: 5 Labels', fontsize=11, fontweight='bold')
        ax2.tick_params(labelsize=9)
        
        # Diferencia (contour plot)
        ax3 = fig.add_subplot(133)
        diff = W5 - W3
        contour = ax3.contourf(DIV, PROG, diff, levels=15, cmap='RdBu_r')
        ax3.set_xlabel('Diversity Ratio', fontsize=10)
        ax3.set_ylabel('Progress (Iteration)', fontsize=10)
        ax3.set_title(f'Set {w_set}: Difference (5-labels minus 3-labels)', fontsize=11, fontweight='bold')
        cbar = plt.colorbar(contour, ax=ax3)
        cbar.set_label('Δw', fontsize=10)
        cbar.ax.tick_params(labelsize=9)
        
        plt.tight_layout(rect=[0, 0, 1, 0.97])
        output_path = os.path.join(plots_dir, f'08_3d_surface_comparison_set_{w_set}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        output_paths.append(output_path)
    
    return output_paths


def generate_all_fuzzy_plots(verbose=False):
    """
    Generate all fuzzy set visualizations.

    Call this to create all plots at once.
    """
    plots_dir = ensure_plots_directory()
    
    if verbose:
        print("\n[*] Generating Fuzzy Set Visualizations")
        print("=" * 70)
    
    outputs = []
    
    # Input: Diversity (both 3 and 5 labels)
    try:
        result = plot_fuzzy_input_diversity()
        if isinstance(result, dict):
            if result.get('3labels'):
                outputs.append(result['3labels'])
                if verbose:
                    print(f"[OK] Diversity input (3-labels): {result['3labels']}")
            if result.get('5labels'):
                outputs.append(result['5labels'])
                if verbose:
                    print(f"[OK] Diversity input (5-labels): {result['5labels']}")
        elif result:
            outputs.append(result)
            if verbose:
                print(f"[OK] Diversity input fuzzy sets: {result}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] Diversity plot failed: {e}")
    
    # Input: Progress (both 3 and 5 labels)
    try:
        result = plot_fuzzy_input_progress()
        if isinstance(result, dict):
            if result.get('3labels'):
                outputs.append(result['3labels'])
                if verbose:
                    print(f"[OK] Progress input (3-labels): {result['3labels']}")
            if result.get('5labels'):
                outputs.append(result['5labels'])
                if verbose:
                    print(f"[OK] Progress input (5-labels): {result['5labels']}")
        elif result:
            outputs.append(result)
            if verbose:
                print(f"[OK] Progress input fuzzy sets: {result}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] Progress plot failed: {e}")
    
    # Output: w for each set (both 3 and 5 labels)
    # Dynamically detect available w_sets
    available_w_sets = _get_available_w_sets(FuzzyInertiaController)
    for w_set in available_w_sets:
        try:
            paths = plot_fuzzy_output_w_set(w_set)
            if isinstance(paths, dict):
                # New version returns dict with '3labels' and '5labels' keys
                if paths.get('3labels'):
                    outputs.append(paths['3labels'])
                    if verbose:
                        print(f"[OK] Output w (3-labels, Set {w_set}): {paths['3labels']}")
                if paths.get('5labels'):
                    outputs.append(paths['5labels'])
                    if verbose:
                        print(f"[OK] Output w (5-labels, Set {w_set}): {paths['5labels']}")
            elif paths:
                # Backward compatibility: old version returns single path
                outputs.append(paths)
                if verbose:
                    print(f"[OK] Output w (Set {w_set}): {paths}")
        except Exception as e:
            if verbose:
                print(f"[ERROR] w_set {w_set} plot failed: {e}")
    
    # Rules heatmap (both 3 and 5 labels)
    try:
        result = plot_fuzzy_rules_heatmap()
        if isinstance(result, dict):
            # New version returns dict with '3labels' and '5labels' keys
            if result.get('3labels'):
                outputs.append(result['3labels'])
                if verbose:
                    print(f"[OK] Fuzzy rules heatmap (3-labels): {result['3labels']}")
            if result.get('5labels'):
                outputs.append(result['5labels'])
                if verbose:
                    print(f"[OK] Fuzzy rules heatmap (5-labels): {result['5labels']}")
        elif result:
            # Backward compatibility: old version returns single path
            outputs.append(result)
            if verbose:
                print(f"[OK] Fuzzy rules heatmap: {result}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] Rules heatmap failed: {e}")
    
    # All w_sets comparison (both 3 and 5 labels)
    try:
        result = plot_all_w_sets_comparison()
        if isinstance(result, dict):
            # New version returns dict with '3labels' and '5labels' keys
            if result.get('3labels'):
                outputs.append(result['3labels'])
                if verbose:
                    print(f"[OK] All w_sets comparison (3-labels): {result['3labels']}")
            if result.get('5labels'):
                outputs.append(result['5labels'])
                if verbose:
                    print(f"[OK] All w_sets comparison (5-labels): {result['5labels']}")
        elif result:
            # Backward compatibility: old version returns single path
            outputs.append(result)
            if verbose:
                print(f"[OK] All w_sets comparison: {result}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] w_sets comparison failed: {e}")
    
    # Comparison: INPUT (Diversity) membership functions - 3 vs 5 labels
    try:
        path = plot_input_diversity_comparison_membership_functions()
        outputs.append(path)
        if verbose:
            print(f"[OK] Diversity input comparison membership functions: {path}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] Diversity input comparison membership functions failed: {e}")
    
    # Comparison: INPUT (Progress) membership functions - 3 vs 5 labels
    try:
        path = plot_input_progress_comparison_membership_functions()
        outputs.append(path)
        if verbose:
            print(f"[OK] Progress input comparison membership functions: {path}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] Progress input comparison membership functions failed: {e}")
    
    # Comparison: OUTPUT (w) membership functions - 3 vs 5 labels
    try:
        path = plot_output_w_comparison_membership_functions()
        outputs.append(path)
        if verbose:
            print(f"[OK] Output w comparison membership functions (3 vs 5): {path}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] Output w comparison membership functions failed: {e}")
    
    # Comparison: 3 vs 5 labels at critical points
    try:
        path = plot_comparison_critical_points()
        outputs.append(path)
        if verbose:
            print(f"[OK] Comparison critical points (3 vs 5): {path}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] Comparison critical points failed: {e}")
    
    # 3D Surface comparison (now returns list of 4 paths, one per set)
    try:
        paths_list = plot_3d_comparison()
        for path in paths_list:
            outputs.append(path)
            if verbose:
                print(f"[OK] 3D Surface comparison: {path}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] 3D Surface comparison failed: {e}")
    
    if verbose:
        print("=" * 70)
        print(f"[OK] Generated {len(outputs)} plots in {plots_dir}\n")
    
    return outputs


def generate_all_plots_comprehensive(verbose=True):
    """
    Generate all fuzzy plots: base plots + set comparison matrices.
    Returns combined list of all generated plot paths.
    """
    # Generate base fuzzy plots
    outputs = generate_all_fuzzy_plots(verbose=verbose)
    
    # Import and generate set comparison matrices
    try:
        from FUZZY.compare_all_sets_w_values import generate_all_set_comparisons
        comparison_outputs = generate_all_set_comparisons(verbose=verbose)
        outputs.extend(comparison_outputs)
    except ImportError:
        # If compare_all_sets not available, continue without it
        if verbose:
            print("[WARNING] compare_all_sets module not found, skipping comparison matrices")
    
    return outputs


if __name__ == '__main__':
    generate_all_fuzzy_plots(verbose=True)
