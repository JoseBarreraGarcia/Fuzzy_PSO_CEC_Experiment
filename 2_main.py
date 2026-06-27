import time
import shutil
import multiprocessing
import os

from Solver.solverBEN import solverBEN
from Solver.solverSCP import solverSCP

from BD.sqlite import BD

from Util.log import log_experimento, log_error, log_final, log_fecha_hora
from Util.util import parse_parametros, verificar_y_crear_carpetas

def ejecutar_ben(id, experimento, parametrosInstancia, parametros):
    """Ejecuta el problema tipo BEN."""
    dim = int(experimento.split(" ")[1])
    lb = float(parametrosInstancia.split(",")[0].split(":")[1])
    ub = float(parametrosInstancia.split(",")[1].split(":")[1])
    
    solverBEN(
        id, parametros["mh_base"], int(parametros["iter"]),
        int(parametros["pop"]), parametros["instancia"], lb, ub, dim, extra_params=parametros
    )

def ejecutar_problema_scp_uscp(id, instancia, ds, parametros, solver_func, unicost):
    """Ejecuta problemas de tipo SCP o USCP."""
    repair = parametros["repair"]
    
    parMH = parametros["cros"]
    
    solver_func(
        id, parametros["mh_base"], int(parametros["iter"]),
        int(parametros["pop"]), instancia, ds, repair, parMH, unicost, extra_params=parametros
    )

def procesar_experimento(data, bd):
    """Procesa cada experimento según su tipo y maneja errores."""
    id = int(data[0][0])
    id_instancia = int(data[0][10])
    datosInstancia = bd.obtenerInstancia(id_instancia)

    parametros = parse_parametros(data[0][4])
    
    parametros.update({
        "mh": data[0][2],
        "instancia": datosInstancia[0][2],})
    
    problema = datosInstancia[0][1]
    # Extraer nombre base de MH (sin sufijo como :A, :B, etc.)
    # Ejemplo: 'PSO_FCS:A' → 'PSO_FCS'
    mh_nombre_completo = parametros["mh"]
    mh_base = mh_nombre_completo.split(':')[0] if ':' in mh_nombre_completo else mh_nombre_completo
    parametros["mh_base"] = mh_base
    
    problema = datosInstancia[0][1]
    
    # Validación de iteraciones
    if int(parametros["iter"]) < 4:
        log_error(id, "El número de iteraciones (iter) debe ser al menos 4. Marcado como error.")
        bd.actualizarExperimento(id, "error")
        
        return

    #try:
    bd.actualizarExperimento(id, "ejecutando")

    if problema == "BEN":
        ejecutar_ben(id, data[0][1], datosInstancia[0][4], parametros)

    elif problema == "SCP":
        ejecutar_problema_scp_uscp(id, f"scp{datosInstancia[0][2]}", data[0][3], parametros, solverSCP, unicost=False)

    elif problema == "USCP":
        ejecutar_problema_scp_uscp(id, f"uscp{datosInstancia[0][2][1:]}", data[0][3], parametros, solverSCP, unicost=True)

    '''except ValueError as ve:
        log_error(id, f"Error de valor: {str(ve)}")
        bd.actualizarExperimento(id, "error")'''

    '''except Exception as e:
        log_error(id, f"Error general: {str(e)}")
        bd.actualizarExperimento(id, "error")'''

def worker_loop(worker_id, use_seed, base_seed):
    """Worker que consume experimentos de la cola (BD) hasta que no queden pendientes."""
    import numpy as np
    import random

    # Establecer ID de worker para prefijo en consola
    os.environ['PSO_WORKER_ID'] = str(worker_id)

    bd = BD()
    experiments_done = 0

    while True:
        data = bd.obtenerExperimento()
        if data is None:
            break

        exp_id = int(data[0][0])

        # Seed determinista basada en ID del experimento (reproducible independientemente del orden de ejecución)
        if use_seed:
            exp_seed = base_seed + exp_id
            np.random.seed(exp_seed)
            random.seed(exp_seed)

        log_experimento(data)
        procesar_experimento(data, bd)
        experiments_done += 1

    print(f"[W{worker_id}] Finalizado. Experimentos ejecutados: {experiments_done}")


def main():
    """Función principal que gestiona la ejecución de los experimentos."""
    import json
    import numpy as np
    import random
    config_path = obtener_ruta_config('PSO_EXPERIMENTS_CONFIG', './config/experiments.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    use_seed = config.get('use_seed', True)
    base_seed = config.get('seed', 42)
    parallel_workers = config.get('parallel_workers', 1)
    console_summary_only = config.get('console_summary_only', False)

    # Configurar modo de consola como variable de entorno (accesible por subprocesos)
    if console_summary_only:
        os.environ['PSO_CONSOLE_SUMMARY'] = '1'
    else:
        os.environ.pop('PSO_CONSOLE_SUMMARY', None)

    verificar_y_crear_carpetas()

    start_time = time.time()
    log_fecha_hora("Inicio de la ejecución")

    if parallel_workers <= 1:
        # Modo secuencial (comportamiento original, sin prefijo [W])
        os.environ.pop('PSO_WORKER_ID', None)
        worker_loop(0, use_seed, base_seed)
    else:
        # Modo paralelo con multiprocessing
        num_cpus = os.cpu_count() or 1
        n_workers = min(parallel_workers, num_cpus)
        print(f"[Parallel] Iniciando {n_workers} workers (CPUs disponibles: {num_cpus})")

        processes = []
        for i in range(n_workers):
            p = multiprocessing.Process(target=worker_loop, args=(i, use_seed, base_seed))
            p.start()
            processes.append(p)

        for p in processes:
            p.join()

    end_time = time.time()
    total_time = end_time - start_time

    log_fecha_hora("Fin de la ejecución")
    log_final(total_time)

    shutil.rmtree("Resultados\\transitorio", ignore_errors=True)
    
if __name__ == "__main__":
    main()