"""
LEVEL 1: RAW DATA EXTRACTION (CSV Support)

Extrae datos crudos de la base de datos en CSVs bien estructurados.
Estos CSVs son la fuente para análisis posteriores y para extraer datos manualmente del entorno.

Structure:
  Resultados/resumen/level1_raw/
    - scp_experiments_all_runs.csv       (todas las corridas SCP)
    - scp_best_per_config.csv             (mejor por configuración)
    - mh_configs_summary.csv              (resumen de configuraciones)
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from BD.sqlite import BD


def ensure_directories():
    """Crear directorios necesarios para level 1."""
    base_dir = 'Resultados/resumen/level1_raw'
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def extract_experiments_data(verbose=False):
    """
    Extrae TODOS los experimentos completados con sus resultados en un CSV.
    
    Columnas:
    - id_experimento, MH, binarizacion, paramMH, iteraciones, poblacion, 
      fitness_min, fitness_max, tiempo_ejecucion, estado, instancia_nombre, 
      instancia_optimo
    """
    bd = BD()
    bd.conectar()
    
    query = """
    SELECT 
        exp.id_experimento,
        exp.experimento,
        exp.MH,
        exp.binarizacion,
        exp.paramMH,
        inst.nombre as instancia_nombre,
        inst.optimo as instancia_optimo,
        res.fitness,
        res.tiempoEjecucion,
        exp.estado
    FROM experimentos exp
    JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
    LEFT JOIN resultados res ON exp.id_experimento = res.fk_id_experimento
    WHERE exp.estado = 'terminado' OR exp.estado = 'completado' OR exp.estado = 'completada'
    ORDER BY exp.MH, inst.nombre, exp.id_experimento
    """
    
    bd.getCursor().execute(query)
    columnas = [descripcion[0] for descripcion in bd.getCursor().description]
    datos = bd.getCursor().fetchall()
    bd.desconectar()
    
    if not datos:
        if verbose:
            print("[WARN] No experiments found with 'terminado'/'completado' status")
        return None
    
    df = pd.DataFrame(datos, columns=columnas)
    
    # Parse paramMH (e.g., "iter:100,pop:50,w_set:A")
    df['iteraciones'] = df['paramMH'].str.extract(r'iter:(\d+)', expand=False).astype(int)
    df['poblacion'] = df['paramMH'].str.extract(r'pop:(\d+)', expand=False).astype(int)
    df['w_set'] = df['paramMH'].str.extract(r'w_set:([A-Z])', expand=False).fillna('N/A')
    
    base_dir = ensure_directories()
    csv_path = os.path.join(base_dir, 'scp_experiments_all_runs.csv')
    
    df.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Extracted {len(df)} experiment results -> {csv_path}")
    
    return df


def extract_best_per_config(df=None, verbose=False):
    """
    Para cada configuración única (MH, binarizacion, iteraciones, poblacion),
    guarda el MEJOR resultado (mínimo fitness).
    """
    if df is None:
        df = extract_experiments_data(verbose=False)
    
    if df is None:
        if verbose:
            print("[WARN] No data to extract best per config")
        return None
    
    # Agrupar por configuración y seleccionar el mejor (min fitness)
    best_per_config = df.loc[df.groupby(['MH', 'binarizacion', 'iteraciones', 'poblacion', 'w_set'])['fitness'].idxmin()]
    best_per_config = best_per_config.reset_index(drop=True)
    
    base_dir = ensure_directories()
    csv_path = os.path.join(base_dir, 'scp_best_per_config.csv')
    
    best_per_config.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Extracted {len(best_per_config)} best configs -> {csv_path}")
    
    return best_per_config


def extract_mh_configs_summary(df=None, verbose=False):
    """
    Resumen de todas las configuraciones probadas para cada MH.
    
    Columnas:
    - MH, binarizacion, w_set, iteraciones, poblacion, instancia_nombre, num_runs
    """
    if df is None:
        df = extract_experiments_data(verbose=False)
    
    if df is None:
        if verbose:
            print("[WARN] No data to extract MH configs")
        return None
    
    configs = df.groupby(['MH', 'binarizacion', 'w_set', 'iteraciones', 'poblacion', 'instancia_nombre']).agg({
        'id_experimento': 'count'
    }).rename(columns={'id_experimento': 'num_runs'}).reset_index()
    
    base_dir = ensure_directories()
    csv_path = os.path.join(base_dir, 'mh_configs_summary.csv')
    
    configs.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Extracted {len(configs)} MH configurations -> {csv_path}")
    
    return configs


def extract_per_instance_per_mh(df=None, verbose=False):
    """
    Para cada (instancia, MH, configuración), todos los resultados.
    Útil para análisis detallado por instancia específica.
    
    CSV: scp_per_instance_mh_<instancia>_<mh>.csv
    """
    if df is None:
        df = extract_experiments_data(verbose=False)
    
    if df is None:
        if verbose:
            print("[WARN] No data to extract per instance/MH")
        return
    
    base_dir = ensure_directories()
    
    # Agrupar por instancia
    for instancia in df['instancia_nombre'].unique():
        instancia_data = df[df['instancia_nombre'] == instancia]
        
        # Agrupar por MH dentro de instancia
        for mh in instancia_data['MH'].unique():
            mh_data = instancia_data[instancia_data['MH'] == mh].reset_index(drop=True)
            
            safe_mh = str(mh).replace(':', '-').replace(' ', '_')
            csv_path = os.path.join(base_dir, f'scp_{instancia}_{safe_mh}.csv')
            
            mh_data.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Extracted per-instance/MH CSVs in {base_dir}")


def extract_xpl_xpt_data(verbose=False):
    """
    Extrae datos de XPL/XPT por iteración desde la tabla iteraciones.
    
    Returns:
        DataFrame con: id_experimento, iter, XPL, XPT, w, DIV
    """
    import io
    bd = BD()
    bd.conectar()
    
    query = """
    SELECT fk_id_experimento, archivo
    FROM iteraciones
    """
    
    cursor = bd.getCursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    bd.desconectar()
    
    if not rows:
        if verbose:
            print("[WARN] No iteration data found")
        return None
    
    all_data = []
    
    for exp_id, csv_blob in rows:
        if csv_blob:
            # Decode CSV from BLOB
            csv_content = csv_blob.decode('utf-8')
            df_iter = pd.read_csv(io.StringIO(csv_content))
            
            # Select relevant columns (condicional: 'w' existe en SCP, no en BEN)
            if 'XPL' in df_iter.columns and 'XPT' in df_iter.columns:
                cols_to_select = ['iter', 'XPL', 'XPT', 'DIV']
                if 'w' in df_iter.columns:
                    cols_to_select.insert(3, 'w')  # Insertar 'w' entre XPT y DIV
                
                df_iter = df_iter[cols_to_select].copy()
                df_iter['id_experimento'] = exp_id
                all_data.append(df_iter)
    
    if not all_data:
        if verbose:
            print("[WARN] No XPL/XPT data found in iterations")
        return None
    
    df_combined = pd.concat(all_data, ignore_index=True)
    
    # Llenar valores de w faltantes (NaN) usando la fórmula lineal de PSO normal
    # w = wMax - iter * ((wMax - wMin) / maxIter), donde wMax=0.9, wMin=0.1
    wMax = 0.9
    wMin = 0.1
    maxIter = 500  # Asumiendo que todos los experimentos usan 500 iteraciones
    
    # Obtener información de experimentos para identificar PSO
    df_exp_info = extract_experiments_data(verbose=False)[['id_experimento', 'MH']]
    df_combined = df_combined.merge(df_exp_info, on='id_experimento', how='left')
    
    # Para PSO con w=NaN, calcular w lineal
    mask_pso_na = (df_combined['MH'] == 'PSO') & (df_combined['w'].isna())
    df_combined.loc[mask_pso_na, 'w'] = 0.9 - df_combined.loc[mask_pso_na, 'iter'] * ((0.9 - 0.1) / maxIter)
    
    # Eliminar columna MH (ya no la necesitamos para el CSV)
    df_combined = df_combined.drop(columns=['MH'])
    
    if verbose:
        print(f"[OK] Extracted XPL/XPT data: {len(df_combined)} iteration records from {len(rows)} experiments")
        w_non_na = df_combined['w'].notna().sum()
        print(f"[INFO] w values (non-NaN): {w_non_na} / {len(df_combined)} ({100*w_non_na/len(df_combined):.1f}%)")
    
    # Guardar en CSV
    base_dir = ensure_directories()
    csv_path = os.path.join(base_dir, 'xpl_xpt_iterations.csv')
    df_combined.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] Saved XPL/XPT data -> {csv_path}")
    
    return df_combined


def main(verbose=False):
    """Ejecutar todas las extracciones de Level 1."""
    if verbose:
        print("\n[*] LEVEL 1: RAW DATA EXTRACTION")
        print("=" * 70)
    
    df = extract_experiments_data(verbose=verbose)
    if df is None:
        if verbose:
            print("[ERROR] No data available")
        return False
    
    extract_best_per_config(df, verbose=verbose)
    extract_mh_configs_summary(df, verbose=verbose)
    extract_per_instance_per_mh(df, verbose=verbose)
    extract_xpl_xpt_data(verbose=verbose)
    
    if verbose:
        print("=" * 70)
        print("[OK] Level 1 completed\n")
    
    return True


if __name__ == '__main__':
    main(verbose=True)
