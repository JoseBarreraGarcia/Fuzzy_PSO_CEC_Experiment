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

# Sistema productivo: usar SIEMPRE el controlador parametrico Auto (n ∈ {3,5,7,9}).
# Los modulos _3L / _5L quedan como referencia historica.
from fuzzy_controller_auto import FuzzyInertiaController_Auto, tri


def _make_controller(num_labels, w_set='O1', input_set='I1', rule_set='R1',
                     wMin=0.0, wMax=1.0):
    """Wrapper unico: construye un FuzzyInertiaController_Auto con la granularidad pedida."""
    return FuzzyInertiaController_Auto(
        w_set=w_set, num_labels=int(num_labels), input_set=input_set,
        rule_set=rule_set, wMin=wMin, wMax=wMax,
    )


def FuzzyInertiaController_3L(*args, **kwargs):
    """Compat shim: redirige al controlador Auto con num_labels=3."""
    kwargs.setdefault('num_labels', 3)
    if args and 'w_set' not in kwargs:
        kwargs['w_set'] = args[0]
        args = args[1:]
    return FuzzyInertiaController_Auto(*args, **kwargs)


def FuzzyInertiaController_5L(*args, **kwargs):
    """Compat shim: redirige al controlador Auto con num_labels=5."""
    kwargs.setdefault('num_labels', 5)
    if args and 'w_set' not in kwargs:
        kwargs['w_set'] = args[0]
        args = args[1:]
    return FuzzyInertiaController_Auto(*args, **kwargs)


def _palette_for_labels(labels):
    """Devuelve un dict {label: color} estable para cualquier num_labels."""
    n = len(labels)
    if n == 3:
        base = ['#1f77b4', '#ff7f0e', '#2ca02c']
    elif n == 5:
        base = ['#1f77b4', '#3a8fd3', '#ff7f0e', '#2ca02c', '#0d5a2c']
    else:
        cmap = plt.get_cmap('viridis')
        base = [cmap(i / max(1, n - 1)) for i in range(n)]
    return {lab: base[i] for i, lab in enumerate(labels)}

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
    plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plots')
    os.makedirs(plots_dir, exist_ok=True)
    return plots_dir


def plot_fuzzy_input_diversity(input_set="I1", num_labels_list=None):
    """
    Plot fuzzy sets for Diversity input para cada granularidad pedida.
    Las MFs se obtienen dinamicamente de FuzzyInertiaController_Auto.

    Args:
        input_set: 'I1', 'I2', ...
        num_labels_list: lista de granularidades (default [3, 5]).

    Returns:
        dict {'{N}labels': ruta_png}
    """
    if num_labels_list is None:
        num_labels_list = [3, 5]
    plots_dir = ensure_plots_directory()
    results = {}

    for n in num_labels_list:
        try:
            ctrl = _make_controller(num_labels=n, w_set='O1', input_set=input_set)
            div_mf = ctrl.div_mf

            x = np.linspace(0, 1, 400)
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = _palette_for_labels(list(div_mf.keys()))

            for label, (a, b, c) in div_mf.items():
                mu = [tri(d, a, b, c) for d in x]
                ax.plot(x, mu, label=f'{label} ({a:.2f}, {b:.2f}, {c:.2f})',
                        linewidth=2.5, color=colors[label])
                ax.fill_between(x, mu, alpha=0.2, color=colors[label])

            ax.set_xlabel('Diversity Ratio (0=convergence, 1=exploration)', fontsize=11)
            ax.set_ylabel('Membership Degree', fontsize=11)
            ax.set_title(f'Fuzzy Input Sets: Diversity ({n} Labels, {input_set})',
                         fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=9 if n <= 5 else 8)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1.05])
            plt.tight_layout()

            output_path = os.path.join(
                plots_dir, f'01_fuzzy_input_diversity_{n}labels_{input_set}.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
            plt.close(fig)
            results[f'{n}labels'] = output_path
        except Exception as e:
            print(f"[WARN] Failed to generate {n}-label diversity plot: {e}")
            results[f'{n}labels'] = None

    return results


def plot_fuzzy_input_progress(input_set="I1", num_labels_list=None):
    """
    Plot fuzzy sets for Iteration Progress input para cada granularidad pedida.
    Las MFs se obtienen dinamicamente de FuzzyInertiaController_Auto.

    Args:
        input_set: 'I1', 'I2', ...
        num_labels_list: lista de granularidades (default [3, 5]).

    Returns:
        dict {'{N}labels': ruta_png}
    """
    if num_labels_list is None:
        num_labels_list = [3, 5]
    plots_dir = ensure_plots_directory()
    results = {}

    for n in num_labels_list:
        try:
            ctrl = _make_controller(num_labels=n, w_set='O1', input_set=input_set)
            it_mf = ctrl.it_mf

            x = np.linspace(0, 1, 400)
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = _palette_for_labels(list(it_mf.keys()))

            for label, (a, b, c) in it_mf.items():
                mu = [tri(p, a, b, c) for p in x]
                ax.plot(x, mu, label=f'{label} ({a:.2f}, {b:.2f}, {c:.2f})',
                        linewidth=2.5, color=colors[label])
                ax.fill_between(x, mu, alpha=0.2, color=colors[label])

            ax.set_xlabel('Iteration Progress (0=start, 1=end)', fontsize=11)
            ax.set_ylabel('Membership Degree', fontsize=11)
            ax.set_title(f'Fuzzy Input Sets: Progress ({n} Labels, {input_set})',
                         fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.legend(loc='upper right', fontsize=9 if n <= 5 else 8)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1.05])
            plt.tight_layout()

            output_path = os.path.join(
                plots_dir, f'02_fuzzy_input_progress_{n}labels_{input_set}.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
            plt.close(fig)
            results[f'{n}labels'] = output_path
        except Exception as e:
            print(f"[WARN] Failed to generate {n}-label progress plot: {e}")
            results[f'{n}labels'] = None

    return results


def plot_fuzzy_output_w_set(w_set, num_labels_list=None):
    """
    Plot fuzzy sets for Inertia Weight w output for a specific w_set.
    Itera sobre las granularidades indicadas usando FuzzyInertiaController_Auto.

    Args:
        w_set: 'O1', 'O2', ...
        num_labels_list: lista de granularidades (default [3, 5]).
    
    Returns:
        dict with keys '{N}labels' pointing to generated PNG paths
    """
    if num_labels_list is None:
        num_labels_list = [3, 5]
    plots_dir = ensure_plots_directory()
    results = {}

    for n in num_labels_list:
        try:
            ctrl = _make_controller(num_labels=n, w_set=w_set)
            w_norm = np.linspace(0, 1, 400)
            w_mf = ctrl.w_mf
            wMin = ctrl.wMin
            wMax = ctrl.wMax

            fig, ax = plt.subplots(figsize=(10, 6))
            colors = _palette_for_labels(list(w_mf.keys()))

            for label, (a, b, c) in w_mf.items():
                mu = [tri(w, a, b, c) for w in w_norm]
                w_scaled = wMin + w_norm * (wMax - wMin)
                ax.plot(w_scaled, mu, label=f'{label} ({a:.2f}, {b:.2f}, {c:.2f})',
                        linewidth=2.5, color=colors[label])
                ax.fill_between(w_scaled, mu, alpha=0.2, color=colors[label])

            ax.set_xlabel(f'Inertia Weight $w$ [{wMin:.2f}, {wMax:.2f}]', fontsize=11)
            ax.set_ylabel('Membership Degree', fontsize=11)
            ax.set_title(f'Fuzzy Output Sets ({n} Labels): Inertia Weight - Set {w_set}',
                         fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
            ax.legend(loc='upper right', fontsize=9, ncol=2 if n > 5 else 1)
            ax.set_ylim([0, 1.05])
            plt.tight_layout()

            output_path = os.path.join(
                plots_dir, f'03_fuzzy_output_w_set_{w_set}_{n}labels.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{n}labels'] = output_path
        except Exception as e:
            print(f"[ERROR] Could not generate {n}-label plot for Set {w_set}: {e}")
            results[f'{n}labels'] = None

    return results


def plot_fuzzy_rules_heatmap(rule_set="R1", num_labels_list=None):
    """
    Plot the fuzzy rule base as a heatmap para cada granularidad indicada.
    Para cada (Diversity, Progress), muestra que w_label se activa.

    Args:
        rule_set: 'R1'-'R8'
        num_labels_list: lista de granularidades (default [3, 5]).

    Returns dict {'{N}labels': path}
    """
    if num_labels_list is None:
        num_labels_list = [3, 5]
    plots_dir = ensure_plots_directory()
    results = {}

    for n in num_labels_list:
        try:
            ctrl = _make_controller(num_labels=n, w_set='O1', rule_set=rule_set)
            div_labels = list(ctrl.div_mf.keys())
            prog_labels = list(ctrl.it_mf.keys())
            out_labels = list(ctrl.w_mf.keys())
            label_to_idx = {lab: i for i, lab in enumerate(out_labels)}

            rule_matrix = np.zeros((n, n), dtype=int)
            for (d_lab, t_lab), out_lab in ctrl.rules.items():
                i = div_labels.index(d_lab)
                j = prog_labels.index(t_lab)
                rule_matrix[i, j] = label_to_idx[out_lab]

            fig, ax = plt.subplots(figsize=(max(8, n * 1.3), max(6, n * 1.0)))
            im = ax.imshow(rule_matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=n - 1)
            ax.set_xticks(range(n))
            ax.set_yticks(range(n))
            ax.set_xticklabels(prog_labels, rotation=30, ha='right', fontsize=9)
            ax.set_yticklabels(div_labels, fontsize=9)

            for i in range(n):
                for j in range(n):
                    text = out_labels[int(rule_matrix[i, j])]
                    ax.text(j, i, text, ha='center', va='center',
                            color='black', fontsize=8, fontweight='bold')

            ax.set_xlabel('Iteration Progress', fontsize=12)
            ax.set_ylabel('Diversity Ratio', fontsize=12)
            ax.set_title(f'Fuzzy Rule Base {rule_set} - {n} Labels',
                         fontsize=13, fontweight='bold')

            cbar = plt.colorbar(im, ax=ax, ticks=list(range(n)))
            cbar.set_label('Output w Label', fontsize=11)
            cbar.ax.set_yticklabels(out_labels, fontsize=8)

            plt.tight_layout()
            output_path = os.path.join(
                plots_dir, f'04_fuzzy_rules_heatmap_{n}labels_{rule_set}.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{n}labels'] = output_path
        except Exception as e:
            print(f"[ERROR] Could not generate {n}-label rules heatmap for {rule_set}: {e}")
            results[f'{n}labels'] = None

    return results


def _LEGACY_plot_fuzzy_rules_heatmap(rule_set="R1"):
    """LEGACY (pre-Auto): superseded by plot_fuzzy_rules_heatmap. Kept as a no-op stub."""
    return {}


def _get_available_w_sets(controller_class=None):
    """
    Dynamically get available w_sets from controller class.
    Creates a dummy instance to access W_SETS dictionary.
    """
    try:
        available = []
        builder = controller_class if controller_class is not None else _make_controller
        for w_set_id in ['O1', 'O2', 'O3', 'O4', 'O5', 'O6']:
            try:
                if controller_class is None:
                    builder(num_labels=3, w_set=w_set_id)
                else:
                    builder(w_set_id)
                available.append(w_set_id)
            except Exception:
                pass
        return available if available else ['O1']
    except Exception:
        return ['O1']


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


def _get_available_rule_sets():
    """
    Get available rule sets from FuzzyInertiaController_3L dynamically.
    Probes R1..R20 and returns all that exist.
    """
    try:
        available = []
        for i in range(1, 21):
            rs = f'R{i}'
            try:
                FuzzyInertiaController_3L('O1', rule_set=rs)
                available.append(rs)
            except (ValueError, KeyError):
                pass
        return available if available else ['R1']
    except Exception:
        return ['R1']


def _short_code(label):
    """'very_very_low' -> 'VVL', 'medium_high' -> 'MH'."""
    return ''.join(part[0].upper() for part in str(label).split('_'))


def plot_fuzzy_rules_heatmap_panel(rule_sets=None, num_labels=None):
    """
    Panel plot comparing rule bases across all granularities.
    Full-page portrait layout (2 columns) with shared axis ticks and a single colorbar.

    Args:
        rule_sets: list of rule sets to include (default: all available)
        num_labels: list of granularities (default: [3, 5, 7, 9])

    Returns dict with paths: {'{N}labels': path, ...}
    """
    plots_dir = ensure_plots_directory()
    
    if rule_sets is None:
        rule_sets = _get_available_rule_sets()
    if num_labels is None:
        num_labels = [3, 5, 7, 9]
    
    results = {}
    
    for n in num_labels:
        try:
            ctrl_sample = _make_controller(num_labels=n, w_set='O1', input_set='I1', rule_set='R1')
            diversity_labels = list(ctrl_sample.div_mf.keys())
            progress_labels = list(ctrl_sample.it_mf.keys())
            output_labels_list = list(ctrl_sample.w_mf.keys())

            output_label_to_idx = {label: idx for idx, label in enumerate(output_labels_list)}
            output_text = {idx: _short_code(label) for idx, label in enumerate(output_labels_list)}
            vmax = len(output_labels_list) - 1

            div_codes = [_short_code(l) for l in diversity_labels]
            prog_codes = [_short_code(l) for l in progress_labels]

            # Coarse granularities fit a half-page landscape grid; fine ones need a full page.
            if n <= 5:
                cols, rows, figsize = 4, int(np.ceil(len(rule_sets) / 4)), (7.0, 4.4)
                tick_fs, cell_fs, title_fs = 7, 8, 10
            else:
                cols, rows, figsize = 2, int(np.ceil(len(rule_sets) / 2)), (7.0, 9.3)
                tick_fs, cell_fs, title_fs = 6, 6 if n == 7 else 5, 10
            fig, axes = plt.subplots(rows, cols, figsize=figsize, squeeze=False)
            axes = axes.flatten()


            im = None
            for idx, rs in enumerate(rule_sets):
                if idx >= len(axes):
                    break
                ax = axes[idx]
                ctrl = _make_controller(num_labels=n, w_set='O1', input_set='I1', rule_set=rs)
                
                rule_matrix = np.zeros((len(diversity_labels), len(progress_labels)))
                for i, div_lab in enumerate(diversity_labels):
                    for j, prog_lab in enumerate(progress_labels):
                        out = ctrl.rules.get((div_lab, prog_lab), 'unknown')
                        rule_matrix[i, j] = output_label_to_idx.get(out, -1)
                
                im = ax.imshow(rule_matrix, cmap='RdYlGn_r', aspect='auto', vmin=0, vmax=vmax)
                ax.set_xticks(range(len(progress_labels)))
                ax.set_yticks(range(len(diversity_labels)))

                is_bottom_row = idx >= len(rule_sets) - cols
                is_left_col = idx % cols == 0
                ax.set_xticklabels(prog_codes if is_bottom_row else [], fontsize=tick_fs)
                ax.set_yticklabels(div_codes if is_left_col else [], fontsize=tick_fs)
                ax.tick_params(length=2)
                if is_bottom_row:
                    ax.set_xlabel('Progress', fontsize=8)
                if is_left_col:
                    ax.set_ylabel('Diversity', fontsize=8)

                for i in range(len(diversity_labels)):
                    for j in range(len(progress_labels)):
                        ax.text(j, i, output_text[int(rule_matrix[i, j])],
                                ha="center", va="center", color="black",
                                fontsize=cell_fs, fontweight='bold')
                
                ax.set_title(f'{rs}', fontsize=title_fs, fontweight='bold')

            for idx in range(len(rule_sets), len(axes)):
                axes[idx].set_visible(False)

            if n <= 5:
                fig.subplots_adjust(left=0.08, right=0.98, top=0.84, bottom=0.18,
                                    hspace=0.30, wspace=0.12)
            else:
                fig.subplots_adjust(left=0.09, right=0.98, top=0.93, bottom=0.10,
                                    hspace=0.22, wspace=0.10)
            if im is not None:
                cax = fig.add_axes((0.15, 0.035, 0.70, 0.014))
                cbar = fig.colorbar(im, cax=cax, orientation='horizontal',
                                    ticks=list(range(len(output_labels_list))))
                cbar.set_label('Output inertia weight label w', fontsize=8)
                cbar.ax.set_xticklabels(
                    [f'{_short_code(l)} = {l}' if n <= 3 else _short_code(l)
                     for l in output_labels_list], fontsize=6)
                cbar.ax.tick_params(length=2)

            output_path = os.path.join(plots_dir, f'04_fuzzy_rules_panel_{n}labels.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{n}labels'] = output_path
        except Exception as e:
            print(f"[WARN] Failed to generate rules heatmap panel for {n} labels: {e}")
            results[f'{n}labels'] = None
    
    return results


def plot_all_w_sets_comparison(num_labels_list=None):
    """
    Create comparison plots showing all available w_sets side by side for ALL granularities.
    Uses FuzzyInertiaController_Auto to support [3, 5, 7, 9] labels.
    Dynamically adjusts grid layout based on number of available sets.
    Shows how output w varies for each set.
    Returns dict with paths: {'{N}labels': path, ...}
    """
    if num_labels_list is None:
        num_labels_list = [3, 5, 7, 9]
    
    plots_dir = ensure_plots_directory()
    results = {}
    
    for num_labels in num_labels_list:
        try:
            ctrl = _make_controller(num_labels=num_labels, w_set='O1', input_set='I1')
            w_sets = _get_available_w_sets(ctrl)
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
            colors = _palette_for_labels(ctrl.w_mf.keys())
            
            for idx, w_set in enumerate(w_sets):
                try:
                    controller = _make_controller(num_labels=num_labels, w_set=w_set, 
                                                  input_set='I1', wMin=0.0, wMax=1.0)
                except ValueError:
                    axes_flat[idx].text(0.5, 0.5, f'Set {w_set} not defined', 
                                       ha='center', va='center', fontsize=12)
                    axes_flat[idx].axis('off')
                    continue
                
                ax = axes_flat[idx]
                w_norm = np.linspace(0, 1, 400)
                w_mf = controller.w_mf
                wMin = controller.wMin
                wMax = controller.wMax
                
                for label, (a, b, c) in w_mf.items():
                    mu = [tri(w, a, b, c) for w in w_norm]
                    w_scaled = wMin + w_norm * (wMax - wMin)
                    ax.plot(w_scaled, mu, label=label, linewidth=2.5, color=colors.get(label, '#000000'))
                    ax.fill_between(w_scaled, mu, alpha=0.15, color=colors.get(label, '#000000'))
                
                ax.set_title(f'Set {w_set}', fontsize=11, fontweight='bold')
                ax.set_xlabel(f'w [{wMin:.2f}, {wMax:.2f}]', fontsize=10)
                ax.set_ylabel('Membership Degree', fontsize=10)
                ax.grid(True, alpha=0.3)
                ax.set_ylim([0, 1.05])
                ax.legend(fontsize=8, loc='upper right')
            
            # Hide unused subplots
            for idx in range(len(w_sets), len(axes_flat)):
                axes_flat[idx].axis('off')
            
            sets_str = ", ".join(w_sets)
            fig.suptitle(f'Fuzzy Inertia Weight Sets Comparison - {num_labels} Labels (O1) - {sets_str}', 
                         fontsize=12, fontweight='bold', y=0.995)
            plt.tight_layout()
            
            output_path = os.path.join(plots_dir, f'05_fuzzy_w_sets_comparison_{num_labels}labels.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
            plt.close(fig)
            
            results[f'{num_labels}labels'] = output_path
        except Exception as e:
            print(f"[WARN] Failed to generate w_sets comparison for {num_labels} labels: {e}")
            results[f'{num_labels}labels'] = None
    
    return results


def plot_output_w_comparison_membership_functions():
    """
    Generate comparison of OUTPUT (w) membership functions for 3 and 5 labels across fuzzy sets.
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w_3L import FuzzyInertiaController_3L
    from fuzzy_controller_w_5L import FuzzyInertiaController_5L
    
    # Dynamically detect available w_sets
    sets = _get_available_w_sets(FuzzyInertiaController_3L)
    if not sets:
        sets = ['O1']  # Fallback to A if nothing available
    
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
        ctrl3 = FuzzyInertiaController_3L(w_set=w_set)
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
        ctrl5 = FuzzyInertiaController_5L(w_set=w_set)
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


def plot_input_diversity_comparison_membership_functions(input_set="I1"):
    """
    Generate comparison of INPUT (Diversity) membership functions for 3 and 5 labels.
    Single figure showing 3-label vs 5-label comparison (NOT multiple fuzzy sets).
    
    Args:
        input_set: 'I1', 'I2', 'I3', or 'I4' (CLEI2026 input MF configuration)
    
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w_3L import FuzzyInertiaController_3L
    from fuzzy_controller_w_5L import FuzzyInertiaController_5L
    
    # Create figure with 2 subplots: 3-label on top, 5-label on bottom
    fig, axes = plt.subplots(2, 1, figsize=(8, 10))
    
    # ===== TOP: 3-LABEL VERSION =====
    ax = axes[0]
    ctrl3 = FuzzyInertiaController_3L(w_set='O1', input_set=input_set)
    
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
    ctrl5 = FuzzyInertiaController_5L(w_set='O1', input_set=input_set)
    
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
    output_path = os.path.join(plots_dir, f'06_input_diversity_comparison_membership_functions_{input_set}.png')
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    return output_path


def plot_input_progress_comparison_membership_functions(input_set="I1"):
    """
    Generate comparison of INPUT (Progress) membership functions for 3 and 5 labels.
    Single figure showing 3-label vs 5-label comparison (NOT multiple fuzzy sets).
    
    Args:
        input_set: 'I1', 'I2', 'I3', or 'I4' (CLEI2026 input MF configuration)
    
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w_3L import FuzzyInertiaController_3L
    from fuzzy_controller_w_5L import FuzzyInertiaController_5L
    
    # Create figure with 2 subplots: 3-label on top, 5-label on bottom
    fig, axes = plt.subplots(2, 1, figsize=(8, 10))
    
    # ===== TOP: 3-LABEL VERSION =====
    ax = axes[0]
    ctrl3 = FuzzyInertiaController_3L(w_set='O1', input_set=input_set)
    
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
    ctrl5 = FuzzyInertiaController_5L(w_set='O1', input_set=input_set)
    
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
    output_path = os.path.join(plots_dir, f'06_input_progress_comparison_membership_functions_{input_set}.png')
    plt.savefig(output_path, dpi=300)
    plt.close(fig)
    
    return output_path


def plot_comparison_critical_points(input_set="I1"):
    """
    Create bar charts comparing inertia weights at critical points (3 vs 5 labels).
    
    Args:
        input_set: 'I1', 'I2', 'I3', or 'I4' (CLEI2026 input MF configuration)
    
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w_3L import FuzzyInertiaController_3L
    from fuzzy_controller_w_5L import FuzzyInertiaController_5L
    
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
        sets = _get_available_w_sets(FuzzyInertiaController_3L)
        if not sets:
            sets = ['O1']  # Fallback
        x_pos = np.arange(len(sets))
        w3_values = []
        w5_values = []
        
        for w_set in sets:
            ctrl3 = FuzzyInertiaController_3L(w_set=w_set, input_set=input_set)
            ctrl5 = FuzzyInertiaController_5L(w_set=w_set, input_set=input_set)
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
    output_path = os.path.join(plots_dir, f'07_comparison_critical_points_{input_set}.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    return output_path


def plot_3d_comparison(input_set="I1", rule_set="R1"):
    """
    Create 3D surface comparison between 3-label and 5-label controllers for all available sets.
    Generates one plot per set.
    Each plot includes: 3D 3-labels, 3D 5-labels, and difference contour.
    
    Args:
        input_set: 'I1', 'I2', 'I3', or 'I4' (CLEI2026 input MF configuration)
        rule_set: 'R1'-'R8' (WEA2026 rule base variant)
    
    Returns list of paths to the 3D comparison plots.
    """
    plots_dir = ensure_plots_directory()
    
    from fuzzy_controller_w_3L import FuzzyInertiaController_3L
    from fuzzy_controller_w_5L import FuzzyInertiaController_5L
    
    # Dynamically detect available w_sets
    sets = _get_available_w_sets(FuzzyInertiaController_3L)
    if not sets:
        sets = ['O1']  # Fallback
    div_range = np.linspace(0.01, 0.99, 40)
    prog_range = np.linspace(0.01, 0.99, 40)
    DIV, PROG = np.meshgrid(div_range, prog_range)
    
    output_paths = []
    
    for w_set in sets:
        ctrl3 = FuzzyInertiaController_3L(w_set=w_set, input_set=input_set, rule_set=rule_set)
        ctrl5 = FuzzyInertiaController_5L(w_set=w_set, input_set=input_set, rule_set=rule_set)
        
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
        output_path = os.path.join(plots_dir, f'08_3d_surface_comparison_set_{w_set}_{input_set}_{rule_set}.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        
        output_paths.append(output_path)
    
    return output_paths


# ==================================================================================
# CLEI2026: Input Set Comparison Plots (I1 vs I2 vs I3 vs I4)
# ==================================================================================

INPUT_SETS_LIST = ['I1', 'I2', 'I3', 'I4']
INPUT_SET_NAMES = {
    'I1': 'Standard',
    'I2': 'Narrow',
    'I3': 'Wide',
    'I4': 'Shoulder',
}


def plot_all_input_sets_diversity_comparison():
    """
    CLEI2026 key plot: Compare all 4 input sets (I1-I4) for the Diversity variable.
    Generates a 2×4 grid: top row = 3-label, bottom row = 5-label, columns = I1..I4.
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()

    from fuzzy_controller_w_3L import FuzzyInertiaController_3L, tri
    from fuzzy_controller_w_5L import FuzzyInertiaController_5L

    fig = plt.figure(figsize=(16, 8))
    fig.suptitle('Input MF Comparison: Diversity Variable (I1-I4)', fontsize=14, fontweight='bold', y=0.98)

    x = np.linspace(0, 1, 300)
    colors_3 = ['#1f77b4', '#ff7f0e', '#2ca02c']
    labels_3 = ['low', 'medium', 'high']
    colors_5 = ['#0072B2', '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    labels_5 = ['very_low', 'low', 'medium', 'high', 'very_high']
    labels_5_display = ['very low', 'low', 'medium', 'high', 'very high']

    for col, iset in enumerate(INPUT_SETS_LIST):
        # Top row: 3-label
        ax = fig.add_subplot(2, 4, col + 1)
        ctrl3 = FuzzyInertiaController_3L(w_set='O1', input_set=iset)
        for label, color in zip(labels_3, colors_3):
            a, b, c = ctrl3.div_mf[label]
            y = [tri(d, a, b, c) for d in x]
            ax.plot(x, y, label=label, linewidth=2, color=color)
            ax.fill_between(x, y, alpha=0.15, color=color)
        ax.set_title(f'{iset} - {INPUT_SET_NAMES[iset]}', fontsize=11, fontweight='bold')
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(labelsize=9)
        if col == 0:
            ax.set_ylabel('3-Label\nMembership', fontsize=10, fontweight='bold')

        # Bottom row: 5-label
        ax = fig.add_subplot(2, 4, col + 5)
        ctrl5 = FuzzyInertiaController_5L(w_set='O1', input_set=iset)
        for lk, ld, color in zip(labels_5, labels_5_display, colors_5):
            a, b, c = ctrl5.div_mf[lk]
            y = [tri(d, a, b, c) for d in x]
            ax.plot(x, y, label=ld, linewidth=2, color=color)
            ax.fill_between(x, y, alpha=0.15, color=color)
        ax.set_xlabel('Diversity Ratio', fontsize=10)
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(labelsize=9)
        if col == 0:
            ax.set_ylabel('5-Label\nMembership', fontsize=10, fontweight='bold')

    # Add shared legends
    handles_3 = [plt.Line2D([0], [0], color=c, lw=2) for c in colors_3]
    handles_5 = [plt.Line2D([0], [0], color=c, lw=2) for c in colors_5]
    fig.legend(handles_3, labels_3, loc='lower left', ncol=3, fontsize=9,
               bbox_to_anchor=(0.02, 0.01), framealpha=0.9, title='3-Label')
    fig.legend(handles_5, labels_5_display, loc='lower right', ncol=5, fontsize=9,
               bbox_to_anchor=(0.98, 0.01), framealpha=0.9, title='5-Label')

    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    output_path = os.path.join(plots_dir, '09_input_sets_diversity_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path


def plot_all_input_sets_progress_comparison():
    """
    CLEI2026 key plot: Compare all 4 input sets (I1-I4) for the Progress variable.
    Generates a 2×4 grid: top row = 3-label, bottom row = 5-label, columns = I1..I4.
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()

    from fuzzy_controller_w_3L import FuzzyInertiaController_3L, tri
    from fuzzy_controller_w_5L import FuzzyInertiaController_5L

    fig = plt.figure(figsize=(16, 8))
    fig.suptitle('Input MF Comparison: Progress Variable (I1-I4)', fontsize=14, fontweight='bold', y=0.98)

    x = np.linspace(0, 1, 300)
    colors_3 = ['#d62728', '#9467bd', '#17becf']
    labels_3 = ['early', 'mid', 'late']
    colors_5 = ['#8B0000', '#d62728', '#9467bd', '#17becf', '#1f77b4']
    labels_5 = ['very_early', 'early', 'mid', 'late', 'very_late']
    labels_5_display = ['very early', 'early', 'mid', 'late', 'very late']

    for col, iset in enumerate(INPUT_SETS_LIST):
        # Top row: 3-label
        ax = fig.add_subplot(2, 4, col + 1)
        ctrl3 = FuzzyInertiaController_3L(w_set='O1', input_set=iset)
        for label, color in zip(labels_3, colors_3):
            a, b, c = ctrl3.it_mf[label]
            y = [tri(d, a, b, c) for d in x]
            ax.plot(x, y, label=label, linewidth=2, color=color)
            ax.fill_between(x, y, alpha=0.15, color=color)
        ax.set_title(f'{iset} - {INPUT_SET_NAMES[iset]}', fontsize=11, fontweight='bold')
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(labelsize=9)
        if col == 0:
            ax.set_ylabel('3-Label\nMembership', fontsize=10, fontweight='bold')

        # Bottom row: 5-label
        ax = fig.add_subplot(2, 4, col + 5)
        ctrl5 = FuzzyInertiaController_5L(w_set='O1', input_set=iset)
        for lk, ld, color in zip(labels_5, labels_5_display, colors_5):
            a, b, c = ctrl5.it_mf[lk]
            y = [tri(d, a, b, c) for d in x]
            ax.plot(x, y, label=ld, linewidth=2, color=color)
            ax.fill_between(x, y, alpha=0.15, color=color)
        ax.set_xlabel('Iteration Progress', fontsize=10)
        ax.set_xlim([-0.02, 1.02])
        ax.set_ylim([0, 1.1])
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.tick_params(labelsize=9)
        if col == 0:
            ax.set_ylabel('5-Label\nMembership', fontsize=10, fontweight='bold')

    # Add shared legends
    handles_3 = [plt.Line2D([0], [0], color=c, lw=2) for c in colors_3]
    handles_5 = [plt.Line2D([0], [0], color=c, lw=2) for c in colors_5]
    fig.legend(handles_3, labels_3, loc='lower left', ncol=3, fontsize=9,
               bbox_to_anchor=(0.02, 0.01), framealpha=0.9, title='3-Label')
    fig.legend(handles_5, labels_5_display, loc='lower right', ncol=5, fontsize=9,
               bbox_to_anchor=(0.98, 0.01), framealpha=0.9, title='5-Label')

    plt.tight_layout(rect=[0, 0.05, 1, 0.96])
    output_path = os.path.join(plots_dir, '09_input_sets_progress_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path


def plot_all_input_sets_3d_surface(rule_set="R1"):
    """
    CLEI2026 key plot: 3D w surfaces for all 4 input sets (I1-I4) with fixed w_set='O1'.
    Shows how different input MF shapes affect the output w surface.
    Generates a 1×4 grid of 3D surfaces (3-label controller only for clarity).
    
    Args:
        rule_set: 'R1'-'R8' (WEA2026 rule base variant)
    
    Returns path to the comparison plot.
    """
    plots_dir = ensure_plots_directory()

    from fuzzy_controller_w_3L import FuzzyInertiaController_3L

    fig = plt.figure(figsize=(18, 5))
    fig.suptitle(f'Inertia Weight Surface: Input Set Comparison (w_set=A, 3-Label, {rule_set})',
                 fontsize=13, fontweight='bold', y=1.02)

    div_range = np.linspace(0.01, 0.99, 35)
    prog_range = np.linspace(0.01, 0.99, 35)
    DIV, PROG = np.meshgrid(div_range, prog_range)

    for col, iset in enumerate(INPUT_SETS_LIST):
        ctrl = FuzzyInertiaController_3L(w_set='O1', input_set=iset, rule_set=rule_set)
        W = np.zeros_like(DIV)
        for i in range(DIV.shape[0]):
            for j in range(DIV.shape[1]):
                W[i, j] = ctrl.compute_w(DIV[i, j], PROG[i, j])

        ax = fig.add_subplot(1, 4, col + 1, projection='3d')
        ax.plot_surface(DIV, PROG, W, cmap='viridis', alpha=0.85, edgecolor='none')
        ax.set_xlabel('Diversity', fontsize=9)
        ax.set_ylabel('Progress', fontsize=9)
        ax.set_zlabel('w', fontsize=9)
        ax.set_title(f'{iset} - {INPUT_SET_NAMES[iset]}', fontsize=11, fontweight='bold')
        ax.set_zlim([0, 1])
        ax.tick_params(labelsize=8)

    plt.tight_layout()
    output_path = os.path.join(plots_dir, '10_input_sets_3d_surface_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    return output_path


def plot_3d_surface_panel(rule_sets=None, num_labels=None, input_set="I1",
                          w_min=0.0, w_max=1.0):
    """
    Panel plot comparing 3D w surfaces for all rule sets side by side.
    Generates a grid of 3D surfaces for each num_labels variant using FuzzyInertiaController_Auto.
    
    Args:
        rule_sets: list of rule sets to include (default: all available)
        num_labels: list of granularities (default: [3, 5, 7, 9])
        input_set: input set to use (default: 'I1')
    
    Returns dict with paths: {'{N}labels': path, ...}
    """
    plots_dir = ensure_plots_directory()
    
    if rule_sets is None:
        rule_sets = _get_available_rule_sets()
    if num_labels is None:
        num_labels = [3, 5, 7, 9]
    
    div_range = np.linspace(0.01, 0.99, 35)
    prog_range = np.linspace(0.01, 0.99, 35)
    DIV, PROG = np.meshgrid(div_range, prog_range)
    
    results = {}
    
    for n in num_labels:
        try:
            cols = 2
            rows = int(np.ceil(len(rule_sets) / cols))
            fig = plt.figure(figsize=(7.0, 9.3))

            surf = None
            for idx, rs in enumerate(rule_sets):
                ctrl = _make_controller(num_labels=n, w_set='O1', input_set=input_set,
                                        rule_set=rs, wMin=w_min, wMax=w_max)
                W = np.zeros_like(DIV)
                for i in range(DIV.shape[0]):
                    for j in range(DIV.shape[1]):
                        W[i, j] = ctrl.compute_w(DIV[i, j], PROG[i, j])
                
                ax = fig.add_subplot(rows, cols, idx + 1, projection='3d')
                surf = ax.plot_surface(DIV, PROG, W, cmap='viridis', alpha=0.9,
                                       edgecolor='none', vmin=w_min, vmax=w_max)
                ax.set_xlabel('Diversity', fontsize=8, labelpad=-4)
                ax.set_ylabel('Progress', fontsize=8, labelpad=-4)
                ax.set_zlabel('w', fontsize=8, labelpad=-6)
                ax.set_title(f'{rs}', fontsize=10, fontweight='bold')
                ax.set_zlim([w_min, w_max])
                ax.tick_params(labelsize=6, pad=-2)

            fig.subplots_adjust(left=0.02, right=0.98, top=0.94, bottom=0.08,
                                hspace=0.32, wspace=0.05)
            if surf is not None:
                cax = fig.add_axes((0.20, 0.035, 0.60, 0.012))
                cbar = fig.colorbar(surf, cax=cax, orientation='horizontal')
                cbar.set_label('Inertia weight w', fontsize=8)
                cbar.ax.tick_params(labelsize=6, length=2)

            output_path = os.path.join(plots_dir, f'11_3d_surface_panel_{n}labels_{input_set}.png')
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            results[f'{n}labels'] = output_path
        except Exception as e:
            print(f"[WARN] Failed to generate 3D surface panel for {n} labels: {e}")
            results[f'{n}labels'] = None
    
    return results


def _load_fuzzy_plots_config():
    """
    Load fuzzy plots configuration from config/fuzzy_plots.json.
    Returns default config if file not found.
    """
    import json
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'config', 'fuzzy_plots.json')
    
    default_config = {
        "rule_sets": ["R1"],
        "w_sets": "auto",
        "input_sets": ["I1"],
        "num_labels": [3, 5],
        "plots": {
            "input_diversity": True,
            "input_progress": True,
            "output_w_sets": True,
            "rules_heatmap_individual": True,
            "rules_heatmap_panel": False,
            "w_sets_comparison": True,
            "input_mf_comparison_3vs5": True,
            "critical_points": True,
            "surface_3d_individual": True,
            "surface_3d_panel": False,
            "input_sets_comparison": False,
            "set_comparison_matrices": False,
        }
    }
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        # Remove _comentarios key if present
        config.pop('_comentarios', None)
        # Merge with defaults for any missing keys
        for key, value in default_config.items():
            if key not in config:
                config[key] = value
            elif key == 'plots' and isinstance(value, dict):
                for pk, pv in value.items():
                    if pk not in config['plots']:
                        config['plots'][pk] = pv
        return config
    except (FileNotFoundError, json.JSONDecodeError):
        return default_config


def _collect_dict_results(result, outputs, verbose, label):
    """Helper to collect results from functions that return dict keyed by '{N}labels'."""
    if isinstance(result, dict):
        def _sort_key(k):
            try:
                return int(str(k).replace('labels', ''))
            except ValueError:
                return 10**6
        for key in sorted(result.keys(), key=_sort_key):
            if result.get(key):
                outputs.append(result[key])
                if verbose:
                    print(f"[OK] {label} ({key}): {result[key]}")
    elif result:
        outputs.append(result)
        if verbose:
            print(f"[OK] {label}: {result}")


def generate_all_fuzzy_plots(verbose=False, config=None):
    """
    Generate all fuzzy set visualizations based on config/fuzzy_plots.json.
    
    Args:
        verbose: Print progress messages
        config: Optional config dict override (if None, loads from file)
    """
    plots_dir = ensure_plots_directory()
    
    if config is None:
        config = _load_fuzzy_plots_config()
    
    rule_sets = config.get('rule_sets', ['R1'])
    input_sets = config.get('input_sets', ['I1'])
    num_labels = config.get('num_labels', [3, 5])
    plots_cfg = config.get('plots', {})
    
    # Resolve w_sets
    w_sets_cfg = config.get('w_sets', 'auto')
    if w_sets_cfg == 'auto':
        w_sets = _get_available_w_sets(None)
    else:
        w_sets = w_sets_cfg
    
    if verbose:
        print("\n[*] Generating Fuzzy Set Visualizations")
        print(f"    Config: rule_sets={rule_sets}, w_sets={w_sets}, input_sets={input_sets}, num_labels={num_labels}")
        print("=" * 70)
    
    outputs = []
    primary_input_set = input_sets[0] if input_sets else 'I1'
    
    # ===== Input MF plots (don't depend on rule_set) =====
    if plots_cfg.get('input_diversity', True):
        for iset in input_sets:
            try:
                result = plot_fuzzy_input_diversity(input_set=iset, num_labels_list=num_labels)
                _collect_dict_results(result, outputs, verbose, f"Diversity input ({iset})")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] Diversity plot {iset} failed: {e}")
    
    if plots_cfg.get('input_progress', True):
        for iset in input_sets:
            try:
                result = plot_fuzzy_input_progress(input_set=iset, num_labels_list=num_labels)
                _collect_dict_results(result, outputs, verbose, f"Progress input ({iset})")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] Progress plot {iset} failed: {e}")
    
    # ===== Output MF plots (don't depend on rule_set) =====
    if plots_cfg.get('output_w_sets', True):
        for w_set in w_sets:
            try:
                result = plot_fuzzy_output_w_set(w_set, num_labels_list=num_labels)
                _collect_dict_results(result, outputs, verbose, f"Output w (Set {w_set})")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] w_set {w_set} plot failed: {e}")
    
    # ===== Rules heatmaps: individual (per rule_set) =====
    if plots_cfg.get('rules_heatmap_individual', True):
        for rs in rule_sets:
            try:
                result = plot_fuzzy_rules_heatmap(rule_set=rs, num_labels_list=num_labels)
                _collect_dict_results(result, outputs, verbose, f"Rules heatmap ({rs})")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] Rules heatmap {rs} failed: {e}")
    
    # ===== Rules heatmaps: panel (all rule_sets side by side) =====
    if plots_cfg.get('rules_heatmap_panel', False):
        try:
            result = plot_fuzzy_rules_heatmap_panel(rule_sets=rule_sets, num_labels=num_labels)
            _collect_dict_results(result, outputs, verbose, "Rules heatmap panel")
        except Exception as e:
            if verbose:
                print(f"[ERROR] Rules heatmap panel failed: {e}")
    
    # ===== w_sets comparison (don't depend on rule_set) =====
    if plots_cfg.get('w_sets_comparison', True):
        try:
            result = plot_all_w_sets_comparison()
            _collect_dict_results(result, outputs, verbose, "All w_sets comparison")
        except Exception as e:
            if verbose:
                print(f"[ERROR] w_sets comparison failed: {e}")
    
    # ===== NEW 06: Input Diversity MF Comparison [3,5,7,9] =====
    if plots_cfg.get('input_diversity_mf', True):
        from fuzzy_plots_06_10_parametric import (
            plot_06_input_diversity_mf_individual,
            plot_06_input_diversity_mf_panel
        )
        for iset in input_sets:
            try:
                result = plot_06_input_diversity_mf_individual(input_set=iset, num_labels_list=num_labels)
                _collect_dict_results(result, outputs, verbose, f"06: Diversity MF individual ({iset})")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] 06 Diversity MF individual {iset} failed: {e}")
            
            try:
                path = plot_06_input_diversity_mf_panel(input_set=iset, num_labels_list=num_labels)
                outputs.append(path)
                if verbose:
                    print(f"[OK] 06: Diversity MF panel ({iset}): {path}")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] 06 Diversity MF panel {iset} failed: {e}")
    
    # ===== NEW 07: Input Progress MF Comparison [3,5,7,9] =====
    if plots_cfg.get('input_progress_mf', True):
        from fuzzy_plots_06_10_parametric import (
            plot_07_input_progress_mf_individual,
            plot_07_input_progress_mf_panel
        )
        for iset in input_sets:
            try:
                result = plot_07_input_progress_mf_individual(input_set=iset, num_labels_list=num_labels)
                _collect_dict_results(result, outputs, verbose, f"07: Progress MF individual ({iset})")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] 07 Progress MF individual {iset} failed: {e}")
            
            try:
                path = plot_07_input_progress_mf_panel(input_set=iset, num_labels_list=num_labels)
                outputs.append(path)
                if verbose:
                    print(f"[OK] 07: Progress MF panel ({iset}): {path}")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] 07 Progress MF panel {iset} failed: {e}")
    
    # ===== NEW 08: Output w MF Comparison [3,5,7,9] =====
    if plots_cfg.get('output_w_mf', True):
        from fuzzy_plots_06_10_parametric import (
            plot_08_output_w_mf_individual,
            plot_08_output_w_mf_panel
        )
        try:
            result = plot_08_output_w_mf_individual(num_labels_list=num_labels)
            _collect_dict_results(result, outputs, verbose, "08: Output w MF individual")
        except Exception as e:
            if verbose:
                print(f"[ERROR] 08 Output w MF individual failed: {e}")
        
        try:
            path = plot_08_output_w_mf_panel(num_labels_list=num_labels)
            outputs.append(path)
            if verbose:
                print(f"[OK] 08: Output w MF panel: {path}")
        except Exception as e:
            if verbose:
                print(f"[ERROR] 08 Output w MF panel failed: {e}")
    
    # ===== NEW 09: Critical Points Comparison [3,5,7,9] =====
    if plots_cfg.get('critical_points_mf', True):
        from fuzzy_plots_06_10_parametric import (
            plot_09_critical_points_individual,
            plot_09_critical_points_panel
        )
        for iset in input_sets:
            try:
                result = plot_09_critical_points_individual(input_set=iset, num_labels_list=num_labels)
                _collect_dict_results(result, outputs, verbose, f"09: Critical points individual ({iset})")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] 09 Critical points individual {iset} failed: {e}")
            
            try:
                path = plot_09_critical_points_panel(input_set=iset, num_labels_list=num_labels)
                outputs.append(path)
                if verbose:
                    print(f"[OK] 09: Critical points panel ({iset}): {path}")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] 09 Critical points panel {iset} failed: {e}")
    
    # ===== NEW 10: 3D Surfaces Individual [3,5,7,9] per rule_set =====
    if plots_cfg.get('surface_3d_individual', True):
        from fuzzy_plots_06_10_parametric import plot_10_3d_surfaces_individual
        for iset in input_sets:
            for rs in rule_sets:
                try:
                    result = plot_10_3d_surfaces_individual(input_set=iset, rule_set=rs, num_labels_list=num_labels)
                    _collect_dict_results(result, outputs, verbose, f"10: 3D Surface ({iset}, {rs})")
                except Exception as e:
                    if verbose:
                        print(f"[ERROR] 10 3D Surface {iset} {rs} failed: {e}")
    
    # ===== 3D Surface: panel (all rule_sets side by side) =====
    if plots_cfg.get('surface_3d_panel', False):
        for iset in input_sets:
            try:
                result = plot_3d_surface_panel(rule_sets=rule_sets, num_labels=num_labels, input_set=iset)
                _collect_dict_results(result, outputs, verbose, f"3D Surface panel ({iset})")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] 3D Surface panel {iset} failed: {e}")
    
    # ===== CLEI2026: Input Set Comparison Plots (only if multiple input_sets configured) =====
    if plots_cfg.get('input_sets_comparison', False):
        try:
            path = plot_all_input_sets_diversity_comparison()
            outputs.append(path)
            if verbose:
                print(f"[OK] Input sets diversity comparison (I1-I4): {path}")
        except Exception as e:
            if verbose:
                print(f"[ERROR] Input sets diversity comparison failed: {e}")
        
        try:
            path = plot_all_input_sets_progress_comparison()
            outputs.append(path)
            if verbose:
                print(f"[OK] Input sets progress comparison (I1-I4): {path}")
        except Exception as e:
            if verbose:
                print(f"[ERROR] Input sets progress comparison failed: {e}")
        
        for rs in rule_sets:
            try:
                path = plot_all_input_sets_3d_surface(rule_set=rs)
                outputs.append(path)
                if verbose:
                    print(f"[OK] Input sets 3D surface ({rs}): {path}")
            except Exception as e:
                if verbose:
                    print(f"[ERROR] Input sets 3D surface {rs} failed: {e}")
    
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




