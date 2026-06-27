import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sys
from pathlib import Path
from io import StringIO

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from Util.util import cargar_configuracion_exp, obtener_ruta_config, writeTofile
from BD.sqlite import BD
from Util.log import escribir_resumenes

# === Carga de Configuraciones ===
CONFIG_FILE = './config/directories.json'
EXPERIMENTS_FILE = obtener_ruta_config('PSO_EXPERIMENTS_CONFIG', './config/experiments.json')

CONFIG, EXPERIMENTS = cargar_configuracion_exp(CONFIG_FILE, EXPERIMENTS_FILE)

# === Definición de directorios ===
DIRS = CONFIG["dirs"]

DIR_RESUMEN      = DIRS["resumen"]
DIR_RESULTADO    = DIRS["base"]
DIR_TRANSITORIO  = DIRS["transitorio"]

# Crear directorios específicos para SCP (bajo resumen/)
DIR_SCP          = os.path.join(DIR_RESUMEN, "SCP")
DIR_SCP_FITNESS  = os.path.join(DIR_SCP, "fitness")
DIR_SCP_GRAFICOS = os.path.join(DIR_SCP, "graficos")
DIR_SCP_BEST     = os.path.join(DIR_SCP, "best")
DIR_SCP_BOXPLOT  = os.path.join(DIR_SCP, "boxplot")
DIR_SCP_VIOLIN   = os.path.join(DIR_SCP, "violinplot")

# === Parámetros generales ===
GRAFICOS = False
MHS_LIST = EXPERIMENTS["mhs"]
COLORS = ['r', 'g']

# === Clase de almacenamiento de resultados ===
class InstancesMhs:
    def __init__(self):
        self.div = []
        self.fitness = []
        self.time = []
        self.xpl = []
        self.xpt = []
        self.bestFitness = []
        self.bestTime = []

# === Inicialización ===

def extraer_xpl_xpt_de_iteraciones(exp_id, iteraciones_cache):
    """
    Extrae los valores promedio de XPL y XPT del archivo de iteraciones
    asociado a un experimento (desde cache en memoria).
    
    Parámetros:
        exp_id: ID del experimento
        iteraciones_cache: Diccionario con archivos de iteraciones precargados
    
    Retorna:
        (xpl_promedio, xpt_promedio) o (50.0, 50.0) si no hay datos
    """
    try:
        if exp_id not in iteraciones_cache or iteraciones_cache[exp_id] is None:
            return 50.0, 50.0
        
        contenido = iteraciones_cache[exp_id]
        
        # Parsear CSV desde el contenido
        try:
            df_iter = pd.read_csv(StringIO(contenido))
        except:
            return 50.0, 50.0
        
        # Buscar columnas XPL y XPT (pueden estar con variaciones de nombre)
        xpl_col = None
        xpt_col = None
        
        for col in df_iter.columns:
            col_lower = col.strip().lower()
            if 'xpl' in col_lower:
                xpl_col = col
            elif 'xpt' in col_lower:
                xpt_col = col
        
        if xpl_col is not None and xpt_col is not None:
            try:
                xpl_promedio = float(df_iter[xpl_col].mean())
                xpt_promedio = float(df_iter[xpt_col].mean())
                return xpl_promedio, xpt_promedio
            except:
                return 50.0, 50.0
        else:
            return 50.0, 50.0
    
    except Exception as e:
        return 50.0, 50.0

bd = BD()

# === Función para actualizar Datos (UPDATED) ===
def actualizar_datos(mhs_instances, mh, archivo_fitness, fitness_value, time_value, xpl_value, xpt_value):
    """Updated version that works with database-sourced data"""
    instancia = mhs_instances[mh]
    instancia.fitness.append(fitness_value)
    instancia.time.append(time_value)
    instancia.xpl.append(xpl_value)
    instancia.xpt.append(xpt_value)
    archivo_fitness.write(f'{mh}, {fitness_value}\n')

def graficar_datos(iteraciones, fitness, xpl, xpt, tiempo, mh, problem, corrida, binarizacion):
    """
    Genera gráficos de convergencia, porcentajes XPL/XPT y tiempo por iteración.
    Guarda los resultados en archivos PDF dentro del directorio configurado.
    """
    # Directorio base para los gráficos de esta corrida
    output_dir = os.path.join(DIR_SCP_GRAFICOS, str(binarizacion))
    os.makedirs(output_dir, exist_ok=True)

    # --- Gráfico de convergencia ---
    path_convergencia = os.path.join(output_dir, f'Convergence_{mh}_SCP_{problem}_{corrida}_{binarizacion}.pdf')
    _, ax = plt.subplots()
    ax.plot(iteraciones, fitness, marker='o')
    ax.set_title(f'Convergence {mh}\nscp{problem} - Run {corrida} - ({binarizacion})')
    ax.set_ylabel("Fitness")
    ax.set_xlabel("Iteration")
    plt.tight_layout()
    plt.savefig(path_convergencia, dpi=300, bbox_inches='tight')
    plt.close()

    # --- Gráfico XPL vs XPT ---
    path_porcentaje = os.path.join(output_dir, f'Percentage_{mh}_SCP_{problem}_{corrida}_{binarizacion}.pdf')
    _, axPER = plt.subplots()
    axPER.plot(iteraciones, xpl, color="r", label=rf"$\overline{{XPL}}$: {np.round(np.mean(xpl), 2)}%")
    axPER.plot(iteraciones, xpt, color="b", label=rf"$\overline{{XPT}}$: {np.round(np.mean(xpt), 2)}%")
    axPER.set_title(f'XPL% - XPT% {mh}\nscp{problem} - Run {corrida} - ({binarizacion})')
    axPER.set_ylabel("Percentage")
    axPER.set_xlabel("Iteration")
    axPER.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(path_porcentaje, dpi=300, bbox_inches='tight')
    plt.close()

    # --- Gráfico de tiempo por iteración ---
    path_tiempo = os.path.join(output_dir, f'Time_{mh}_SCP_{problem}_{corrida}_{binarizacion}.pdf')
    _, axTime = plt.subplots()
    axTime.plot(iteraciones, tiempo, color='g', label='Time per Iteration')
    axTime.set_title(f'Time per Iteration {mh}\nscp{problem} - Run {corrida} - ({binarizacion})')
    axTime.set_ylabel("Time (s)")
    axTime.set_xlabel("Iteration")
    axTime.legend(loc='upper right')
    plt.tight_layout()
    plt.savefig(path_tiempo, dpi=300, bbox_inches='tight')
    plt.close()

def graficar_boxplot_violin(instancia, binarizacion):
    """
    Genera gráficos Boxplot y Violinplot para los valores de fitness
    según cada metaheurística aplicada en una instancia del SCP.

    Parámetros:
        instancia (str): Nombre o número de la instancia del problema.
        binarizacion (str/int): Tipo de técnica de binarización usada.
    """

    # Ruta al archivo de datos
    direccion_datos = os.path.join(DIR_SCP_FITNESS, f'fitness_SCP_{instancia}_{binarizacion}.csv')

    # Cargar y validar los datos
    try:
        datos = pd.read_csv(direccion_datos)
        
        # Si el archivo está vacío, saltarlo
        if datos.empty or len(datos) < 2:
            print(f"        [INFO] Archivo {direccion_datos} vacío o insuficiente para gráficos. Saltando.")
            return
        
        datos.columns = datos.columns.str.strip()  # Limpia espacios
        if 'FITNESS' not in datos.columns or 'MH' not in datos.columns:
            print(f"        [ERROR] Columnas necesarias no encontradas en {direccion_datos}")
            return
    except FileNotFoundError:
        print(f"        [INFO] Archivo no encontrado: {direccion_datos} (será creado en siguientes ejecuciones)")
        return
    except pd.errors.EmptyDataError:
        print(f"        [INFO] Archivo vacío: {direccion_datos}")
        return
    except Exception as e:
        print(f"        [ERROR] Error al leer {direccion_datos}: {e}")
        return

    # --- Boxplot ---
    output_dir_box = DIR_SCP_BOXPLOT
    os.makedirs(output_dir_box, exist_ok=True)
    file_path_box = os.path.join(output_dir_box, f'boxplot_fitness_SCP_{instancia}_{binarizacion}.pdf')

    try:
        sns.boxplot(x='MH', y='FITNESS', data=datos, hue='MH', palette='Set2', legend=False)
        plt.title(f'Boxplot Fitness\nscp{instancia} - {binarizacion}')
        plt.xlabel('Metaheuristic')
        plt.ylabel('Fitness')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(file_path_box, dpi=300, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"        [ERROR] Fallo al generar boxplot: {e}")

    # --- Violinplot ---
    output_dir_violin = DIR_SCP_VIOLIN
    os.makedirs(output_dir_violin, exist_ok=True)
    file_path_violin = os.path.join(output_dir_violin, f'violinplot_fitness_SCP_{instancia}_{binarizacion}.pdf')

    try:
        sns.violinplot(x='MH', y='FITNESS', data=datos, hue='MH', palette='Set3', legend=False)
        plt.title(f'Violinplot Fitness\nscp{instancia} - {binarizacion}')
        plt.xlabel('Metaheuristic')
        plt.ylabel('Fitness')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(file_path_violin, dpi=300, bbox_inches='tight')
        plt.close()
    except Exception as e:
        print(f"        [ERROR] Fallo al generar violinplot: {e}")

def procesar_archivos_legacy(instancia, blob, archivo_fitness, bin_actual, mhs_instances):
    """
    [LEGACY] Procesa una lista de archivos (blob), extrae sus datos y genera gráficos asociados
    a una instancia específica del SCP, utilizando una binarización concreta.
    
    Esta función se mantiene por compatibilidad pero ya no se usa en analizar_instancias().
    Procesa archivos CSV del transitorio en lugar de la base de datos.

    Parámetros:
        instancia (str): Identificador del problema SCP a analizar.
        blob (list): Lista de tuplas (nombre_archivo, contenido, binarizacion).
        archivo_fitness (file): Archivo abierto para escribir resultados de fitness.
        bin_actual (str): Tipo de binarización a procesar en esta ejecución.
    """
    corrida = 1  # Contador de ejecuciones

    for nombre_archivo, contenido, binarizacion in blob:
        # Validar nombre del archivo
        try:
            mh, _ = nombre_archivo.split('_')[:2]
        except ValueError:
            print(f"[ADVERTENCIA] Archivo '{nombre_archivo}' con nombre inválido. Se omite.")
            continue

        # Filtrar archivos según la binarización actual
        if binarizacion.strip() != bin_actual:
            continue

        # Guardar contenido temporal para su análisis
        direccion_destino = os.path.join(DIR_TRANSITORIO, f'{nombre_archivo}.csv')
        writeTofile(contenido, direccion_destino)

        # Intentar leer el archivo temporal
        try:
            data = pd.read_csv(direccion_destino)
        except Exception as e:
            print(f"[ERROR] Fallo al leer '{direccion_destino}': {e}")
            os.remove(direccion_destino)
            continue

        # Solo procesar si la metaheurística está registrada
        if mh in MHS_LIST:
            actualizar_datos(mhs_instances, mh, archivo_fitness, data)
            mhs_instances[mh].bestFitness = data['fitness']
            mhs_instances[mh].bestTime = data['time']

        # Generar gráficos por corrida
        if GRAFICOS:
            graficar_datos(
                iteraciones=data['iter'],
                fitness=data['fitness'],
                xpl=data['XPL'],
                xpt=data['XPT'],
                tiempo=data['time'],
                mh=mh,
                problem=instancia,
                corrida=corrida,
                binarizacion=binarizacion
            )

        # Limpiar archivo temporal
        os.remove(direccion_destino)

        corrida += 1  # Siguiente corrida

    archivo_fitness.close()

def graficar_mejores_resultados(instancia, mhs_instances, binarizacion):
    """
    Genera gráficos de comparación para los mejores valores de fitness y tiempo
    alcanzados por cada metaheurística en una instancia del SCP.

    Parámetros:
        instancia (str): Nombre o identificador de la instancia SCP.
        mhs_instances (dict): Diccionario con las instancias de cada MH (incluyendo w_sets).
        binarizacion (str): Nombre del esquema de binarización utilizado.
    """
    
    # Verificar que hay datos
    has_data = any(len(mhs_instances[mh].bestFitness) > 0 for mh in mhs_instances.keys())
    if not has_data:
        print(f"        [INFO] Sin datos de fitness para graficar en {instancia}-{binarizacion}")
        return
    
    mejor_fitness = float('inf')
    mejor_tiempo = float('inf')
    mh_mejor_fitness = "N/A"
    mh_mejor_tiempo = "N/A"

    # Buscar la mejor metaheurística en fitness y tiempo (usando todas las claves dinámicamente)
    for name in mhs_instances.keys():
        mh = mhs_instances[name]
        if len(mh.bestFitness) == 0 or len(mh.bestTime) == 0:
            continue
            
        min_fitness = min(mh.bestFitness)
        min_tiempo = min(mh.bestTime)

        if min_fitness < mejor_fitness:
            mejor_fitness = min_fitness
            mh_mejor_fitness = name

        if min_tiempo < mejor_tiempo:
            mejor_tiempo = min_tiempo
            mh_mejor_tiempo = name

    # Crear carpeta de salida si no existe
    output_dir = DIR_SCP_BEST
    os.makedirs(output_dir, exist_ok=True)

    # Paleta de colores para diferentes variantes
    colores = ['#FF0000', '#0000FF', '#00AA00', '#FF8800', '#AA00AA', '#00AAAA', '#FFAA00', '#AA0000']
    
    # --- Gráfico de mejores fitness ---
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        for idx, name in enumerate(sorted(mhs_instances.keys())):  # Ordenar para consistencia
            mh = mhs_instances[name]
            if len(mh.bestFitness) > 0:
                color = colores[idx % len(colores)]
                ax.plot(range(len(mh.bestFitness)), mh.bestFitness, label=name, marker='o', color=color, linewidth=2)
        
        ax.set_title(f'Best Fitness per MH\nscp{instancia} - {binarizacion}\nBest: {mh_mejor_fitness} ({mejor_fitness})', fontsize=12)
        ax.set_ylabel("Fitness", fontsize=11)
        ax.set_xlabel("Run Number", fontsize=11)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'fitness_SCP_{instancia}_{binarizacion}.pdf'), dpi=300)
        plt.close()
    except Exception as e:
        print(f"        [ERROR] Fallo al generar gráfico de fitness: {e}")

    # --- Gráfico de mejores tiempos ---
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        for idx, name in enumerate(sorted(mhs_instances.keys())):  # Ordenar para consistencia
            mh = mhs_instances[name]
            if len(mh.bestTime) > 0:
                color = colores[idx % len(colores)]
                ax.plot(range(len(mh.bestTime)), mh.bestTime, label=name, marker='s', color=color, linewidth=2)
        
        ax.set_title(f'Best Time per MH\nscp{instancia} - {binarizacion}\nBest: {mh_mejor_tiempo} ({mejor_tiempo:.2f} s)', fontsize=12)
        ax.set_ylabel("Time (s)", fontsize=11)
        ax.set_xlabel("Run Number", fontsize=11)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, f'time_SCP_{instancia}_{binarizacion}.pdf'), dpi=300)
        plt.close()
    except Exception as e:
        print(f"        [ERROR] Fallo al generar gráfico de tiempo: {e}")


def analizar_instancias():
    """
    Función principal para analizar instancias del problema SCP.
    Lee datos desde la base de datos directamente, genera gráficos y resúmenes estadísticos.
    """
    
    bd.conectar()
    
    # Crear carpeta transitorio si no existe
    os.makedirs(DIR_TRANSITORIO, exist_ok=True)
    
    # Obtener lista de instancias y binarizaciones
    lista_instancias = ', '.join([f'"{inst}"' for inst in EXPERIMENTS["instancias"]["SCP"]])
    lista_bin = EXPERIMENTS["DS_actions"]
    
    # Query para obtener todos los experimentos completados
    query = f"""
    SELECT 
        exp.id_experimento,
        exp.MH,
        exp.binarizacion,
        inst.nombre as instancia_nombre,
        inst.optimo as instancia_optimo,
        res.fitness,
        res.tiempoEjecucion,
        exp.estado
    FROM experimentos exp
    JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
    LEFT JOIN resultados res ON exp.id_experimento = res.fk_id_experimento
    WHERE inst.nombre IN ({lista_instancias}) 
    AND (exp.estado = 'terminado' OR exp.estado = 'completado' OR exp.estado = 'completada')
    ORDER BY inst.nombre, exp.binarizacion, exp.MH
    """
    
    bd.getCursor().execute(query)
    columnas = [descripcion[0] for descripcion in bd.getCursor().description]
    todos_datos = bd.getCursor().fetchall()
    
    if not todos_datos:
        print("[ADVERTENCIA] No hay experimentos completados en la base de datos.")
        bd.desconectar()
        return
    
    # Convertir a DataFrame para procesamiento más fácil
    df_todos = pd.DataFrame(todos_datos, columns=columnas)
    
    print("[INFO] Iniciando procesamiento de instancias...\n")
    
    # [IMPORTANTE] Precarga de iteraciones en memoria para evitar problemas de cursor
    print("[INFO] Precargando archivos de iteraciones en memoria...")
    iteraciones_cache = {}
    
    cursor_iter = bd.getCursor()
    cursor_iter.execute('SELECT fk_id_experimento, archivo FROM iteraciones')
    for exp_id, archivo_blob in cursor_iter.fetchall():
        if archivo_blob is not None:
            try:
                if isinstance(archivo_blob, bytes):
                    contenido = archivo_blob.decode('utf-8', errors='ignore')
                else:
                    contenido = str(archivo_blob)
                iteraciones_cache[exp_id] = contenido
            except:
                iteraciones_cache[exp_id] = None
        else:
            iteraciones_cache[exp_id] = None
    
    print(f"[INFO] {len(iteraciones_cache)} archivos de iteraciones precargados.\n")
    
    # Procesar por instancia y binarización
    instancias_unicas = df_todos['instancia_nombre'].unique()
    
    for instancia_nombre in instancias_unicas:
        # Extraer número de instancia (ej: "SCP41" -> "41")
        instancia_id = instancia_nombre.replace('SCP', '')
        
        print(f"[INFO] Procesando instancia: {instancia_nombre}")
        df_inst = df_todos[df_todos['instancia_nombre'] == instancia_nombre]
        
        for binarizacion in lista_bin:
            print(f"    > Binarización: {binarizacion}")
            
            # Filtrar datos para esta combinación
            df_bin = df_inst[df_inst['binarizacion'] == binarizacion]
            
            if df_bin.empty:
                print(f"        [ADVERTENCIA] Sin datos para {instancia_nombre} - {binarizacion}")
                continue
            
            mhs_instances_local = {name: InstancesMhs() for name in MHS_LIST}
            
            # Preparar carpetas de salida
            output_dir_resumen = os.path.join(DIR_RESUMEN, 'SCP')
            output_dir_fitness = DIR_SCP_FITNESS
            os.makedirs(output_dir_resumen, exist_ok=True)
            os.makedirs(output_dir_fitness, exist_ok=True)
            
            # Inicializar archivos de salida
            archivoResumenFitness = open(os.path.join(output_dir_resumen, f'resumen_fitness_SCP_{instancia_id}_{binarizacion}.csv'), 'w')
            archivoResumenTimes = open(os.path.join(output_dir_resumen, f'resumen_times_SCP_{instancia_id}_{binarizacion}.csv'), 'w')
            archivoResumenPercentage = open(os.path.join(output_dir_resumen, f'resumen_percentage_SCP_{instancia_id}_{binarizacion}.csv'), 'w')
            archivoFitness = open(os.path.join(output_dir_fitness, f'fitness_SCP_{instancia_id}_{binarizacion}.csv'), 'w')
            
            # Escribir encabezados
            archivoResumenFitness.write("instance, best, avg. fitness, std fitness\n")
            archivoResumenTimes.write("instance, min time (s), avg. time (s), std time (s)\n")
            archivoResumenPercentage.write("instance, avg. XPL%, avg. XPT%\n")
            archivoFitness.write("MH, FITNESS\n")
            
            # Obtener lista de MH únicos en estos datos (con w_sets incluidos)
            mhs_unicos = df_bin['MH'].unique()
            mhs_instances_local = {mh: InstancesMhs() for mh in mhs_unicos}
            
            # Procesar cada MH completo (incluyendo w_set)
            for mh_completo in mhs_unicos:
                df_mh = df_bin[df_bin['MH'] == mh_completo]
                
                if df_mh.empty:
                    continue
                
                # Recolectar todos los valores para este MH
                fitness_vals = []
                time_vals = []
                
                for _, row in df_mh.iterrows():
                    fitness_val = float(row['fitness']) if row['fitness'] is not None else float('inf')
                    time_val = float(row['tiempoEjecucion']) if row['tiempoEjecucion'] is not None else 0.0
                    exp_id = int(row['id_experimento'])
                    
                    fitness_vals.append(fitness_val)
                    time_vals.append(time_val)
                    
                    # Extraer XPL/XPT del archivo de iteraciones (desde cache)
                    xpl_val, xpt_val = extraer_xpl_xpt_de_iteraciones(exp_id, iteraciones_cache)
                    
                    actualizar_datos(mhs_instances_local, mh_completo, archivoFitness, fitness_val, time_val, xpl_val, xpt_val)
                
                # Asignar listas completas de mejores valores (para visualización en gráficos)
                mhs_instances_local[mh_completo].bestFitness = fitness_vals
                mhs_instances_local[mh_completo].bestTime = time_vals
            
            # Escribir resúmenes estadísticos
            escribir_resumenes(mhs_instances_local, archivoResumenFitness, archivoResumenTimes, archivoResumenPercentage, list(mhs_unicos))
            
            # Generar gráficos resumen (sin boxplot/violin si no hay datos suficientes)
            try:
                graficar_mejores_resultados(instancia_id, mhs_instances_local, binarizacion)
            except Exception as e:
                print(f"        [ADVERTENCIA] Error al generar gráficos de mejores resultados: {e}")
            
            try:
                graficar_boxplot_violin(instancia_id, binarizacion)
            except Exception as e:
                print(f"        [ADVERTENCIA] Error al generar boxplot/violin: {e}")
            
            # Cerrar archivos
            archivoResumenFitness.close()
            archivoResumenTimes.close()
            archivoResumenPercentage.close()
            archivoFitness.close()
        
        print("")  # Separación visual entre instancias
    
    bd.desconectar()
    print("[INFO] Análisis SCP completado con éxito.")
    print("-" * 50)
