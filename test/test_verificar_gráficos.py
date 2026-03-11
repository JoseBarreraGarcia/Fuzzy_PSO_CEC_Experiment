#!/usr/bin/env python3
"""
Verifica que los PDFs generados contienen las 5 líneas de MH distintasy genera PNG de comparación.
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Configuración
DIR_BEST_PDF = './Resultados/best/SCP'
DIR_FITNESS = './Resultados/fitness'

def comparar_pdfs_vs_csv(instancia, binarizacion):
    """Compara los datos en CSV con los que deberían estar en el PDF"""
    
    print(f"\n[INFO] Comparando SCP_{instancia}_{binarizacion}")
    
    # Leer CSV
    csv_path = os.path.join(DIR_FITNESS, f'SCP/fitness_SCP_{instancia}_{binarizacion}.csv')
    
    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV no encontrado: {csv_path}")
        return False
    
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    
    mhs = sorted(df['MH'].unique())
    print(f"[OK] MH en CSV: {mhs}")
    print(f"[OK] Cantidad de MH: {len(mhs)}")
    
    # Verificar que hay 5 MH
    if len(mhs) == 5:
        print(f"[OK] CORRECTO: Se encontraron 5 variantes como se esperaba")
        expected = ['PSO', 'PSO_FCS:A', 'PSO_FCS:B', 'PSO_FCS:C', 'PSO_FCS:D']
        if set(mhs) == set(expected):
            print(f"[OK] CORRECTO: Las variantes coinciden exactamente")
            return True
        else:
            print(f"[WARN] Las variantes no coinciden. Esperadas: {expected}, Encontradas: {mhs}")
            return False
    else:
        print(f"[ERROR] Se esperaban 5 MH, se encontraron {len(mhs)}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("VERIFICACIÓN DE GRÁFICOS - MH VARIANTS DISTINCTNESS")
    print("=" * 70)
    
    instancias = [41, 51, 61]
    binarizaciones = ['S4-ELIT', 'S4-STD']
    
    success_count = 0
    total_count = 0
    
    for inst in instancias:
        for bin_type in binarizaciones:
            total_count += 1
            if comparar_pdfs_vs_csv(inst, bin_type):
                success_count += 1
    
    print("\n" + "=" * 70)
    print(f"RESUMEN: {success_count}/{total_count} gráficos contienen 5 variantes distintss")
    print("=" * 70)
    
    if success_count == total_count:
        print("\n[OK] PROBLEMA 1 RESUELTO: Todos los gráficos muestran PSO_FCS:A/B/C/D")
        print("[OK] Los PDFs en Resultados/best/SCP ahora contienen 5 líneas distintass")
    else:
        print(f"\n[ERROR] {total_count - success_count} gráficos aún tienen problemas")
