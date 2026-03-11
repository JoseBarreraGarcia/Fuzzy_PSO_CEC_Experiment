"""
W Evolution Analysis: Comparar comportamiento de w entre fuzzy sets (PSO_FCS:A/B/C/D)

Genera CSV con evolución de w promediado por iteración para cada fuzzy set y combinación
de instancia+binarización.

Output: Resultados/resumen/w_evolution_analysis.csv
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis_modules.level1_raw_data import extract_experiments_data

def analyze_w_evolution(verbose=False):
    """
    Analiza la evolución de w a través de iteraciones para cada fuzzy set.
    Genera un CSV con estadísticas agregadas.
    """
    # Leer datos
    df_iter = pd.read_csv('Resultados/resumen/level1_raw/xpl_xpt_iterations.csv')
    df_exp = extract_experiments_data(verbose=False)
    
    df_merged = df_iter.merge(
        df_exp[['id_experimento', 'MH', 'experimento', 'binarizacion']], 
        on='id_experimento'
    )
    
    # Filtrar solo PSO_FCS
    fcs_mhs = ['PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']
    df_fcs = df_merged[df_merged['MH'].isin(fcs_mhs)]
    
    # Agrupar por instancia, binarización, MH e iteración
    grouped = df_fcs.groupby(['experimento', 'binarizacion', 'MH', 'iter']).agg({
        'w': ['mean', 'std', 'min', 'max', 'count']
    }).reset_index()
    
    # Flatten column names
    grouped.columns = ['instancia', 'binarizacion', 'MH', 'iter', 'w_mean', 'w_std', 'w_min', 'w_max', 'w_count']
    
    # Crear directorio de salida
    output_dir = 'Resultados/resumen'
    os.makedirs(output_dir, exist_ok=True)
    
    # Guardar CSV
    csv_path = os.path.join(output_dir, 'w_evolution_analysis.csv')
    grouped.to_csv(csv_path, index=False)
    
    if verbose:
        print(f"[OK] W evolution analysis saved: {csv_path}")
        print(f"[INFO] Total rows: {len(grouped)}")
        print(f"[INFO] Instancias: {sorted(grouped['instancia'].unique())}")
        print(f"[INFO] Binarizaciones: {sorted(grouped['binarizacion'].unique())}")
        print(f"[INFO] Fuzzy sets: {sorted(grouped['MH'].unique())}")
    
    return grouped

if __name__ == '__main__':
    df = analyze_w_evolution(verbose=True)
    print(f"\nPrimeras filas del CSV:")
    print(df.head(20))
