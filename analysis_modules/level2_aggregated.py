"""
LEVEL 2: AGGREGATED ANALYSIS (Descriptive Statistics & Plots)

Análisis agregado con tablas de estadísticas descriptivas y gráficos agregados.
Presenta los resultados a nivel de MH, sin desagregar por instancia específica.

Output:
  Resultados/resumen/level2_aggregated/
    - descriptive_stats_by_mh.csv         (media, max, min, range, std, CV)
    - descriptive_stats_by_instance.csv   (por instancia)
    - plots/fitness/          (boxplot + violin por instancia+binarización)
    - plots/time/             (boxplot + violin por instancia+binarización)
    - plots/xpl_xpt/evolution/ (30 gráficos XPL + XPT juntos)
    - plots/w/evolution/      (30 gráficos w individual)
    - plots/div/evolution/    (30 gráficos DIV individual)
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
import seaborn as sns
from scipy import stats

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis_modules.level1_raw_data import extract_experiments_data

# LNCS style configuration
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['font.serif'] = ['Times New Roman']
mpl.rcParams['font.size'] = 10


def ensure_directories():
    """Crear directorios para level 2."""
    base_dir = 'Resultados/resumen/level2_aggregated'
    plots_dir = os.path.join(base_dir, 'plots')
    
    # Crear subdirectorios por métrica
    fitness_dir = os.path.join(plots_dir, 'fitness')
    time_dir = os.path.join(plots_dir, 'time')
    xpl_xpt_dir = os.path.join(plots_dir, 'xpl_xpt')
    
    os.makedirs(fitness_dir, exist_ok=True)
    os.makedirs(time_dir, exist_ok=True)
    os.makedirs(xpl_xpt_dir, exist_ok=True)
    
    return base_dir, plots_dir, fitness_dir, time_dir, xpl_xpt_dir


def coefficient_of_variation(series):
    """Coeficiente de variación (CV) = std / mean * 100."""
    mean_val = series.mean()
    if mean_val == 0:
        return np.nan
    return (series.std() / mean_val) * 100


def generate_descriptive_stats_by_mh(df, verbose=False):
    """
    Genera tabla de estadísticas descriptivas por MH.
    
    Estadísticas:
    - count, mean, min, max, range, std, CV (coeficiente variación)
    """
    if df is None or len(df) == 0:
        if verbose:
            print("[WARN] No data for descriptive stats")
        return None
    
    base_dir, _, _, _, _ = ensure_directories()
    
    # Agrupar por MH y calcular estadísticas
    stats_by_mh = []
    
    for mh in df['MH'].unique():
        mh_data = df[df['MH'] == mh]['fitness'].dropna()
        
        if len(mh_data) == 0:
            continue
        
        stats_dict = {
            'MH': mh,
            'Count': len(mh_data),
            'Mean': mh_data.mean(),
            'Median': mh_data.median(),
            'Min': mh_data.min(),
            'Max': mh_data.max(),
            'Range': mh_data.max() - mh_data.min(),
            'Std': mh_data.std(),
            'CV%': coefficient_of_variation(mh_data),
            'Q1': mh_data.quantile(0.25),
            'Q3': mh_data.quantile(0.75),
            'IQR': mh_data.quantile(0.75) - mh_data.quantile(0.25),
        }
        stats_by_mh.append(stats_dict)
    
    df_stats = pd.DataFrame(stats_by_mh)
    csv_path = os.path.join(base_dir, 'descriptive_stats_by_mh.csv')
    df_stats.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Descriptive stats by MH -> {csv_path}")
        print(df_stats.to_string())
    
    return df_stats


def generate_descriptive_stats_by_instance(df, verbose=False):
    """
    Genera tabla de estadísticas descriptivas por instancia.
    """
    if df is None or len(df) == 0:
        if verbose:
            print("[WARN] No data for instance stats")
        return None
    
    base_dir, _, _, _, _ = ensure_directories()
    
    stats_by_inst = []
    
    for inst in df['instancia_nombre'].unique():
        inst_data = df[df['instancia_nombre'] == inst]['fitness'].dropna()
        
        if len(inst_data) == 0:
            continue
        
        stats_dict = {
            'Instance': inst,
            'Count': len(inst_data),
            'Mean': inst_data.mean(),
            'Median': inst_data.median(),
            'Min': inst_data.min(),
            'Max': inst_data.max(),
            'Std': inst_data.std(),
            'CV%': coefficient_of_variation(inst_data),
        }
        stats_by_inst.append(stats_dict)
    
    df_stats = pd.DataFrame(stats_by_inst)
    csv_path = os.path.join(base_dir, 'descriptive_stats_by_instance.csv')
    df_stats.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Descriptive stats by instance -> {csv_path}")
    
    return df_stats


def plot_boxplot_by_instance_binarization(df, metric='fitness', verbose=False):
    """
    Genera 6 boxplots (instancia × binarización) para una métrica específica.
    """
    if df is None or len(df) == 0:
        if verbose:
            print("[WARN] No data for boxplots")
        return
    
    # Seleccionar directorio y columna según métrica
    if metric == 'fitness':
        _, _, fitness_dir, _, _ = ensure_directories()
        plots_dir = fitness_dir
        column = 'fitness'
        y_label = 'Fitness (minimized)'
    elif metric == 'time':
        _, _, _, time_dir, _ = ensure_directories()
        plots_dir = time_dir
        column = 'tiempoEjecucion'
        y_label = 'Execution Time (seconds)'
    elif metric == 'xpl_xpt':
        _, _, _, _, xpl_xpt_dir = ensure_directories()
        plots_dir = xpl_xpt_dir
        column = 'xpl_promedio'
        y_label = 'Exploration Ratio (0-100%)'
        if column not in df.columns:
            if verbose:
                print(f"[SKIP] Column {column} not found for xpl_xpt metric")
            return
    else:
        return
    
    # Instancias y binarizaciones únicas
    instancias = sorted(df['instancia_nombre'].unique())
    binarizaciones = sorted(df['binarizacion'].unique())
    mhs_order = sorted(df['MH'].unique())
    
    for instancia_nombre in instancias:
        for binarizacion in binarizaciones:
            subset = df[(df['instancia_nombre'] == instancia_nombre) & 
                       (df['binarizacion'] == binarizacion)]
            
            if len(subset) == 0:
                continue
            
            fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
            
            sns.boxplot(data=subset, x='MH', y=column, ax=ax, 
                       order=mhs_order, palette='Set2')
            
            ax.set_xlabel('Metaheuristic', fontsize=10)
            ax.set_ylabel(y_label, fontsize=10)
            ax.set_title(f'{metric.upper()} - Instance {instancia_nombre} + {binarizacion}', 
                        fontsize=11, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Sanitizar nombres para filenames (reemplazar caracteres inválidos)
            safe_instancia = str(instancia_nombre).replace('/', '_').replace('\\', '_').replace(':', '_').strip()
            safe_binarizacion = str(binarizacion).replace('/', '_').replace('\\', '_').replace(':', '_').strip()
            if safe_binarizacion.lower() in ['none', 'nan', 'null']:
                safe_binarizacion = 'NoData'
            
            output_filename = f'boxplot_{safe_instancia}_{safe_binarizacion}.png'
            output_path = os.path.join(plots_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            if verbose:
                print(f"[OK] {metric.upper()} Boxplot Instance {instancia_nombre} + {binarizacion} -> {output_filename}")
    
    if verbose:
        print(f"[OK] Generated 6 instance-binarization boxplots ({metric})")


def plot_violinplot_by_instance_binarization(df, metric='fitness', verbose=False):
    """
    Genera 6 violin plots (instancia × binarización) para una métrica específica.
    """
    if df is None or len(df) == 0:
        if verbose:
            print("[WARN] No data for violin plots")
        return
    
    # Seleccionar directorio y columna según métrica
    if metric == 'fitness':
        _, _, fitness_dir, _, _ = ensure_directories()
        plots_dir = fitness_dir
        column = 'fitness'
        y_label = 'Fitness (minimized)'
    elif metric == 'time':
        _, _, _, time_dir, _ = ensure_directories()
        plots_dir = time_dir
        column = 'tiempoEjecucion'
        y_label = 'Execution Time (seconds)'
    elif metric == 'xpl_xpt':
        _, _, _, _, xpl_xpt_dir = ensure_directories()
        plots_dir = xpl_xpt_dir
        column = 'xpl_promedio'
        y_label = 'Exploration Ratio (0-100%)'
        if column not in df.columns:
            if verbose:
                print(f"[SKIP] Column {column} not found for xpl_xpt metric")
            return
    else:
        return
    
    instancias = sorted(df['instancia_nombre'].unique())
    binarizaciones = sorted(df['binarizacion'].unique())
    mhs_order = sorted(df['MH'].unique())
    
    for instancia_nombre in instancias:
        for binarizacion in binarizaciones:
            subset = df[(df['instancia_nombre'] == instancia_nombre) & 
                       (df['binarizacion'] == binarizacion)]
            
            if len(subset) == 0:
                continue
            
            fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
            
            sns.violinplot(data=subset, x='MH', y=column, ax=ax, 
                          order=mhs_order, palette='Set2', legend=False)
            
            ax.set_xlabel('Metaheuristic', fontsize=10)
            ax.set_ylabel(y_label, fontsize=10)
            ax.set_title(f'{metric.upper()} Distribution - Instance {instancia_nombre} + {binarizacion}', 
                        fontsize=11, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Sanitizar nombres para filenames
            safe_instancia = str(instancia_nombre).replace('/', '_').replace('\\', '_').replace(':', '_').strip()
            safe_binarizacion = str(binarizacion).replace('/', '_').replace('\\', '_').replace(':', '_').strip()
            if safe_binarizacion.lower() in ['none', 'nan', 'null']:
                safe_binarizacion = 'NoData'
            
            output_filename = f'violinplot_{safe_instancia}_{safe_binarizacion}.png'
            output_path = os.path.join(plots_dir, output_filename)
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            if verbose:
                print(f"[OK] {metric.upper()} Violin plot Instance {instancia_nombre} + {binarizacion} -> {output_filename}")
    
    if verbose:
        print(f"[OK] Generated 6 instance-binarization violin plots ({metric})")


def plot_xpl_xpt_evolution(verbose=False):
    """
    Genera 30 gráficos de evolución XPL/XPT:
    - 5 MH × 3 instancias × 2 binarizaciones = 30 plots
    - Cada plot muestra XPL y XPT JUNTAS en el mismo gráfico (2 líneas)
    """
    # Leer CSVs de level1
    csv_exp = 'Resultados/resumen/level1_raw/scp_experiments_all_runs.csv'
    csv_iter = 'Resultados/resumen/level1_raw/xpl_xpt_iterations.csv'
    
    if not os.path.exists(csv_iter) or not os.path.exists(csv_exp):
        if verbose:
            print("[WARN] XPL/XPT CSV not found. Run level1 extraction first.")
        return
    
    df_exp = pd.read_csv(csv_exp)
    df_iter = pd.read_csv(csv_iter)
    
    # Merge para tener MH, instancia, binarización por experimento
    df_merged = df_iter.merge(
        df_exp[['id_experimento', 'MH', 'instancia_nombre', 'binarizacion']], 
        on='id_experimento'
    )
    
    # Crear directorio
    _, _, _, _, xpl_xpt_dir = ensure_directories()
    evolution_dir = os.path.join(xpl_xpt_dir, 'evolution')
    os.makedirs(evolution_dir, exist_ok=True)
    
    # Agrupar por MH, instancia, binarización
    groups = df_merged.groupby(['MH', 'instancia_nombre', 'binarizacion'])
    
    plot_count = 0
    for (mh, inst, binariz), group in groups:
        # Calcular promedio por iteración (promediando las 31 ejecuciones)
        avg_by_iter = group.groupby('iter').agg({
            'XPL': 'mean',
            'XPT': 'mean'
        }).reset_index()
        
        # Crear plot CON DOS LÍNEAS (XPL y XPT juntas)
        fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
        
        ax.plot(avg_by_iter['iter'], avg_by_iter['XPL'], 
                label='Exploration (XPL)', color='#2E86AB', linewidth=1.5)
        ax.plot(avg_by_iter['iter'], avg_by_iter['XPT'], 
                label='Exploitation (XPT)', color='#A23B72', linewidth=1.5)
        
        ax.set_xlabel('Iteration', fontsize=10)
        ax.set_ylabel('Percentage (%)', fontsize=10)
        ax.set_title(f'{mh} - Instance {inst} - {binariz}', fontsize=11, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 100])
        
        plt.tight_layout()
        
        # Sanitizar nombre para Windows (quitar ":")
        mh_safe = mh.replace(':', '_')
        filename = f'xpl_xpt_evolution_{mh_safe}_{inst}_{binariz}.png'
        filepath = os.path.join(evolution_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        plot_count += 1
        if verbose:
            print(f"[OK] XPL/XPT Evolution {mh} + Instance {inst} + {binariz} -> {filename}")
    
    if verbose:
        print(f"[OK] Generated {plot_count} XPL/XPT evolution plots")


def plot_evolution_by_variable(variable='w', verbose=False):
    """
    Genera 30 gráficos de evolución por variable individual:
    - 5 MH × 3 instancias × 2 binarizaciones = 30 plots
    - Cada plot muestra UNA ÚNICA variable (w o DIV) con una sola línea
    
    Variables soportadas: 'w', 'DIV'
    """
    # Leer CSVs de level1
    csv_exp = 'Resultados/resumen/level1_raw/scp_experiments_all_runs.csv'
    csv_iter = 'Resultados/resumen/level1_raw/xpl_xpt_iterations.csv'
    
    if not os.path.exists(csv_iter) or not os.path.exists(csv_exp):
        if verbose:
            print(f"[WARN] CSV not found. Run level1 extraction first.")
        return
    
    df_exp = pd.read_csv(csv_exp)
    df_iter = pd.read_csv(csv_iter)
    
    # Validar que la variable existe
    if variable not in df_iter.columns:
        if verbose:
            print(f"[WARN] Variable '{variable}' not found in CSV columns")
        return
    
    # Merge para tener MH, instancia, binarización por experimento
    df_merged = df_iter.merge(
        df_exp[['id_experimento', 'MH', 'instancia_nombre', 'binarizacion']], 
        on='id_experimento'
    )
    
    # Crear directorio
    base_dir, plots_dir, _, _, _ = ensure_directories()
    var_dir = os.path.join(plots_dir, variable.lower())
    evolution_dir = os.path.join(var_dir, 'evolution')
    os.makedirs(evolution_dir, exist_ok=True)
    
    # Definir propiedades por variable
    var_config = {
        'w': {'ylabel': 'Inertia Weight (w)', 'color': '#F18F01', 'ylim': None},
        'DIV': {'ylabel': 'Diversity', 'color': '#06A77D', 'ylim': [0, 1]},
    }
    
    config = var_config.get(variable, {'ylabel': variable, 'color': '#333333', 'ylim': None})
    
    # Agrupar por MH, instancia, binarización
    groups = df_merged.groupby(['MH', 'instancia_nombre', 'binarizacion'])
    
    plot_count = 0
    for (mh, inst, binariz), group in groups:
        # Calcular promedio por iteración (promediando las 31 ejecuciones)
        avg_by_iter = group.groupby('iter').agg({
            variable: 'mean'
        }).reset_index()
        
        # Crear plot CON UNA SOLA LÍNEA
        fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
        
        ax.plot(avg_by_iter['iter'], avg_by_iter[variable], 
                label=f'{variable} (avg)', color=config['color'], linewidth=1.5)
        
        ax.set_xlabel('Iteration', fontsize=10)
        ax.set_ylabel(config['ylabel'], fontsize=10)
        ax.set_title(f'{mh} - Instance {inst} - {binariz}', fontsize=11, fontweight='bold')
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        if config['ylim']:
            ax.set_ylim(config['ylim'])
        
        plt.tight_layout()
        
        # Sanitizar nombre para Windows (quitar ":")
        mh_safe = mh.replace(':', '_')
        filename = f'{variable.lower()}_evolution_{mh_safe}_{inst}_{binariz}.png'
        filepath = os.path.join(evolution_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        plot_count += 1
        if verbose:
            print(f"[OK] {variable} Evolution {mh} + Instance {inst} + {binariz} -> {filename}")
    
    if verbose:
        print(f"[OK] Generated {plot_count} {variable} evolution plots")


def plot_evolution_matrix(variable='w', verbose=False):
    """
    Genera 6 matrices de gráficos (una por instancia×binarización):
    - Cada matriz: 5 subplots (uno por MH)
    - Cada subplot: evolución de la variable a través de iteraciones
    
    Ejemplo: div_evolution_matrix_Instance_41_S4-ELIT.png contiene 5 subplots (PSO, PSO_FCS:A/B/C/D)
    
    Variables soportadas: 'w', 'DIV'
    """
    # Leer CSVs de level1
    csv_iter = 'Resultados/resumen/level1_raw/xpl_xpt_iterations.csv'
    
    if not os.path.exists(csv_iter):
        if verbose:
            print(f"[WARN] CSV not found for matrix plots")
        return
    
    df_iter = pd.read_csv(csv_iter)
    
    # Validar que la variable existe
    if variable not in df_iter.columns:
        if verbose:
            print(f"[WARN] Variable '{variable}' not found in CSV columns")
        return
    
    # Obtener información de experimentos desde la BD directamente
    df_exp = extract_experiments_data(verbose=False)
    
    # Merge para tener MH, instancia, binarización por experimento
    df_merged = df_iter.merge(
        df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
        on='id_experimento'
    )
    
    # Renombrar 'experimento' a 'instancia' para mantener consistencia
    df_merged = df_merged.rename(columns={'experimento': 'instancia'})
    
    # Crear directorio
    base_dir, plots_dir, _, _, _ = ensure_directories()
    var_dir = os.path.join(plots_dir, variable.lower())
    matrix_dir = os.path.join(var_dir, 'matrix')
    os.makedirs(matrix_dir, exist_ok=True)
    
    # Definir propiedades por variable
    var_config = {
        'w': {'ylabel': 'Inertia Weight (w)', 'color': '#F18F01', 'ylim': None},
        'DIV': {'ylabel': 'Diversity', 'color': '#06A77D', 'ylim': [0, 1]},
    }
    
    config = var_config.get(variable, {'ylabel': variable, 'color': '#333333', 'ylim': None})
    
    # Obtener combinaciones únicas de instancia y binarización
    combinations = df_merged[['instancia', 'binarizacion']].drop_duplicates().values
    mhs = sorted(df_merged['MH'].unique())
    
    plot_count = 0
    for inst, binariz in combinations:
        # Crear figura con N subplots (dinámico basado en cantidad de MHs)
        num_mhs = len(mhs)
        fig, axes = plt.subplots(num_mhs, 1, figsize=(10, 3*num_mhs), dpi=300)
        
        # Ensure axes is always iterable
        if num_mhs == 1:
            axes = [axes]
        
        for idx, mh in enumerate(mhs):
            ax = axes[idx]
            
            # Filtrar datos para este MH, instancia y binarización
            subset = df_merged[
                (df_merged['MH'] == mh) & 
                (df_merged['instancia'] == inst) & 
                (df_merged['binarizacion'] == binariz)
            ]
            
            if len(subset) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=10)
                ax.set_title(f'{mh}', fontsize=10, fontweight='bold')
                continue
            
            # Calcular promedio por iteración
            avg_by_iter = subset.groupby('iter').agg({
                variable: 'mean'
            }).reset_index()
            
            # Plotear
            ax.plot(avg_by_iter['iter'], avg_by_iter[variable], 
                   label=f'{variable} (avg)', color=config['color'], linewidth=1.5)
            
            ax.set_xlabel('Iteration', fontsize=9)
            ax.set_ylabel(config['ylabel'], fontsize=9)
            ax.set_title(f'{mh}', fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3)
            if config['ylim']:
                ax.set_ylim(config['ylim'])
            ax.tick_params(labelsize=8)
        
        # Título general
        fig.suptitle(f'{variable.upper()} Evolution - Instance {inst} - {binariz}', 
                    fontsize=12, fontweight='bold', y=0.995)
        
        plt.tight_layout(rect=[0, 0, 1, 0.99])
        
        # Sanitizar nombres para filenames
        safe_inst = str(inst).replace('/', '_').replace('\\', '_').replace(':', '_').strip()
        safe_binariz = str(binariz).replace('/', '_').replace('\\', '_').replace(':', '_').strip()
        if safe_binariz.lower() in ['none', 'nan', 'null']:
            safe_binariz = 'NoData'
        
        # Guardar
        filename = f'{variable.lower()}_evolution_matrix_Instance_{safe_inst}_{safe_binariz}.png'
        filepath = os.path.join(matrix_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        plot_count += 1
        if verbose:
            print(f"[OK] {variable.upper()} Matrix - Instance {inst} - {binariz} -> {filename}")
    
    if verbose:
        print(f"[OK] Generated {plot_count} {variable} evolution matrix plots")


def plot_xpl_xpt_evolution_matrix(verbose=False):
    """
    Genera 6 matrices de gráficos para XPL/XPT (una por instancia×binarización):
    - Cada matriz: 5 subplots (uno por MH)
    - Cada subplot: XPL y XPT juntos (2 líneas)
    """
    # Leer CSV de iteraciones
    csv_iter = 'Resultados/resumen/level1_raw/xpl_xpt_iterations.csv'
    
    if not os.path.exists(csv_iter):
        if verbose:
            print("[WARN] CSV not found for XPL/XPT matrix plots")
        return
    
    df_iter = pd.read_csv(csv_iter)
    
    # Obtener información de experimentos desde la BD directamente
    df_exp = extract_experiments_data(verbose=False)
    
    # Merge
    df_merged = df_iter.merge(
        df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
        on='id_experimento'
    )
    
    # Renombrar 'experimento' a 'instancia' para mantener consistencia
    df_merged = df_merged.rename(columns={'experimento': 'instancia'})
    
    # Crear directorio
    _, _, _, _, xpl_xpt_dir = ensure_directories()
    matrix_dir = os.path.join(xpl_xpt_dir, 'matrix')
    os.makedirs(matrix_dir, exist_ok=True)
    
    # Obtener combinaciones
    combinations = df_merged[['instancia', 'binarizacion']].drop_duplicates().values
    mhs = sorted(df_merged['MH'].unique())
    
    plot_count = 0
    for inst, binariz in combinations:
        # Crear figura con N subplots (dinámico basado en cantidad de MHs)
        num_mhs = len(mhs)
        fig, axes = plt.subplots(num_mhs, 1, figsize=(10, 3*num_mhs), dpi=300)
        
        # Ensure axes is always iterable (si num_mhs=1, no es array)
        if num_mhs == 1:
            axes = [axes]
        
        for idx, mh in enumerate(mhs):
            ax = axes[idx]
            
            # Filtrar datos
            subset = df_merged[
                (df_merged['MH'] == mh) & 
                (df_merged['instancia'] == inst) & 
                (df_merged['binarizacion'] == binariz)
            ]
            
            if len(subset) == 0:
                ax.text(0.5, 0.5, 'No data', ha='center', va='center', 
                       transform=ax.transAxes, fontsize=10)
                ax.set_title(f'{mh}', fontsize=10, fontweight='bold')
                continue
            
            # Calcular promedio por iteración
            avg_by_iter = subset.groupby('iter').agg({
                'XPL': 'mean',
                'XPT': 'mean'
            }).reset_index()
            
            # Plotear ambas líneas
            ax.plot(avg_by_iter['iter'], avg_by_iter['XPL'], 
                   label='Exploration (XPL)', color='#2E86AB', linewidth=1.5)
            ax.plot(avg_by_iter['iter'], avg_by_iter['XPT'], 
                   label='Exploitation (XPT)', color='#A23B72', linewidth=1.5)
            
            ax.set_xlabel('Iteration', fontsize=9)
            ax.set_ylabel('Percentage (%)', fontsize=9)
            ax.set_title(f'{mh}', fontsize=10, fontweight='bold')
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 100])
            ax.tick_params(labelsize=8)
            if idx == 0:  # Legend solo en el primero
                ax.legend(loc='best', fontsize=8)
        
        # Título general
        fig.suptitle(f'XPL/XPT Evolution - Instance {inst} - {binariz}', 
                    fontsize=12, fontweight='bold', y=0.995)
        
        plt.tight_layout(rect=[0, 0, 1, 0.99])
        
        # Sanitizar nombres para filenames
        safe_inst = str(inst).replace('/', '_').replace('\\', '_').replace(':', '_').strip()
        safe_binariz = str(binariz).replace('/', '_').replace('\\', '_').replace(':', '_').strip()
        if safe_binariz.lower() in ['none', 'nan', 'null']:
            safe_binariz = 'NoData'
        
        # Guardar
        filename = f'xpl_xpt_evolution_matrix_Instance_{safe_inst}_{safe_binariz}.png'
        filepath = os.path.join(matrix_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        plot_count += 1
        if verbose:
            print(f"[OK] XPL/XPT Matrix - Instance {inst} - {binariz} -> {filename}")
    
    if verbose:
        print(f"[OK] Generated {plot_count} XPL/XPT evolution matrix plots")


def main(df=None, verbose=False):
    """Ejecutar análisis agregado Level 2."""
    if verbose:
        print("\n[*] LEVEL 2: AGGREGATED ANALYSIS")
        print("=" * 70)
    
    # Cargar datos si no se pasan
    if df is None:
        try:
            from .level1_raw_data import extract_experiments_data
        except ImportError:
            from level1_raw_data import extract_experiments_data
        df = extract_experiments_data(verbose=False)
    
    if df is None or len(df) == 0:
        if verbose:
            print("[ERROR] No data available for Level 2")
        return False
    
    # Generar estadísticas
    generate_descriptive_stats_by_mh(df, verbose=verbose)
    generate_descriptive_stats_by_instance(df, verbose=verbose)
    
    # Generar gráficos para CADA MÉTRICA (fitness, time, xpl_xpt)
    metrics = ['fitness', 'time']
    
    for metric in metrics:
        if verbose:
            print(f"\n[*] Generating plots for metric: {metric.upper()}")
        plot_boxplot_by_instance_binarization(df, metric=metric, verbose=verbose)
        plot_violinplot_by_instance_binarization(df, metric=metric, verbose=verbose)
    
    # Generar gráficos de evolución XPL/XPT (2 líneas juntas)
    if verbose:
        print(f"\n[*] Generating XPL/XPT evolution plots (30 gráficos con 2 líneas cada uno)")
    plot_xpl_xpt_evolution(verbose=verbose)
    
    # Generar gráficos de evolución w (30 gráficos individuales)
    if verbose:
        print(f"\n[*] Generating w evolution plots (30 gráficos)")
    plot_evolution_by_variable('w', verbose=verbose)
    
    # Generar gráficos de evolución DIV (30 gráficos individuales)
    if verbose:
        print(f"\n[*] Generating DIV evolution plots (30 gráficos)")
    plot_evolution_by_variable('DIV', verbose=verbose)
    
    # Generar MATRICES de gráficos (6 matrices por variable)
    if verbose:
        print(f"\n[*] Generating evolution matrix plots (XPL/XPT, w, DIV)")
    plot_xpl_xpt_evolution_matrix(verbose=verbose)
    plot_evolution_matrix('w', verbose=verbose)
    plot_evolution_matrix('DIV', verbose=verbose)
    
    if verbose:
        print("\n" + "=" * 70)
        print("[OK] Level 2 completed\n")
    
    return True


if __name__ == '__main__':
    main(verbose=True)
