"""
Updated versions of fuzzy plots 06-10 using FuzzyInertiaController_Auto.
These versions support all granularities [3,5,7,9] with both individual and panel views.

Generates:
  06: Input diversity MF comparison (individual + panel)
  07: Input progress MF comparison (individual + panel)
  08: Output w MF comparison (individual + panel)
  09: Critical points comparison (individual + panel)
  10: 3D surfaces individual (per granularity × rule_set)
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.integrate import trapezoid

# Import the universal controller
try:
    from fuzzy_controller_auto import FuzzyInertiaController_Auto, tri
except ImportError:
    from .fuzzy_controller_auto import FuzzyInertiaController_Auto, tri


def ensure_plots_directory():
    """Ensure plots directory exists."""
    plots_dir = os.path.join(os.path.dirname(__file__), 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    return plots_dir


def _palette_for_labels(num_labels):
    """Return color palette for num_labels."""
    palettes = {
        3: ['#349E84', '#3F719B', '#042EAD'],
        5: ["#349E84", "#4C8496", "#3F719B", "#253E57", "#042EAD"],
        7: ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#a6761d"],
        9: ["#1b9e77", "#d95f02", "#7570b3", "#e7298a", "#66a61e", "#e6ab02", "#a6761d", "#fc8d62", "#8da0cb"],
    }
    return palettes.get(num_labels, [f'C{i}' for i in range(num_labels)])


# ==============================================================================
# 06: Input Diversity MF Comparison (Individual + Panel)
# ==============================================================================

def plot_06_input_diversity_mf_individual(input_set="I1", num_labels_list=None):
    """
    Generate individual input diversity MF plots for each granularity.
    Individual files: one per num_labels value.
    """
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    results = {}
    x = np.linspace(0, 1, 500)
    
    for num_labels in num_labels_list:
        try:
            ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels, input_set=input_set)
            colors = _palette_for_labels(num_labels)
            labels = list(ctrl.div_mf.keys())
            
            fig, ax = plt.subplots(figsize=(10, 6))
            for label, color in zip(labels, colors):
                a, b, c = ctrl.div_mf[label]
                y = [tri(d, a, b, c) for d in x]
                ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=4, 
                       color=color, linewidth=2.5)
            
            ax.set_xlabel('Diversity Ratio', fontsize=14, fontweight='bold')
            ax.set_ylabel('Membership', fontsize=14, fontweight='bold')
            ax.set_title(f'Input Diversity MF ({num_labels} Labels)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
            ax.set_xlim([-0.05, 1.05])
            ax.set_ylim([0, 1.15])
            ax.tick_params(labelsize=12)
            ax.legend(fontsize=11, loc='upper center', bbox_to_anchor=(0.5, -0.12), 
                     ncol=num_labels, framealpha=0.95, edgecolor='black')
            
            plt.tight_layout()
            output_path = os.path.join(plots_dir, f'06_input_diversity_mf_{num_labels}labels_{input_set}.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{num_labels}labels'] = output_path
        except Exception as e:
            print(f"[ERROR] 06 diversity individual ({num_labels}): {e}")
            results[f'{num_labels}labels'] = None
    
    return results


def plot_06_input_diversity_mf_panel(input_set="I1", num_labels_list=None):
    """
    Generate panel comparison of input diversity MF across all granularities.
    Single file: 06_input_diversity_mf_panel.png
    """
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    x = np.linspace(0, 1, 500)
    fig, axes = plt.subplots(1, len(num_labels_list), figsize=(16, 4))
    
    for idx, num_labels in enumerate(num_labels_list):
        try:
            ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels, input_set=input_set)
            ax = axes[idx]
            colors = _palette_for_labels(num_labels)
            labels = list(ctrl.div_mf.keys())
            
            for label, color in zip(labels, colors):
                a, b, c = ctrl.div_mf[label]
                y = [tri(d, a, b, c) for d in x]
                ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=3, 
                       color=color, linewidth=2)
            
            ax.set_title(f'{num_labels} Labels', fontsize=12, fontweight='bold')
            ax.set_xlabel('Diversity Ratio', fontsize=11)
            ax.set_ylabel('Membership', fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
            ax.set_xlim([-0.05, 1.05])
            ax.set_ylim([0, 1.15])
            ax.tick_params(labelsize=10)
        except Exception as e:
            print(f"[ERROR] 06 diversity panel ({num_labels}): {e}")
    
    plt.tight_layout()
    output_path = os.path.join(plots_dir, f'06_input_diversity_mf_panel_{input_set}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path


# ==============================================================================
# 07: Input Progress MF Comparison (Individual + Panel)
# ==============================================================================

def plot_07_input_progress_mf_individual(input_set="I1", num_labels_list=None):
    """Generate individual input progress MF plots for each granularity."""
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    results = {}
    x = np.linspace(0, 1, 500)
    
    for num_labels in num_labels_list:
        try:
            ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels, input_set=input_set)
            colors = _palette_for_labels(num_labels)
            labels = list(ctrl.it_mf.keys())
            
            fig, ax = plt.subplots(figsize=(10, 6))
            for label, color in zip(labels, colors):
                a, b, c = ctrl.it_mf[label]
                y = [tri(d, a, b, c) for d in x]
                ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=4, 
                       color=color, linewidth=2.5)
            
            ax.set_xlabel('Iteration Progress', fontsize=14, fontweight='bold')
            ax.set_ylabel('Membership', fontsize=14, fontweight='bold')
            ax.set_title(f'Input Progress MF ({num_labels} Labels)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
            ax.set_xlim([-0.05, 1.05])
            ax.set_ylim([0, 1.15])
            ax.tick_params(labelsize=12)
            ax.legend(fontsize=11, loc='upper center', bbox_to_anchor=(0.5, -0.12), 
                     ncol=num_labels, framealpha=0.95, edgecolor='black')
            
            plt.tight_layout()
            output_path = os.path.join(plots_dir, f'07_input_progress_mf_{num_labels}labels_{input_set}.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{num_labels}labels'] = output_path
        except Exception as e:
            print(f"[ERROR] 07 progress individual ({num_labels}): {e}")
            results[f'{num_labels}labels'] = None
    
    return results


def plot_07_input_progress_mf_panel(input_set="I1", num_labels_list=None):
    """Generate panel comparison of input progress MF across all granularities."""
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    x = np.linspace(0, 1, 500)
    fig, axes = plt.subplots(1, len(num_labels_list), figsize=(16, 4))
    
    for idx, num_labels in enumerate(num_labels_list):
        try:
            ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels, input_set=input_set)
            ax = axes[idx]
            colors = _palette_for_labels(num_labels)
            labels = list(ctrl.it_mf.keys())
            
            for label, color in zip(labels, colors):
                a, b, c = ctrl.it_mf[label]
                y = [tri(d, a, b, c) for d in x]
                ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=3, 
                       color=color, linewidth=2)
            
            ax.set_title(f'{num_labels} Labels', fontsize=12, fontweight='bold')
            ax.set_xlabel('Iteration Progress', fontsize=11)
            ax.set_ylabel('Membership', fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
            ax.set_xlim([-0.05, 1.05])
            ax.set_ylim([0, 1.15])
            ax.tick_params(labelsize=10)
        except Exception as e:
            print(f"[ERROR] 07 progress panel ({num_labels}): {e}")
    
    plt.tight_layout()
    output_path = os.path.join(plots_dir, f'07_input_progress_mf_panel_{input_set}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path


# ==============================================================================
# 08: Output w MF Comparison (Individual + Panel)
# ==============================================================================

def plot_08_output_w_mf_individual(num_labels_list=None):
    """Generate individual output w MF plots for each granularity."""
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    results = {}
    
    for num_labels in num_labels_list:
        try:
            ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels)
            colors = _palette_for_labels(num_labels)
            labels = list(ctrl.w_mf.keys())
            
            x = np.linspace(ctrl.wMin, ctrl.wMax, 500)
            fig, ax = plt.subplots(figsize=(10, 6))
            
            for label, color in zip(labels, colors):
                a, b, c = ctrl.w_mf[label]
                y = [tri(w, a, b, c) for w in x]
                ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=4, 
                       color=color, linewidth=2.5)
            
            ax.set_xlabel('Inertia Weight w', fontsize=14, fontweight='bold')
            ax.set_ylabel('Membership', fontsize=14, fontweight='bold')
            ax.set_title(f'Output Inertia Weight MF ({num_labels} Labels)', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
            ax.set_xlim([ctrl.wMin-0.05, ctrl.wMax+0.05])
            ax.set_ylim([0, 1.15])
            ax.tick_params(labelsize=12)
            ax.legend(fontsize=11, loc='upper center', bbox_to_anchor=(0.5, -0.12), 
                     ncol=num_labels, framealpha=0.95, edgecolor='black')
            
            plt.tight_layout()
            output_path = os.path.join(plots_dir, f'08_output_w_mf_{num_labels}labels.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{num_labels}labels'] = output_path
        except Exception as e:
            print(f"[ERROR] 08 output w individual ({num_labels}): {e}")
            results[f'{num_labels}labels'] = None
    
    return results


def plot_08_output_w_mf_panel(num_labels_list=None):
    """Generate panel comparison of output w MF across all granularities."""
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    fig, axes = plt.subplots(1, len(num_labels_list), figsize=(16, 4))
    
    for idx, num_labels in enumerate(num_labels_list):
        try:
            ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels)
            ax = axes[idx]
            colors = _palette_for_labels(num_labels)
            labels = list(ctrl.w_mf.keys())
            
            x = np.linspace(ctrl.wMin, ctrl.wMax, 500)
            for label, color in zip(labels, colors):
                a, b, c = ctrl.w_mf[label]
                y = [tri(w, a, b, c) for w in x]
                ax.plot(x, y, 'o-', label=label, alpha=0.8, markersize=3, 
                       color=color, linewidth=2)
            
            ax.set_title(f'{num_labels} Labels', fontsize=12, fontweight='bold')
            ax.set_xlabel('Inertia Weight w', fontsize=11)
            ax.set_ylabel('Membership', fontsize=11)
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
            ax.set_xlim([ctrl.wMin-0.05, ctrl.wMax+0.05])
            ax.set_ylim([0, 1.15])
            ax.tick_params(labelsize=10)
        except Exception as e:
            print(f"[ERROR] 08 output w panel ({num_labels}): {e}")
    
    plt.tight_layout()
    output_path = os.path.join(plots_dir, f'08_output_w_mf_panel.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path


# ==============================================================================
# 09: Critical Points Comparison (Individual + Panel)
# ==============================================================================

def plot_09_critical_points_individual(input_set="I1", num_labels_list=None):
    """Generate individual critical points plots for each granularity."""
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    results = {}
    test_points = [
        (0.1, 0.1, "Low Div\n(Early)"),
        (0.5, 0.5, "Med Div\n(Mid)"),
        (0.9, 0.9, "High Div\n(Late)"),
    ]
    
    for num_labels in num_labels_list:
        try:
            fig, axes = plt.subplots(1, 3, figsize=(12, 4))
            fig.suptitle(f'Critical Points: {num_labels} Labels', fontsize=12, fontweight='bold')
            
            for ax_idx, (diversity, progress, title) in enumerate(test_points):
                ax = axes[ax_idx]
                ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels, input_set=input_set)
                w_value = ctrl.compute_w(diversity, progress)
                
                ax.bar([1], [w_value], width=0.5, alpha=0.7, color='#0072B2', edgecolor='black')
                ax.set_ylabel('Inertia Weight w', fontsize=11)
                ax.set_title(title, fontsize=11, fontweight='bold')
                ax.set_xticks([])
                ax.set_ylim([0, 1.0])
                ax.grid(axis='y', alpha=0.3, linestyle='--')
                ax.text(1, w_value + 0.05, f'{w_value:.3f}', ha='center', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            output_path = os.path.join(plots_dir, f'09_critical_points_{num_labels}labels_{input_set}.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{num_labels}labels'] = output_path
        except Exception as e:
            print(f"[ERROR] 09 critical individual ({num_labels}): {e}")
            results[f'{num_labels}labels'] = None
    
    return results


def plot_09_critical_points_panel(input_set="I1", num_labels_list=None):
    """Generate panel comparison of critical points across all granularities."""
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    test_points = [
        (0.1, 0.1, "Low Div (Early)"),
        (0.5, 0.5, "Med Div (Mid)"),
        (0.9, 0.9, "High Div (Late)"),
    ]
    
    fig, axes = plt.subplots(len(test_points), len(num_labels_list), figsize=(14, 10))
    fig.suptitle(f'Critical Points: Granularity Comparison ({input_set})', 
                 fontsize=14, fontweight='bold', y=0.995)
    
    for row_idx, (diversity, progress, title) in enumerate(test_points):
        for col_idx, num_labels in enumerate(num_labels_list):
            try:
                ax = axes[row_idx, col_idx]
                ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels, input_set=input_set)
                w_value = ctrl.compute_w(diversity, progress)
                
                ax.bar([1], [w_value], width=0.5, alpha=0.7, color='#0072B2', edgecolor='black', linewidth=1.5)
                ax.set_ylim([0, 1.0])
                ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=0.7)
                ax.text(1, w_value + 0.04, f'{w_value:.3f}', ha='center', fontsize=9, fontweight='bold')
                ax.set_xticks([])
                ax.tick_params(labelsize=9)
                
                if col_idx == 0:
                    ax.set_ylabel(f'{title}\nw', fontsize=10, fontweight='bold')
                if row_idx == 0:
                    ax.set_title(f'{num_labels} Labels', fontsize=11, fontweight='bold')
                if row_idx == len(test_points) - 1:
                    ax.set_xlabel('Operating Point', fontsize=10)
            except Exception as e:
                print(f"[ERROR] 09 critical panel ({num_labels}): {e}")
    
    plt.tight_layout()
    output_path = os.path.join(plots_dir, f'09_critical_points_panel_{input_set}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path


# ==============================================================================
# 10: 3D Surfaces Individual (per granularity × rule_set)
# ==============================================================================

def plot_10_3d_surfaces_individual(input_set="I1", rule_set="R1", num_labels_list=None):
    """Generate individual 3D surface plots for each granularity."""
    plots_dir = ensure_plots_directory()
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    results = {}
    div_range = np.linspace(0.01, 0.99, 35)
    prog_range = np.linspace(0.01, 0.99, 35)
    DIV, PROG = np.meshgrid(div_range, prog_range)
    
    for num_labels in num_labels_list:
        try:
            ctrl = FuzzyInertiaController_Auto('O1', num_labels=num_labels, 
                                              input_set=input_set, rule_set=rule_set)
            W = np.zeros_like(DIV)
            for i in range(DIV.shape[0]):
                for j in range(DIV.shape[1]):
                    W[i, j] = ctrl.compute_w(DIV[i, j], PROG[i, j])
            
            fig = plt.figure(figsize=(10, 8))
            ax = fig.add_subplot(111, projection='3d')
            ax.plot_surface(DIV, PROG, W, cmap='viridis', alpha=0.9, edgecolor='none')
            ax.set_xlabel('Diversity Ratio', fontsize=11, fontweight='bold')
            ax.set_ylabel('Iteration Progress', fontsize=11, fontweight='bold')
            ax.set_zlabel('Inertia Weight w', fontsize=11, fontweight='bold')
            ax.set_title(f'3D Surface: {num_labels} Labels ({rule_set})', fontsize=12, fontweight='bold')
            ax.set_zlim([0, 1])
            ax.tick_params(labelsize=10)
            
            plt.tight_layout()
            output_path = os.path.join(plots_dir, f'10_3d_surface_{num_labels}labels_{input_set}_{rule_set}.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{num_labels}labels'] = output_path
        except Exception as e:
            print(f"[ERROR] 10 3d surface individual ({num_labels}): {e}")
            results[f'{num_labels}labels'] = None
    
    return results


if __name__ == "__main__":
    """Generate all 06-10 plots."""
    print("[*] Generating plots 06-10 (parametric versions)")
    
    # 06: Input Diversity
    print("[06] Input Diversity MF...")
    plot_06_input_diversity_mf_individual()
    plot_06_input_diversity_mf_panel()
    
    # 07: Input Progress
    print("[07] Input Progress MF...")
    plot_07_input_progress_mf_individual()
    plot_07_input_progress_mf_panel()
    
    # 08: Output w
    print("[08] Output w MF...")
    plot_08_output_w_mf_individual()
    plot_08_output_w_mf_panel()
    
    # 09: Critical Points
    print("[09] Critical Points...")
    plot_09_critical_points_individual()
    plot_09_critical_points_panel()
    
    # 10: 3D Surfaces
    print("[10] 3D Surfaces...")
    for rule_set in ["R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"]:
        plot_10_3d_surfaces_individual(rule_set=rule_set)
    
    print("[OK] All plots 06-10 generated!")
