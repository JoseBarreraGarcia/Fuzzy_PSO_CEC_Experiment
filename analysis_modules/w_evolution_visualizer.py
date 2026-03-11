"""
W Evolution Visualizer
======================
Crea visualizaciones de la evolución de w a lo largo de iteraciones
para comparar fuzzy sets A, B, C, D.

Genera:
1. Gráficos de evolución por instancia/binarización
2. Comparativa directa de todos los fuzzy sets
3. Tabla resumen de diferencias estadísticas
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Configuración de estilo
plt.style.use('seaborn-v0_8-darkgrid')
COLORS = {
    'PSO_FCS:A': '#1f77b4',  # Blue
    'PSO_FCS:B': '#ff7f0e',  # Orange
    'PSO_FCS:C': '#2ca02c',  # Green
    'PSO_FCS:D': '#d62728',  # Red
}

def load_w_evolution_data():
    """Carga los datos de w_evolution_analysis.csv"""
    csv_path = 'Resultados/resumen/w_evolution_analysis.csv'
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} no encontrado")
        return None
    
    df = pd.read_csv(csv_path)
    # Filtrar filas válidas (iter > 0)
    df = df[df['iter'] > 0].copy()
    return df

def create_evolution_plots(df, output_dir='Resultados/resumen/w_evolution_plots'):
    """Crea gráficos de evolución de w por instancia y binarización"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    instancias = sorted(df['instancia'].unique())
    binarizaciones = sorted(df['binarizacion'].unique())
    
    plot_count = 0
    
    for instancia in instancias:
        for binari in binarizaciones:
            df_subset = df[(df['instancia'] == instancia) & (df['binarizacion'] == binari)]
            
            fig, ax = plt.subplots(figsize=(12, 6))
            
            for mh in sorted(df_subset['MH'].unique()):
                if 'FCS' not in mh:
                    continue
                
                df_mh = df_subset[df_subset['MH'] == mh]
                ax.plot(df_mh['iter'], df_mh['w_mean'], 
                       label=mh, linewidth=2, color=COLORS.get(mh, 'black'))
                
                # Agregar área de variabilidad (std)
                w_mean = df_mh['w_mean'].values
                w_std = df_mh['w_std'].fillna(0).values
                iters = df_mh['iter'].values
                
                ax.fill_between(iters, w_mean - w_std, w_mean + w_std, 
                               alpha=0.2, color=COLORS.get(mh, 'black'))
            
            ax.set_xlabel('Iteración', fontsize=12)
            ax.set_ylabel('Inertia Weight (w)', fontsize=12)
            ax.set_title(f'Evolución de w - Instancia {instancia} ({binari})', fontsize=14, fontweight='bold')
            ax.legend(loc='best', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 0.8])
            
            # Guardar
            filename = f'{output_dir}/w_evolution_inst{instancia}_{binari}.png'
            plt.tight_layout()
            plt.savefig(filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            plot_count += 1
            print(f"  ✓ {filename}")
    
    return plot_count

def create_comparison_plot(df, output_dir='Resultados/resumen/w_evolution_plots'):
    """Crea un gráfico comparativo general de todos los fuzzy sets"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes = axes.flatten()
    
    fcs_mhs = sorted([mh for mh in df['MH'].unique() if 'FCS' in mh])
    
    for idx, mh in enumerate(fcs_mhs):
        ax = axes[idx]
        
        df_mh = df[df['MH'] == mh]
        
        # Agrupar por instancia y binarización
        for instancia in sorted(df_mh['instancia'].unique()):
            df_inst = df_mh[df_mh['instancia'] == instancia]
            
            # Promedio sobre binarizaciones
            df_avg = df_inst.groupby('iter').agg({'w_mean': 'mean'}).reset_index()
            
            ax.plot(df_avg['iter'], df_avg['w_mean'], 
                   label=f'SCP-{instancia}', linewidth=2, marker='o', markersize=3, alpha=0.7)
        
        ax.set_xlabel('Iteración', fontsize=11)
        ax.set_ylabel('w (media)', fontsize=11)
        ax.set_title(f'{mh}', fontsize=12, fontweight='bold', color=COLORS.get(mh, 'black'))
        ax.legend(loc='best', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0.15, 0.75])
    
    fig.suptitle('Comparación de Evolución de w por Fuzzy Set', fontsize=14, fontweight='bold', y=1.00)
    plt.tight_layout()
    
    filename = f'{output_dir}/w_evolution_comparison_all_sets.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ {filename}")

def create_statistical_summary(df, output_dir='Resultados/resumen/w_evolution_plots'):
    """Crea tabla resumen de estadísticas por fase"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Crear tabla resumen
    summary_data = []
    
    for mh in sorted(df['MH'].unique()):
        if 'FCS' not in mh:
            continue
        
        df_mh = df[df['MH'] == mh]
        
        # Por fases
        early = df_mh[df_mh['iter'] <= 100]['w_mean'].dropna()
        mid = df_mh[(df_mh['iter'] > 100) & (df_mh['iter'] <= 300)]['w_mean'].dropna()
        late = df_mh[df_mh['iter'] > 300]['w_mean'].dropna()
        all_iters = df_mh['w_mean'].dropna()
        
        summary_data.append({
            'Fuzzy Set': mh,
            'General (media)': f"{all_iters.mean():.4f}",
            'General (std)': f"{all_iters.std():.4f}",
            'Temprana 1-100 (media)': f"{early.mean():.4f}",
            'Temprana (std)': f"{early.std():.4f}",
            'Media 101-300 (media)': f"{mid.mean():.4f}",
            'Media (std)': f"{mid.std():.4f}",
            'Tardía 301-500 (media)': f"{late.mean():.4f}",
            'Tardía (std)': f"{late.std():.4f}",
        })
    
    df_summary = pd.DataFrame(summary_data)
    
    # Guardar como CSV
    summary_csv = f'{output_dir}/w_evolution_summary_stats.csv'
    df_summary.to_csv(summary_csv, index=False)
    print(f"  ✓ {summary_csv}")
    
    # También mostrar en pantalla
    print("\n" + "=" * 100)
    print("TABLA RESUMEN: ESTADÍSTICAS DE W POR FASE")
    print("=" * 100)
    print(df_summary.to_string(index=False))
    print("=" * 100 + "\n")

def create_phase_comparison_plot(df, output_dir='Resultados/resumen/w_evolution_plots'):
    """Crea gráfico comparativo de w en diferentes fases"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    fcs_mhs = sorted([mh for mh in df['MH'].unique() if 'FCS' in mh])
    
    phases = {
        'Temprana (1-100)': df[df['iter'] <= 100],
        'Media (101-300)': df[(df['iter'] > 100) & (df['iter'] <= 300)],
        'Tardía (301-500)': df[df['iter'] > 300],
    }
    
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    for phase_idx, (phase_name, phase_df) in enumerate(phases.items()):
        ax = axes[phase_idx]
        
        phase_data = []
        labels = []
        
        for mh in fcs_mhs:
            df_mh = phase_df[phase_df['MH'] == mh]
            w_values = df_mh['w_mean'].dropna().values
            phase_data.append(w_values)
            labels.append(mh.replace('PSO_FCS:', ''))
        
        bp = ax.boxplot(phase_data, labels=labels, patch_artist=True)
        
        # Colorear
        for patch, mh in zip(bp['boxes'], fcs_mhs):
            patch.set_facecolor(COLORS.get(mh, 'lightblue'))
            patch.set_alpha(0.7)
        
        ax.set_ylabel('w (inertia weight)', fontsize=11)
        ax.set_title(phase_name, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    
    fig.suptitle('Distribución de w por Fase de Optimización', fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    filename = f'{output_dir}/w_phase_comparison_boxplot.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"  ✓ {filename}")

def main(verbose=True):
    """Ejecuta todas las visualizaciones"""
    
    if verbose:
        print("\n" + "=" * 80)
        print("W EVOLUTION VISUALIZER")
        print("=" * 80)
    
    # Cargar datos
    df = load_w_evolution_data()
    if df is None:
        return False
    
    if verbose:
        print(f"\n[INFO] Datos cargados: {len(df)} filas")
    
    # Crear visualizaciones
    output_dir = 'Resultados/resumen/w_evolution_plots'
    os.makedirs(output_dir, exist_ok=True)
    
    if verbose:
        print("\n[1/4] Creando gráficos de evolución por instancia/binarización...")
    plot_count = create_evolution_plots(df, output_dir)
    
    if verbose:
        print(f"      {plot_count} gráficos creados")
        print("\n[2/4] Creando gráfico comparativo...")
    create_comparison_plot(df, output_dir)
    
    if verbose:
        print("\n[3/4] Creando tabla de estadísticas...")
    create_statistical_summary(df, output_dir)
    
    if verbose:
        print("\n[4/4] Creando gráfico de comparación por fases...")
    create_phase_comparison_plot(df, output_dir)
    
    if verbose:
        print(f"\n[OK] Todas las visualizaciones guardadas en: {output_dir}")
        print("=" * 80 + "\n")
    
    return True

if __name__ == '__main__':
    main(verbose=True)
