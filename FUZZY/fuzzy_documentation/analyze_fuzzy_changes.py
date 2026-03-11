"""
Análisis: Comparación de Resultados PSO vs PSO_FCS (Después de Cambios en Fuzzy)

Compara:
1. Resultados previos (Set A original)
2. Resultados actuales (Set A ajustado + reglas modificadas)
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Datos ANTERIORES (antes de cambios)
DATOS_ANTERIORES = {
    "F1": {
        "PSO": {"mean": 0.0014, "std": 0.0012},
        "PSO_FCS:A": {"mean": 15785.59, "std": 1042.83},
        "PSO_FCS:B": {"mean": 15881.53, "std": 646.77},
        "PSO_FCS:C": {"mean": 7831.04, "std": 0},
        "PSO_FCS:D": {"mean": 8445.10, "std": 0}
    },
    "F8": {
        "PSO": {"mean": -6242.50, "std": 1493.64},
        "PSO_FCS:A": {"mean": -3380.17, "std": 308.49},
        "PSO_FCS:B": {"mean": -3033.38, "std": 241.92},
        "PSO_FCS:C": {"mean": -3165.96, "std": 30.78},
        "PSO_FCS:D": {"mean": -2804.82, "std": 95.99}
    },
    "F9": {
        "PSO": {"mean": 40.80, "std": 14.07},
        "PSO_FCS:A": {"mean": 230.77, "std": 12.94},
        "PSO_FCS:B": {"mean": 221.44, "std": 0.97},
        "PSO_FCS:C": {"mean": 214.02, "std": 2.17},
        "PSO_FCS:D": {"mean": 227.24, "std": 9.44}
    },
    "F16": {
        "PSO": {"mean": -1.0316, "std": 0.0},
        "PSO_FCS:A": {"mean": -1.0306, "std": 0.0006},
        "PSO_FCS:B": {"mean": -1.0291, "std": 0.0002},
        "PSO_FCS:C": {"mean": -1.0311, "std": 0.0002},
        "PSO_FCS:D": {"mean": -1.0306, "std": 0.0012}
    }
}

def extract_csv_data():
    """Intenta extraer datos del CSV de resultados actuales"""
    csv_path = Path("Resultados/resumen/level1_raw_cec/ben_experiments_all_runs.csv")
    
    if not csv_path.exists():
        print(f"⚠️  CSV no encontrado: {csv_path}")
        return None
    
    try:
        df = pd.read_csv(csv_path)
        print(f"✓ CSV cargado: {csv_path}")
        print(f"  Registros: {len(df)}")
        print(f"  Columnas: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"✗ Error al leer CSV: {e}")
        return None

def calculate_statistics(df):
    """Calcula estadísticas por MH y función"""
    if df is None:
        return None
    
    stats = {}
    
    for funcion in df['function'].unique():
        stats[funcion] = {}
        df_func = df[df['function'] == funcion]
        
        for mh in df_func['MH'].unique():
            df_mh = df_func[df_func['MH'] == mh]
            fitness_values = df_mh['fitness']
            
            stats[funcion][mh] = {
                "mean": fitness_values.mean(),
                "std": fitness_values.std(),
                "min": fitness_values.min(),
                "max": fitness_values.max(),
                "count": len(df_mh)
            }
    
    return stats

def compare_results(stats_actuales):
    """Compara resultados anteriores vs actuales"""
    
    print("\n" + "="*100)
    print("COMPARACIÓN: RESULTADOS ANTERIORES vs ACTUALES")
    print("="*100)
    
    funciones = ["F1", "F8", "F9", "F16"]
    
    for funcion in funciones:
        print(f"\n{'─'*100}")
        print(f"FUNCIÓN: {funcion}")
        print(f"{'─'*100}")
        
        anterior_pso = DATOS_ANTERIORES[funcion]["PSO"]["mean"]
        anterior_fcs_a = DATOS_ANTERIORES[funcion]["PSO_FCS:A"]["mean"]
        
        print(f"\n{'Algoritmo':<20} {'Anterior':<15} {'Actual':<15} {'Cambio':<12} {'% Mejora':<12}")
        print(f"{'-'*74}")
        
        # PSO
        actual_pso = stats_actuales[funcion]["PSO"]["mean"] if stats_actuales and funcion in stats_actuales else "N/A"
        if actual_pso != "N/A":
            cambio_pso = actual_pso - anterior_pso
            mejora_pso = (cambio_pso / anterior_pso * 100) if anterior_pso != 0 else 0
            print(f"{'PSO':<20} {anterior_pso:<15.6f} {actual_pso:<15.6f} {cambio_pso:<12.6f} {mejora_pso:<12.2f}%")
        else:
            print(f"{'PSO':<20} {anterior_pso:<15.6f} {'N/A':<15} {'N/A':<12} {'N/A':<12}")
        
        # PSO_FCS:A
        actual_fcs_a = stats_actuales[funcion]["PSO_FCS:A"]["mean"] if stats_actuales and funcion in stats_actuales and "PSO_FCS:A" in stats_actuales[funcion] else "N/A"
        if actual_fcs_a != "N/A":
            cambio_fcs = actual_fcs_a - anterior_fcs_a
            mejora_fcs = (cambio_fcs / anterior_fcs_a * 100) if anterior_fcs_a != 0 else 0
            print(f"{'PSO_FCS:A':<20} {anterior_fcs_a:<15.6f} {actual_fcs_a:<15.6f} {cambio_fcs:<12.6f} {mejora_fcs:<12.2f}%")
        else:
            print(f"{'PSO_FCS:A':<20} {anterior_fcs_a:<15.6f} {'N/A':<15} {'N/A':<12} {'N/A':<12}")
        
        # Ratio
        if actual_pso != "N/A" and actual_fcs_a != "N/A":
            ratio_anterior = anterior_pso / anterior_fcs_a if anterior_fcs_a != 0 else 0
            ratio_actual = actual_pso / actual_fcs_a if actual_fcs_a != 0 else 0
            print(f"\n{'Ratio PSO/FCS:A':<20} {ratio_anterior:<15.2f}x {ratio_actual:<15.2f}x")

def analyze_fuzzy_changes():
    """Analiza qué cambios se hicieron en fuzzy_controller_w.py"""
    
    print("\n" + "="*100)
    print("CAMBIOS REALIZADOS EN FUZZY_CONTROLLER_W.PY")
    print("="*100)
    
    cambios = {
        "Set A - W_SETS": {
            "Anterior": {
                "high": "(0.55, 0.9, 0.9)",
                "medium": "(0.35, 0.5, 0.65)",
                "low": "(0.1, 0.1, 0.45)"
            },
            "Actual": {
                "high": "(0.65, 0.85, 0.95)",
                "medium": "(0.45, 0.65, 0.80)",
                "low": "(0.10, 0.25, 0.50)"
            }
        },
        "Reglas": {
            "Anterior": {
                '("low", "early")': "medium",
                '("medium", "mid")': "medium"
            },
            "Actual": {
                '("low", "early")': "high",
                '("medium", "mid")': "high"
            }
        }
    }
    
    print("\n📊 SET A - MEMBRESÍAS (W_SETS)")
    print(f"{'Término':<10} {'Anterior':<20} {'Actual':<25} {'Cambio':<30}")
    print(f"{'-'*85}")
    for termino in ["high", "medium", "low"]:
        ant = cambios["Set A - W_SETS"]["Anterior"][termino]
        act = cambios["Set A - W_SETS"]["Actual"][termino]
        print(f"{termino:<10} {ant:<20} {act:<25}")
    
    print("\n🎯 REGLAS MAMDANI")
    print(f"{'Regla':<25} {'Anterior':<15} {'Actual':<15}")
    print(f"{'-'*55}")
    for regla, ant in cambios["Reglas"]["Anterior"].items():
        act = cambios["Reglas"]["Actual"][regla]
        print(f"{regla:<25} {ant:<15} {act:<15}")
    
    print("\n💡 IMPACTO ESPERADO:")
    print("""
    Set A Anterior: w_medium = 0.5 (bajo)
    Set A Actual:   w_medium = 0.65 (más alto)
    
    Regla Anterior: ("low", "early") → "medium" = 0.5
    Regla Actual:   ("low", "early") → "high" = 0.85
    
    Predicción: PSO_FCS:A debería mejorar significativamente,
                especialmente en iteraciones tempranas
    """)

def main():
    print("\n🔍 ANÁLISIS DE RESULTADOS EXPERIMENTALES")
    print("="*100)
    
    # Analizar cambios en fuzzy
    analyze_fuzzy_changes()
    
    # Extraer datos actuales
    df = extract_csv_data()
    stats_actuales = calculate_statistics(df) if df is not None else None
    
    # Comparar
    compare_results(stats_actuales)
    
    # Análisis interpretativo
    print("\n" + "="*100)
    print("ANÁLISIS INTERPRETATIVO")
    print("="*100)
    
    if stats_actuales is None:
        print("""
⚠️  No se encontraron datos actuales. 

Posibles razones:
1. Los experimentos aún no se han ejecutado
2. El CSV está en una ubicación diferente
3. Los cambios se hicieron pero no se corrió `python reiniciarDB.py && python poblarDB.py && python main.py`

PRÓXIMO PASO: Ejecutar pipeline completo
        """)
    else:
        print("""
✓ Datos encontrados. Comparación lista.

Interpretación:
- Si PSO_FCS:A mejoró > 20%: Los cambios fueron efectivos
- Si PSO_FCS:A mejoró < 20%: Los cambios son insuficientes
- Si PSO_FCS:A empeoró: Cambios van en dirección opuesta
        """)

if __name__ == "__main__":
    main()
