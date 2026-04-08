"""
Compare all fuzzy sets (A, B, C, D) across 3-label and 5-label controllers.
Generates three 4×4 matrices of difference heatmaps:
1. 3-labels: Set A vs B vs C vs D (16 heatmaps)
2. 5-labels: Set A vs B vs C vs D (16 heatmaps)
3. 3-labels vs 5-labels: All cross-comparisons (16 heatmaps)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import cm


def ensure_plots_directory():
    """Ensure FUZZY/plots directory exists."""
    plots_dir = os.path.join(os.path.dirname(__file__), 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    return plots_dir


def _get_available_w_sets(controller_class):
    """
    Dynamically get available w_sets from controller class.
    Creates a dummy instance to access W_SETS dictionary.
    """
    try:
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


def compute_surface(controller, div_range, prog_range):
    """Compute w values for a controller across diversity/progress grid."""
    DIV, PROG = np.meshgrid(div_range, prog_range)
    W = np.zeros_like(DIV)
    
    for i in range(DIV.shape[0]):
        for j in range(DIV.shape[1]):
            W[i, j] = controller.compute_w(DIV[i, j], PROG[i, j])
    
    return W


def plot_nxn_matrix_3labels(input_set="I1"):
    """
    Create NxN matrix comparing 3-label controllers for available sets.
    Each cell: heatmap of Δw = Set_i(3L) - Set_j(3L)
    N is dynamically determined by the number of available sets.
    """
    from fuzzy_controller_w import FuzzyInertiaController
    
    plots_dir = ensure_plots_directory()
    sets = _get_available_w_sets(FuzzyInertiaController)
    if not sets:
        sets = ['A', 'B']
    
    n_sets = len(sets)
    div_range = np.linspace(0.01, 0.99, 50)
    prog_range = np.linspace(0.01, 0.99, 50)
    
    # Calculate figsize based on number of sets
    figsize = (4 * n_sets, 4 * n_sets)
    
    # Precompute all surfaces
    surfaces_3L = {}
    for w_set in sets:
        try:
            ctrl = FuzzyInertiaController(w_set=w_set, input_set=input_set)
            surfaces_3L[w_set] = compute_surface(ctrl, div_range, prog_range)
        except ValueError:
            # Skip if set not available
            pass
    
    # Create NxN matrix
    fig, axes = plt.subplots(n_sets, n_sets, figsize=figsize)
    
    # Handle case where n_sets == 1 (axes won't be 2D)
    if n_sets == 1:
        axes = np.array([[axes]])
    elif n_sets > 1:
        axes = axes.reshape(n_sets, n_sets) if axes.ndim > 1 else axes
    
    sets_str = ", ".join(sets)
    fig.suptitle(f'Comparison Matrix: 3-Label Controllers ({sets_str})', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    vmin, vmax = -0.5, 0.5
    im = None
    
    for i, set_i in enumerate(sets):
        for j, set_j in enumerate(sets):
            ax = axes[i, j] if n_sets > 1 else axes[0, 0]
            
            if set_i not in surfaces_3L or set_j not in surfaces_3L:
                ax.text(0.5, 0.5, f'{set_i} or {set_j}\nnot available', 
                       ha='center', va='center', fontsize=10)
                ax.axis('off')
                continue
            
            if i == j:
                diff = np.zeros_like(surfaces_3L[set_i])
                im = ax.imshow(diff, cmap='RdBu_r', vmin=vmin, vmax=vmax, aspect='auto', origin='lower')
                ax.set_title(f'{set_i} vs {set_j} (same)', fontsize=10, fontweight='bold')
            else:
                diff = surfaces_3L[set_i] - surfaces_3L[set_j]
                im = ax.imshow(diff, cmap='RdBu_r', vmin=vmin, vmax=vmax, aspect='auto', origin='lower')
                ax.set_title(f'{set_i} vs {set_j}', fontsize=10, fontweight='bold')
            
            ax.set_xlabel('Diversity', fontsize=9)
            ax.set_ylabel('Progress', fontsize=9)
            ax.tick_params(labelsize=8)
    
    # Add colorbar
    if im is not None:
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        cbar = plt.colorbar(im, cax=cbar_ax)
        cbar.set_label('Δw (Set_i minus Set_j)', fontsize=10)
    
    plt.tight_layout(rect=[0, 0, 0.91, 0.99])
    output_path = os.path.join(plots_dir, '09_comparison_matrix_3labels.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def plot_nxn_matrix_5labels(input_set="I1"):
    """
    Create NxN matrix comparing 5-label controllers for available sets.
    Each cell: heatmap of Δw = Set_i(5L) - Set_j(5L)
    N is dynamically determined by the number of available sets.
    """
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
    plots_dir = ensure_plots_directory()
    sets = _get_available_w_sets(FuzzyInertiaController_5labels)
    if not sets:
        sets = ['A', 'B']
    
    n_sets = len(sets)
    div_range = np.linspace(0.01, 0.99, 50)
    prog_range = np.linspace(0.01, 0.99, 50)
    
    # Calculate figsize based on number of sets
    figsize = (4 * n_sets, 4 * n_sets)
    
    # Precompute all surfaces
    surfaces_5L = {}
    for w_set in sets:
        try:
            ctrl = FuzzyInertiaController_5labels(w_set=w_set, input_set=input_set)
            surfaces_5L[w_set] = compute_surface(ctrl, div_range, prog_range)
        except ValueError:
            pass
    
    # Create NxN matrix
    fig, axes = plt.subplots(n_sets, n_sets, figsize=figsize)
    
    # Handle case where n_sets == 1
    if n_sets == 1:
        axes = np.array([[axes]])
    elif n_sets > 1:
        axes = axes.reshape(n_sets, n_sets) if axes.ndim > 1 else axes
    
    sets_str = ", ".join(sets)
    fig.suptitle(f'Comparison Matrix: 5-Label Controllers ({sets_str})', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    vmin, vmax = -0.5, 0.5
    im = None
    
    for i, set_i in enumerate(sets):
        for j, set_j in enumerate(sets):
            ax = axes[i, j] if n_sets > 1 else axes[0, 0]
            
            if set_i not in surfaces_5L or set_j not in surfaces_5L:
                ax.text(0.5, 0.5, f'{set_i} or {set_j}\nnot available', 
                       ha='center', va='center', fontsize=10)
                ax.axis('off')
                continue
            
            if i == j:
                diff = np.zeros_like(surfaces_5L[set_i])
                im = ax.imshow(diff, cmap='RdBu_r', vmin=vmin, vmax=vmax, aspect='auto', origin='lower')
                ax.set_title(f'{set_i} vs {set_j} (same)', fontsize=10, fontweight='bold')
            else:
                diff = surfaces_5L[set_i] - surfaces_5L[set_j]
                im = ax.imshow(diff, cmap='RdBu_r', vmin=vmin, vmax=vmax, aspect='auto', origin='lower')
                ax.set_title(f'{set_i} vs {set_j}', fontsize=10, fontweight='bold')
            
            ax.set_xlabel('Diversity', fontsize=9)
            ax.set_ylabel('Progress', fontsize=9)
            ax.tick_params(labelsize=8)
    
    # Add colorbar
    if im is not None:
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        cbar = plt.colorbar(im, cax=cbar_ax)
        cbar.set_label('Δw (Set_i minus Set_j)', fontsize=10)
    
    plt.tight_layout(rect=[0, 0, 0.91, 0.99])
    output_path = os.path.join(plots_dir, '09_comparison_matrix_5labels.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def plot_nxn_matrix_3vs5labels(input_set="I1"):
    """
    Create NxN matrix comparing 3-label vs 5-label for available sets.
    Each cell: heatmap of Δw = Set_j(5L) - Set_i(3L)
    N is dynamically determined by the number of available sets.
    """
    from fuzzy_controller_w import FuzzyInertiaController
    from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
    
    plots_dir = ensure_plots_directory()
    sets = _get_available_w_sets(FuzzyInertiaController)
    if not sets:
        sets = ['A', 'B']
    
    n_sets = len(sets)
    div_range = np.linspace(0.01, 0.99, 50)
    prog_range = np.linspace(0.01, 0.99, 50)
    
    # Calculate figsize based on number of sets
    figsize = (4 * n_sets, 4 * n_sets)
    
    # Precompute all surfaces
    surfaces_3L = {}
    surfaces_5L = {}
    for w_set in sets:
        try:
            ctrl3 = FuzzyInertiaController(w_set=w_set, input_set=input_set)
            ctrl5 = FuzzyInertiaController_5labels(w_set=w_set, input_set=input_set)
            surfaces_3L[w_set] = compute_surface(ctrl3, div_range, prog_range)
            surfaces_5L[w_set] = compute_surface(ctrl5, div_range, prog_range)
        except ValueError:
            pass
    
    # Create NxN matrix
    fig, axes = plt.subplots(n_sets, n_sets, figsize=figsize)
    
    # Handle case where n_sets == 1
    if n_sets == 1:
        axes = np.array([[axes]])
    elif n_sets > 1:
        axes = axes.reshape(n_sets, n_sets) if axes.ndim > 1 else axes
    
    sets_str = ", ".join(sets)
    fig.suptitle(f'Comparison Matrix: 3-Label (rows) vs 5-Label (columns) ({sets_str})\nΔw = 5-label minus 3-label', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    vmin, vmax = -0.5, 0.5
    im = None
    
    for i, set_i in enumerate(sets):
        for j, set_j in enumerate(sets):
            ax = axes[i, j] if n_sets > 1 else axes[0, 0]
            
            if set_i not in surfaces_3L or set_j not in surfaces_5L:
                ax.text(0.5, 0.5, 'Set not\navailable', ha='center', va='center', fontsize=10)
                ax.axis('off')
                continue
            
            diff = surfaces_5L[set_j] - surfaces_3L[set_i]
            im = ax.imshow(diff, cmap='RdBu_r', vmin=vmin, vmax=vmax, aspect='auto', origin='lower')
            
            title_text = f'{set_i}(3L) vs {set_j}(5L)'
            if i == j:
                title_text += ' (same set)'
            ax.set_title(title_text, fontsize=10, fontweight='bold')
            
            ax.set_xlabel('Diversity', fontsize=9)
            ax.set_ylabel('Progress', fontsize=9)
            ax.tick_params(labelsize=8)
    
    # Add colorbar
    if im is not None:
        cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
        cbar = plt.colorbar(im, cax=cbar_ax)
        cbar.set_label('Δw (5-label minus 3-label)', fontsize=10)
    
    plt.tight_layout(rect=[0, 0, 0.91, 0.99])
    output_path = os.path.join(plots_dir, '09_comparison_matrix_3vs5labels.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def generate_all_set_comparisons(verbose=True):
    """Generate all comparison matrices with dynamic N×N layout."""
    outputs = []
    
    if verbose:
        print("\n" + "="*70)
        print("Generating Set Comparison Matrices (N×N, dynamically sized)")
        print("="*70 + "\n")
    
    # 1. 3-Label comparison matrix
    try:
        path = plot_nxn_matrix_3labels()
        outputs.append(path)
        if verbose:
            print(f"[OK] 3-Label comparison matrix: {path}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] 3-Label comparison matrix failed: {e}")
    
    # 2. 5-Label comparison matrix
    try:
        path = plot_nxn_matrix_5labels()
        outputs.append(path)
        if verbose:
            print(f"[OK] 5-Label comparison matrix: {path}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] 5-Label comparison matrix failed: {e}")
    
    # 3. 3-Label vs 5-Label comparison matrix
    try:
        path = plot_nxn_matrix_3vs5labels()
        outputs.append(path)
        if verbose:
            print(f"[OK] 3vs5-Label comparison matrix: {path}")
    except Exception as e:
        if verbose:
            print(f"[ERROR] 3vs5-Label comparison matrix failed: {e}")
    
    if verbose:
        print("\n" + "="*70)
        print(f"[OK] Generated {len(outputs)} comparison matrices")
        print("="*70 + "\n")
    
    return outputs


if __name__ == '__main__':
    generate_all_set_comparisons(verbose=True)
