"""
LEVEL 3: DISAGGREGATED ANALYSIS (Per-Instance & Per-Config Best Results)

Análisis desagregado: mejores resultados específicos para cada:
  1. Instancia (SCP41, SCP51, ...)
  2. Configuración MH (PSO_S4_STD, PSO_S4_STD_FCS:A, ...)

Output:
  Resultados/resumen/level3_disaggregated/
    - best_results_by_instance_mh.csv        (mejor resultado por instancia + MH)
    - top_configs_global.csv                 (mejores configuraciones globales)
    - instance_SCP41_ranking.csv             (ranking de MH para SCP41 específicamente)
    - instance_SCP51_ranking.csv
    - ... (una tabla por instancia)
    
    - config_PSO_S4_STD_ranking.csv           (ranking de instancias para PSO_S4_STD)
    - config_PSO_S4_STD_FCS-A_ranking.csv
    - ... (una tabla por configuración)
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def ensure_directories():
    """Crear directorios para level 3."""
    base_dir = 'Resultados/resumen/level3_disaggregated'
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def sanitize_filename(name):
    """Sanitizar para nombres de archivo."""
    return str(name).replace(':', '-').replace(' ', '_').replace('/', '-')


def generate_best_results_by_instance_mh(df, verbose=False):
    """
    Para cada par (instancia, MH), el MEJOR resultado.
    
    Columnas:
    - instancia, MH, configuración (binarizacion, w_set, etc.), 
      fitness_best, fitness_mean, fitness_std, runs_count
    """
    if df is None or len(df) == 0:
        if verbose:
            print("[WARN] No data for best results")
        return None
    
    base_dir = ensure_directories()
    
    best_results = []
    
    for instancia in df['instancia_nombre'].unique():
        inst_df = df[df['instancia_nombre'] == instancia]
        
        for mh in inst_df['MH'].unique():
            mh_inst_data = inst_df[inst_df['MH'] == mh]
            
            # Encontrar la mejor configuración para esta instancia + MH
            grouped = mh_inst_data.groupby(['binarizacion', 'w_set']).agg({
                'fitness': ['min', 'mean', 'std', 'count'],
                'iteraciones': 'first',
                'poblacion': 'first',
            }).reset_index()
            
            grouped.columns = ['binarizacion', 'w_set', 'fitness_best', 'fitness_mean', 
                              'fitness_std', 'runs_count', 'iteraciones', 'poblacion']
            
            # Ordenar por fitness_best y tomar el mejor
            best = grouped.sort_values('fitness_best').iloc[0]
            
            result = {
                'instance': instancia,
                'optimum': mh_inst_data['instancia_optimo'].iloc[0],
                'MH': mh,
                'binarizacion': best['binarizacion'],
                'w_set': best['w_set'],
                'iteraciones': int(best['iteraciones']),
                'poblacion': int(best['poblacion']),
                'fitness_best': best['fitness_best'],
                'fitness_mean': best['fitness_mean'],
                'fitness_std': best['fitness_std'],
                'runs_count': int(best['runs_count']),
                'fitness_gap': best['fitness_best'] - mh_inst_data['instancia_optimo'].iloc[0],
            }
            best_results.append(result)
    
    df_best = pd.DataFrame(best_results)
    csv_path = os.path.join(base_dir, 'best_results_by_instance_mh.csv')
    df_best.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Best results by instance/MH -> {csv_path}")
        print(f"     ({len(df_best)} rows)")
    
    return df_best


def generate_top_configs_global(df, verbose=False, top_n=20):
    """
    Top N mejores configuraciones globales (sin restricción de instancia).
    Útil para identificar qué combinaciones funcionan mejor en general.
    """
    if df is None or len(df) == 0:
        if verbose:
            print("[WARN] No data for top configs")
        return None
    
    base_dir = ensure_directories()
    
    # Agrupar por configuración y calcular estadísticas
    config_groups = df.groupby(['MH', 'binarizacion', 'w_set']).agg({
        'fitness': ['mean', 'min', 'max', 'std', 'count'],
    }).reset_index()
    
    config_groups.columns = ['MH', 'binarizacion', 'w_set', 'fitness_mean', 'fitness_min', 
                             'fitness_max', 'fitness_std', 'num_runs']
    
    # Ordenar por fitness_mean (mejor primero) y tomar top N
    config_groups = config_groups.sort_values('fitness_mean').head(top_n).reset_index(drop=True)
    config_groups['rank'] = range(1, len(config_groups) + 1)
    
    csv_path = os.path.join(base_dir, 'top_configs_global.csv')
    config_groups.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Top {top_n} global configs -> {csv_path}")
    
    return config_groups


def generate_instance_rankings(df, verbose=False):
    """
    Para CADA instancia específica, crear un ranking de todos los MH.
    
    Output: instance_<SCP41>_ranking.csv
           instance_<SCP51>_ranking.csv
           ... etc
    """
    if df is None or len(df) == 0:
        if verbose:
            print("[WARN] No data for instance rankings")
        return
    
    base_dir = ensure_directories()
    
    for instancia in sorted(df['instancia_nombre'].unique()):
        inst_data = df[df['instancia_nombre'] == instancia]
        
        # Agrupar por MH
        mh_rankings = []
        for mh in inst_data['MH'].unique():
            mh_data = inst_data[inst_data['MH'] == mh]['fitness'].dropna()
            
            if len(mh_data) == 0:
                continue
            
            mh_rankings.append({
                'rank': None,  # Se asignará después
                'MH': mh,
                'optimum': inst_data['instancia_optimo'].iloc[0],
                'num_runs': len(mh_data),
                'best_fitness': mh_data.min(),
                'mean_fitness': mh_data.mean(),
                'median_fitness': mh_data.median(),
                'worst_fitness': mh_data.max(),
                'std_fitness': mh_data.std(),
                'fitness_gap': mh_data.min() - inst_data['instancia_optimo'].iloc[0],
            })
        
        # Ordenar por best_fitness y asignar rank
        mh_rankings = sorted(mh_rankings, key=lambda x: x['best_fitness'])
        for rank, item in enumerate(mh_rankings, 1):
            item['rank'] = rank
        
        df_ranking = pd.DataFrame(mh_rankings)
        
        safe_inst = sanitize_filename(instancia)
        csv_path = os.path.join(base_dir, f'instance_{safe_inst}_ranking.csv')
        df_ranking.to_csv(csv_path, index=False)
        
        if verbose:
            print(f"[OK] Instance {instancia} ranking ({len(mh_rankings)} MH) -> {csv_path}")
    
    return


def generate_config_rankings(df, verbose=False):
    """
    Para CADA configuración específica (MH + binarizacion + w_set),
    crear un ranking de todas las instancias.
    
    Output: config_<PSO_S4_STD>_ranking.csv
           config_<PSO_S4_STD_FCS-A>_ranking.csv
           ... etc
    """
    if df is None or len(df) == 0:
        if verbose:
            print("[WARN] No data for config rankings")
        return
    
    base_dir = ensure_directories()
    
    # Crear configs únicos
    df['config_name'] = df['MH'] + '_' + df['binarizacion'].fillna('NA') + '_' + df['w_set'].fillna('NA')
    
    for config_name in sorted(df['config_name'].unique()):
        config_data = df[df['config_name'] == config_name]
        
        # Agrupar por instancia
        inst_rankings = []
        for instancia in config_data['instancia_nombre'].unique():
            inst_data = config_data[config_data['instancia_nombre'] == instancia]['fitness'].dropna()
            
            if len(inst_data) == 0:
                continue
            
            inst_rankings.append({
                'rank': None,
                'instance': instancia,
                'optimum': config_data[config_data['instancia_nombre'] == instancia]['instancia_optimo'].iloc[0],
                'num_runs': len(inst_data),
                'best_fitness': inst_data.min(),
                'mean_fitness': inst_data.mean(),
                'median_fitness': inst_data.median(),
                'worst_fitness': inst_data.max(),
                'std_fitness': inst_data.std(),
                'fitness_gap': inst_data.min() - config_data[config_data['instancia_nombre'] == instancia]['instancia_optimo'].iloc[0],
            })
        
        # Ordenar por best_fitness
        inst_rankings = sorted(inst_rankings, key=lambda x: x['best_fitness'])
        for rank, item in enumerate(inst_rankings, 1):
            item['rank'] = rank
        
        df_ranking = pd.DataFrame(inst_rankings)
        
        safe_config = sanitize_filename(config_name)
        csv_path = os.path.join(base_dir, f'config_{safe_config}_ranking.csv')
        df_ranking.to_csv(csv_path, index=False)
        
        if verbose:
            print(f"[OK] Config {config_name} ranking ({len(inst_rankings)} instances) -> {csv_path}")
    
    return


def main(df=None, verbose=False):
    """Ejecutar análisis desagregado Level 3."""
    if verbose:
        print("\n[*] LEVEL 3: DISAGGREGATED ANALYSIS")
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
            print("[ERROR] No data available for Level 3")
        return False
    
    # Generar análisis desagregados
    generate_best_results_by_instance_mh(df, verbose=verbose)
    generate_top_configs_global(df, verbose=verbose)
    generate_instance_rankings(df, verbose=verbose)
    generate_config_rankings(df, verbose=verbose)
    
    if verbose:
        print("=" * 70)
        print("[OK] Level 3 completed\n")
    
    return True


if __name__ == '__main__':
    main(verbose=True)
