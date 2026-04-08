"""
LEVEL 1: RAW DATA EXTRACTION FOR CEC2017 BENCHMARKS

Extrae datos crudos de la base de datos en CSVs bien estructurados.
Estos CSVs son la fuente para análisis posteriores (Level 2).

Structure:
  Resultados/resumen/level1_raw_cec/
    - ben_experiments_all_runs.csv        (todas las corridas BEN)
    - ben_best_per_config.csv             (mejor resultado por configuración MH)
    - ben_convergence_data.csv            (datos de convergencia por iteración)
    - ben_diversity_metrics.csv           (métricas de diversidad por iteración)
    - ben_mh_comparison.csv               (comparación de MH por función)
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from io import StringIO

sys.path.insert(0, str(Path(__file__).parent.parent))

from BD.sqlite import BD

# Óptimos globales conocidos (desde graficosBenchmark.py)
OPTIMOS_CEC2017 = {
    'F1': 0.0,           # Sphere
    'F2': 0.0,           # Schwefel 2.22
    'F3': 0.0,           # Schwefel 1.2
    'F4': 0.0,           # Schwefel 2.21
    'F5': 0.0,           # Rosenbrock
    'F6': 0.0,           # Step
    'F7': 0.0,           # Quartic
    'F8': -418.9829 * 2, # Schwefel (2D)
    'F9': 0.0,           # Rastrigin
    'F10': 0.0,          # Ackley
    'F11': 0.0,          # Griewank
    'F12': 0.0,          # Penalized 1
    'F13': 0.0,          # Penalized 2
    'F14': 1.0,          # Shekel's Foxholes
    'F15': 0.0003075,    # Kowalik
    'F16': -1.0316,      # Six-Hump Camel
    'F17': 0.398,        # Branin
    'F18': 3.0,          # Goldstein-Price
    'F19': -3.86,        # Hartman 3
    'F20': -3.32,        # Hartman 6
    'F21': -10.153199679058229,  # Shekel 5
    'F22': -10.402940566818662,  # Shekel 7
    'F23': -10.536409816692046   # Shekel 10
}


def ensure_directories():
    """Crear directorios necesarios."""
    base_dir = 'Resultados/resumen/level1_raw_cec'
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def extract_experiments_data(output_dir):
    """Extrae TODOS los experimentos completados BEN con sus resultados."""
    
    bd = BD()
    bd.conectar()
    
    query = """
    SELECT 
        exp.id_experimento,
        exp.MH,
        inst.nombre as funcion,
        res.fitness,
        res.tiempoEjecucion,
        exp.estado
    FROM experimentos exp
    JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
    LEFT JOIN resultados res ON exp.id_experimento = res.fk_id_experimento
    WHERE inst.tipo_problema = 'BEN'
    AND (exp.estado = 'terminado' OR exp.estado = 'completado' OR exp.estado = 'completada')
    ORDER BY inst.nombre, exp.MH
    """
    
    bd.getCursor().execute(query)
    columnas = [d[0] for d in bd.getCursor().description]
    datos = bd.getCursor().fetchall()
    bd.desconectar()
    
    if not datos:
        print("[WARN] No hay experimentos BEN completados")
        return
    
    df = pd.DataFrame(datos, columns=columnas)
    
    # Agregar gap al óptimo
    def calcular_gap(row):
        optimo = OPTIMOS_CEC2017.get(row['funcion'], None)
        if optimo is None or pd.isna(row['fitness']):
            return np.nan
        # Si óptimo es 0, usar diferencia absoluta como métrica
        if abs(optimo) < 1e-10:
            return abs(row['fitness'] - optimo)
        # Si óptimo no es 0, usar porcentaje relativo
        return ((row['fitness'] - optimo) / abs(optimo)) * 100
    
    df['gap_optimo_pct'] = df.apply(calcular_gap, axis=1)
    
    # Guardar
    csv_path = os.path.join(output_dir, 'ben_experiments_all_runs.csv')
    df.to_csv(csv_path, index=False)
    print(f"[OK] ben_experiments_all_runs.csv guardado ({len(df)} registros)")
    
    return df


def extract_best_per_config(output_dir, df):
    """Extrae el mejor resultado por configuración (MH x Función)."""
    
    df_best = df.loc[df.groupby(['funcion', 'MH'])['fitness'].idxmin()]
    
    # Agregar estadísticas por config
    stats = df.groupby(['funcion', 'MH']).agg({
        'fitness': ['min', 'max', 'mean', 'std', 'count'],
        'tiempoEjecucion': 'mean',
        'gap_optimo_pct': 'mean'
    }).round(4)
    
    stats.columns = ['fitness_min', 'fitness_max', 'fitness_mean', 'fitness_std', 
                      'n_runs', 'tiempo_medio', 'gap_medio_pct']
    stats = stats.reset_index()
    
    csv_path = os.path.join(output_dir, 'ben_best_per_config.csv')
    stats.to_csv(csv_path, index=False)
    print(f"[OK] ben_best_per_config.csv guardado ({len(stats)} configuraciones)")
    
    return stats


def extract_convergence_data(output_dir):
    """Extrae datos de convergencia: fitness vs iteración para cada experimento."""
    
    bd = BD()
    bd.conectar()
    
    # Obtener todos los archivos de iteraciones
    cursor = bd.getCursor()
    cursor.execute('''
        SELECT fk_id_experimento, archivo FROM iteraciones
    ''')
    
    convergence_records = []
    
    for exp_id, archivo_blob in cursor.fetchall():
        if archivo_blob is None:
            continue
        
        try:
            if isinstance(archivo_blob, bytes):
                contenido = archivo_blob.decode('utf-8', errors='ignore')
            else:
                contenido = str(archivo_blob)
            
            df_iter = pd.read_csv(StringIO(contenido))
            
            # Obtener info del experimento
            cursor2 = bd.getCursor()
            cursor2.execute('''
                SELECT exp.MH, inst.nombre 
                FROM experimentos exp
                JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
                WHERE exp.id_experimento = ?
            ''', (exp_id,))
            
            result = cursor2.fetchone()
            if result:
                mh, funcion = result
                
                # Si el CSV tiene columna 'iter', agregar MH y función
                if 'fitness' in df_iter.columns:
                    df_iter['id_experimento'] = exp_id
                    df_iter['MH'] = mh
                    df_iter['funcion'] = funcion
                    convergence_records.append(df_iter)
        
        except Exception as e:
            pass
    
    bd.desconectar()
    
    if convergence_records:
        df_convergence = pd.concat(convergence_records, ignore_index=True)
        
        csv_path = os.path.join(output_dir, 'ben_convergence_data.csv')
        df_convergence.to_csv(csv_path, index=False)
        print(f"[OK] ben_convergence_data.csv guardado ({len(df_convergence)} registros)")
        
        return df_convergence
    
    return None


def extract_diversity_metrics(output_dir):
    """Extrae métricas de diversidad por iteración."""
    
    bd = BD()
    bd.conectar()
    
    cursor = bd.getCursor()
    cursor.execute('''
        SELECT fk_id_experimento, archivo FROM iteraciones
    ''')
    
    diversity_records = []
    
    for exp_id, archivo_blob in cursor.fetchall():
        if archivo_blob is None:
            continue
        
        try:
            if isinstance(archivo_blob, bytes):
                contenido = archivo_blob.decode('utf-8', errors='ignore')
            else:
                contenido = str(archivo_blob)
            
            df_iter = pd.read_csv(StringIO(contenido))
            
            # Obtener info del experimento
            cursor2 = bd.getCursor()
            cursor2.execute('''
                SELECT exp.MH, inst.nombre 
                FROM experimentos exp
                JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
                WHERE exp.id_experimento = ?
            ''', (exp_id,))
            
            result = cursor2.fetchone()
            if result:
                mh, funcion = result
                
                # Normalize column names: BLOB uses best_fitness/DIV
                col_remap = {}
                for c in df_iter.columns:
                    cl = c.strip().lower()
                    if cl == 'best_fitness':
                        col_remap[c] = 'fitness'
                    elif cl == 'div':
                        col_remap[c] = 'diversity'
                df_iter = df_iter.rename(columns=col_remap)
                
                # Extraer w, diversidad, XPL, XPT si existen
                if 'diversity' in df_iter.columns:
                    keep_cols = []
                    if 'fitness' in df_iter.columns:
                        keep_cols.append('fitness')
                    keep_cols.append('diversity')
                    df_div = df_iter[keep_cols].copy()
                    
                    # Agregar w si existe
                    if 'w' in df_iter.columns:
                        df_div['w'] = df_iter['w']
                    
                    # Agregar XPL/XPT si existen
                    if 'XPL' in df_iter.columns:
                        df_div['XPL'] = df_iter['XPL']
                    if 'XPT' in df_iter.columns:
                        df_div['XPT'] = df_iter['XPT']
                    
                    df_div['id_experimento'] = exp_id
                    df_div['MH'] = mh
                    df_div['funcion'] = funcion
                    df_div['iter'] = range(len(df_div))
                    
                    diversity_records.append(df_div)
        
        except Exception as e:
            pass
    
    bd.desconectar()
    
    if diversity_records:
        df_diversity = pd.concat(diversity_records, ignore_index=True)
        
        csv_path = os.path.join(output_dir, 'ben_diversity_metrics.csv')
        df_diversity.to_csv(csv_path, index=False)
        print(f"[OK] ben_diversity_metrics.csv guardado ({len(df_diversity)} registros)")
        
        return df_diversity
    
    return None


def extract_mh_comparison(output_dir, df_experiments):
    """Comparación de MH por función."""
    
    comparison = df_experiments.groupby(['funcion', 'MH']).agg({
        'fitness': ['min', 'mean', 'std'],
        'tiempoEjecucion': 'mean',
        'gap_optimo_pct': 'mean'
    }).round(4)
    
    comparison.columns = ['fitness_min', 'fitness_mean', 'fitness_std', 
                         'tiempo_medio', 'gap_pct_medio']
    comparison = comparison.reset_index()
    comparison = comparison.sort_values(['funcion', 'fitness_mean'])
    
    csv_path = os.path.join(output_dir, 'ben_mh_comparison.csv')
    comparison.to_csv(csv_path, index=False)
    print(f"[OK] ben_mh_comparison.csv guardado ({len(comparison)} comparaciones)")
    
    return comparison


def main():
    """Ejecutar extracción de datos Nivel 1."""
    
    print("\n" + "=" * 80)
    print("LEVEL 1: RAW DATA EXTRACTION FOR CEC2017 BENCHMARKS")
    print("=" * 80 + "\n")
    
    output_dir = ensure_directories()
    print(f"[INFO] Directorio de salida: {output_dir}\n")
    
    # Paso 1: Extraer experimentos
    df_experiments = extract_experiments_data(output_dir)
    if df_experiments is None:
        print("\n[ERROR] No se pudieron extraer experimentos")
        return
    
    # Paso 2: Mejor por configuración
    extract_best_per_config(output_dir, df_experiments)
    
    # Paso 3: Convergencia
    extract_convergence_data(output_dir)
    
    # Paso 4: Diversidad
    extract_diversity_metrics(output_dir)
    
    # Paso 5: Comparación MH
    extract_mh_comparison(output_dir, df_experiments)
    
    print("\n" + "=" * 80)
    print("[OK] LEVEL 1 EXTRACTION COMPLETADO")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
