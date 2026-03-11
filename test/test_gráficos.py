#!/usr/bin/env python3
"""
Script de prueba para verificar los gráficos generados
"""

import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuración
DIR_FITNESS = './Resultados/fitness'
DIR_BEST = './Resultados/best'

def verificar_grafico(instancia, binarizacion):
    """Visualiza el gráfico de mejores resultados"""
    
    # Ruta al archivo CSV de fitness
    ruta_csv = os.path.join(DIR_FITNESS, f'SCP/fitness_SCP_{instancia}_{binarizacion}.csv')
    
    print(f"\n[INFO] Verificando gráfico para SCP_{instancia}_{binarizacion}")
    print(f"[INFO] Ruta CSV: {ruta_csv}")
    
    # Leer el archivo CSV
    if not os.path.exists(ruta_csv):
        print(f"[ERROR] Archivo no encontrado: {ruta_csv}")
        return
    
    try:
        df = pd.read_csv(ruta_csv)
        df.columns = df.columns.str.strip()
        
        print(f"[OK] Archivo leído. Shape: {df.shape}")
        print(f"[OK] Columnas: {df.columns.tolist()}")
        print(f"[OK] Variantes de MH únicas:")
        for mh in df['MH'].unique():
            count = len(df[df['MH'] == mh])
            print(f"      - {mh}: {count} registros")
        
        # Crear gráfico de prueba
        fig, ax = plt.subplots(figsize=(12, 6))
        
        colores = ['#FF0000', '#0000FF', '#00AA00', '#FF8800', '#AA00AA']
        for idx, mh in enumerate(sorted(df['MH'].unique())):
            fitness_values = df[df['MH'] == mh]['FITNESS'].values.tolist()
            color = colores[idx % len(colores)]
            ax.plot(range(len(fitness_values)), fitness_values, label=mh, marker='o', color=color, linewidth=2)
        
        ax.set_title(f'Test: Best Fitness per MH\nscp{instancia} - {binarizacion}', fontsize=12)
        ax.set_ylabel("Fitness", fontsize=11)
        ax.set_xlabel("Run Number", fontsize=11)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Guardar como PNG para visualización
        output_file = os.path.join(DIR_BEST, f'SCP/test_fitness_SCP_{instancia}_{binarizacion}.png')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        plt.savefig(output_file, dpi=100)
        print(f"[OK] Gráfico de prueba guardado: {output_file}")
        plt.close()
        
    except Exception as e:
        print(f"[ERROR] Fallo al procesar: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("VERIFICACIÓN DE GRÁFICOS")
    print("=" * 60)
    
    # Verificar todos los gráficos
    instancias = [41, 51, 61]
    binarizaciones = ['S4-ELIT', 'S4-STD']
    
    for inst in instancias:
        for bin_type in binarizaciones:
            verificar_grafico(inst, bin_type)
    
    print("\n[OK] Verificación completada. Ver los archivos .png para inspeccionar los gráficos.")
