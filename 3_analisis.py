from Util.util import cargar_configuracion

import importlib
analisisSCP = importlib.import_module('3_2_analisisSCP')
analisisBEN = importlib.import_module('3_1_analisisBEN')

from analysis_modules_cec import (
    level1_raw_data_cec,
    level2_aggregated_cec,
    convergence_curves_cec,
    w_relationships_cec,
)

import time

CONFIG_PATH = './config/analysis.json'

def main():
    """
    Función principal que ejecuta los análisis de los diferentes métodos de optimización,
    dependiendo de los flags de configuración en el archivo analysis.json.
    También mide y reporta tiempos de ejecución.
    """
    config = cargar_configuracion(CONFIG_PATH)
    tiempos = {}

    tiempo_total_inicio = time.time()

    if config.get("ben", False):
        print("[INFO] Ejecutando análisis BEN...")
        print("-" * 50)
        t0 = time.time()
        analisisBEN.analizar_instancias()
        t1 = time.time()
        tiempos["BEN"] = round(t1 - t0, 2)

        # CEC analysis pipeline: Level 1 (raw extraction) + Level 2 (comparative plots)
        print("[INFO] Ejecutando análisis CEC (Level 1 + Level 2)...")
        print("-" * 50)
        t0 = time.time()
        level1_raw_data_cec.main()
        level2_aggregated_cec.main()
        t1 = time.time()
        tiempos["CEC_Pipeline"] = round(t1 - t0, 2)

        # Convergence curves analysis (adaptive to MH configurations)
        print("[INFO] Ejecutando análisis de curvas de convergencia...")
        print("-" * 50)
        t0 = time.time()
        convergence_curves_cec.main()
        t1 = time.time()
        tiempos["Convergence_Curves"] = round(t1 - t0, 2)

        # W-metric relationship analysis (w vs diversity, progress, fitness)
        print("[INFO] Ejecutando análisis de relaciones w-métricas...")
        print("-" * 50)
        t0 = time.time()
        w_relationships_cec.main()
        t1 = time.time()
        tiempos["W_Relationships"] = round(t1 - t0, 2)

    if config.get("scp", False):
        print("[INFO] Ejecutando análisis SCP...")
        print("-" * 50)
        t0 = time.time()
        analisisSCP.analizar_instancias()
        t1 = time.time()
        tiempos["SCP"] = round(t1 - t0, 2)

    tiempo_total_fin = time.time()
    tiempo_total = round(tiempo_total_fin - tiempo_total_inicio, 2)

    ancho = 50

    print("\n" + "=" * ancho)
    print("RESUMEN DE TIEMPOS DE EJECUCIÓN".center(ancho))
    print("=" * ancho)

    for metodo, duracion in tiempos.items():
        print(f"  > {metodo:<6} : {duracion:>6.2f} segundos")

    print("-" * ancho)
    print(f"    TOTAL    : {tiempo_total:>6.2f} segundos")
    print("=" * ancho)
    
    print("[INFO] Análisis completado.")

if __name__ == '__main__':
    main()
