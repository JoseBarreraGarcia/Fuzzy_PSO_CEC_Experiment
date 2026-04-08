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

from Util.util import cargar_configuracion_exp, writeTofile
from BD.sqlite import BD
from Util.log import escribir_resumenes

# === Carga de Configuraciones ===
CONFIG_FILE = './config/directories.json'
EXPERIMENTS_FILE = './config/experiments.json'

CONFIG, EXPERIMENTS = cargar_configuracion_exp(CONFIG_FILE, EXPERIMENTS_FILE)

# === Definición de directorios ===
DIRS = CONFIG["dirs"]

DIR_FITNESS      = DIRS["fitness"]
DIR_RESUMEN      = DIRS["resumen"]
DIR_RESULTADO    = DIRS["base"]
DIR_TRANSITORIO  = DIRS["transitorio"]
DIR_GRAFICOS     = DIRS["graficos"]
DIR_BEST         = DIRS["best"]
DIR_BOXPLOT      = DIRS["boxplot"]
DIR_VIOLIN       = DIRS["violinplot"]

# Crear directorios específicos para BEN
DIR_BEN          = os.path.join(DIR_RESUMEN, "BEN")
DIR_BEN_BOXPLOT  = os.path.join(DIR_BEN, "boxplot")
DIR_BEN_VIOLIN   = os.path.join(DIR_BEN, "violinplot")

# === Parámetros generales ===
GRAFICOS = True
MHS_LIST = EXPERIMENTS["mhs"]
# Paleta de colores escalable (genera más colores si es necesario)
COLORS = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#95E1D3', '#F38181', 
          '#AA96DA', '#FCBAD3', '#A8D8EA', '#FFB7B2', '#B5EAD7', '#FFCAB0']

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
bd = BD()

def analizar_instancias():
    """
    Función principal para analizar instancias de funciones benchmark (BEN).
    Lee datos desde la base de datos directamente, genera gráficos y resúmenes estadísticos.
    """
    
    bd.conectar()
    
    # Crear carpeta de resultados BEN si no existe
    os.makedirs(DIR_BEN, exist_ok=True)
    os.makedirs(DIR_BEN_BOXPLOT, exist_ok=True)
    os.makedirs(DIR_BEN_VIOLIN, exist_ok=True)
    os.makedirs(DIR_TRANSITORIO, exist_ok=True)
    
    # Obtener lista de funciones BEN y sus configuraciones
    lista_funciones = ', '.join([f'"{func}"' for func in EXPERIMENTS["instancias"]["BEN"]])
    
    # Query para obtener todos los experimentos completados de BEN
    query = f"""
    SELECT 
        exp.id_experimento,
        exp.experimento,
        exp.MH,
        inst.nombre as funcion_nombre,
        inst.optimo as optimo,
        res.fitness,
        res.tiempoEjecucion,
        exp.estado,
        exp.paramMH
    FROM experimentos exp
    JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
    LEFT JOIN resultados res ON exp.id_experimento = res.fk_id_experimento
    WHERE inst.nombre IN ({lista_funciones}) 
    AND (exp.estado = 'terminado' OR exp.estado = 'completado' OR exp.estado = 'completada')
    ORDER BY inst.nombre, exp.MH
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
    
    print("[INFO] Iniciando procesamiento de funciones BEN...\n")
    
    # Precarga de iteraciones en memoria
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
    
    # Procesar cada función BEN
    funciones = df_todos['funcion_nombre'].unique()
    
    for funcion in funciones:
        print(f"[INFO] Procesando función: {funcion}")
        df_funcion = df_todos[df_todos['funcion_nombre'] == funcion]
        
        # Obtener MH únicos dinámicamente desde los datos (incluyendo w_sets)
        mhs_unicos = df_funcion['MH'].unique()
        
        # Diccionario para almacenar datos por MH
        mhs_instances = {mh: InstancesMhs() for mh in mhs_unicos}
        
        # Procesar cada experimento de esta función
        for idx, row in df_funcion.iterrows():
            exp_id = row['id_experimento']
            mh = row['MH']
            fitness = row['fitness']
            tiempo = row['tiempoEjecucion']
            optimo = row['optimo']
            
            if mh in mhs_instances and fitness is not None and tiempo is not None:
                mhs_instances[mh].fitness.append(fitness)
                mhs_instances[mh].time.append(tiempo)
                mhs_instances[mh].bestFitness.append(fitness)
                mhs_instances[mh].bestTime.append(tiempo)
        
        # Generar estadísticas por función
        print(f"  > Generando estadisticas para {funcion}...")
        generar_estadisticas_funcion(funcion, mhs_instances, df_funcion)
        
        # Generar gráficos
        if GRAFICOS:
            print(f"  > Generando graficos para {funcion}...")
            generar_graficos_funcion(funcion, mhs_instances)
        
        print()
    
    # Generar resumen global
    print("[INFO] Generando resumen global...")
    generar_resumen_global(df_todos)
    
    bd.desconectar()
    print("[INFO] Análisis de BEN completado.")

def generar_estadisticas_funcion(funcion, mhs_instances, df_funcion):
    """Genera estadísticas por función BEN."""
    
    stats = []
    
    # Iterar sobre los MH únicos en los datos
    for mh in mhs_instances.keys():
        instance = mhs_instances[mh]
        
        if len(instance.fitness) == 0:
            continue
        
        fitness_arr = np.array(instance.fitness)
        time_arr = np.array(instance.time)
        
        stats.append({
            'Función': funcion,
            'MH': mh,
            'N': len(fitness_arr),
            'Media_Fitness': np.mean(fitness_arr),
            'Std_Fitness': np.std(fitness_arr),
            'Min_Fitness': np.min(fitness_arr),
            'Max_Fitness': np.max(fitness_arr),
            'Media_Tiempo': np.mean(time_arr),
            'Std_Tiempo': np.std(time_arr),
        })
    
    if stats:
        df_stats = pd.DataFrame(stats)
        csv_path = os.path.join(DIR_BEN, f"estadisticas_{funcion}.csv")
        df_stats.to_csv(csv_path, index=False)
        print(f"    * Estadisticas guardadas en {csv_path}")

def generar_graficos_funcion(funcion, mhs_instances):
    """Genera gráficos para una función BEN."""
    
    # Preparar datos para gráficos
    fitness_data = []
    tiempo_data = []
    
    # Iterar sobre los MH únicos en los datos
    for mh in mhs_instances.keys():
        if len(mhs_instances[mh].fitness) > 0:
            fitness_data.append({
                'MH': mh,
                'Fitness': mhs_instances[mh].fitness
            })
            tiempo_data.append({
                'MH': mh,
                'Tiempo': mhs_instances[mh].time
            })
    
    if not fitness_data:
        return
    
    # Gráfico de BoxPlot (Fitness)
    fitness_vals = [data['Fitness'] for data in fitness_data]
    mh_labels = [data['MH'] for data in fitness_data]
    
    # Generar suficientes colores si hay más MH de los predefinidos
    num_mh = len(fitness_vals)
    colores_para_usar = COLORS * ((num_mh // len(COLORS)) + 1)  # Repetir si es necesario
    
    # Detectar si la escala es muy dispar entre MH (e.g. PSO vs PSO_FCS)
    all_flat = [v for lst in fitness_vals for v in lst]
    global_min = min(all_flat)
    global_max = max(all_flat)
    use_log = False
    if global_min > 0 and global_max / global_min > 100:
        use_log = True
    elif global_min <= 0:
        abs_vals = [abs(v) for v in all_flat if v != 0]
        if abs_vals and max(abs_vals) / min(abs_vals) > 100:
            use_log = True
    
    fig_width = max(10, num_mh * 1.2)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    
    bp = ax.boxplot(fitness_vals, labels=mh_labels, patch_artist=True)
    for patch, color in zip(bp['boxes'], colores_para_usar[:num_mh]):
        patch.set_facecolor(color)
    
    ax.set_xlabel('Metaheuristic', fontsize=12)
    ylabel = 'Fitness (symlog scale)' if use_log else 'Fitness'
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(f'Fitness Distribution - Function {funcion}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    if use_log:
        ax.set_yscale('symlog')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    
    boxplot_path = os.path.join(DIR_BEN_BOXPLOT, f"boxplot_{funcion}.png")
    plt.tight_layout()
    plt.savefig(boxplot_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    * BoxPlot guardado en {boxplot_path}")
    
    # Gráfico de Violín (Fitness)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    
    df_violin = pd.DataFrame([
        {'MH': mh_label, 'Fitness': f}
        for mh_label, fitness_list in zip(mh_labels, fitness_vals)
        for f in fitness_list
    ])
    
    sns.violinplot(data=df_violin, x='MH', y='Fitness', palette='Set2', ax=ax)
    ax.set_xlabel('Metaheuristic', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(f'Fitness Distribution (Violin) - Function {funcion}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    if use_log:
        ax.set_yscale('symlog')
    plt.xticks(rotation=45, ha='right', fontsize=9)
    
    violin_path = os.path.join(DIR_BEN_VIOLIN, f"violin_{funcion}.png")
    plt.tight_layout()
    plt.savefig(violin_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"    * Violin guardado en {violin_path}")

def generar_resumen_global(df_todos):
    """Genera resumen global de todos los experimentos BEN."""
    
    if len(df_todos) == 0:
        return
    
    # Resumen por MH
    resumen_mh = df_todos.groupby('MH').agg({
        'fitness': ['mean', 'std', 'min', 'max', 'count'],
        'tiempoEjecucion': ['mean', 'std']
    }).round(4)
    
    csv_path = os.path.join(DIR_BEN, "resumen_global_mh.csv")
    resumen_mh.to_csv(csv_path)
    print(f"[INFO] Resumen global por MH guardado en {csv_path}")
    
    # Resumen por Función
    resumen_func = df_todos.groupby('funcion_nombre').agg({
        'fitness': ['mean', 'std', 'min', 'max'],
        'tiempoEjecucion': 'mean'
    }).round(4)
    
    csv_path = os.path.join(DIR_BEN, "resumen_global_funciones.csv")
    resumen_func.to_csv(csv_path)
    print(f"[INFO] Resumen global por Función guardado en {csv_path}")
    
    # Resumen detallado: todas las corridas individuales (Función × MH × Run)
    df_detalle = df_todos[df_todos['fitness'].notna()][['funcion_nombre', 'MH', 'id_experimento', 'fitness', 'tiempoEjecucion']].copy()
    df_detalle = df_detalle.rename(columns={
        'funcion_nombre': 'Function',
        'id_experimento': 'Experiment_ID',
        'fitness': 'Fitness',
        'tiempoEjecucion': 'Time_s'
    })
    df_detalle['Run'] = df_detalle.groupby(['Function', 'MH']).cumcount() + 1
    df_detalle = df_detalle[['Function', 'MH', 'Run', 'Fitness', 'Time_s', 'Experiment_ID']]
    df_detalle = df_detalle.sort_values(['Function', 'MH', 'Run']).reset_index(drop=True)
    
    csv_path = os.path.join(DIR_BEN, "all_runs_fitness.csv")
    df_detalle.to_csv(csv_path, index=False)
    print(f"[INFO] Detalle de todas las corridas guardado en {csv_path}")
    
    # Resumen descriptivo: Función × MH con estadísticas
    df_resumen_detallado = df_detalle.groupby(['Function', 'MH']).agg(
        N=('Fitness', 'count'),
        Mean=('Fitness', 'mean'),
        Std=('Fitness', 'std'),
        Min=('Fitness', 'min'),
        Q25=('Fitness', lambda x: np.percentile(x, 25)),
        Median=('Fitness', 'median'),
        Q75=('Fitness', lambda x: np.percentile(x, 75)),
        Max=('Fitness', 'max'),
        Mean_Time=('Time_s', 'mean'),
    ).round(6).reset_index()
    
    csv_path = os.path.join(DIR_BEN, "summary_function_mh.csv")
    df_resumen_detallado.to_csv(csv_path, index=False)
    print(f"[INFO] Resumen Función × MH guardado en {csv_path}")

if __name__ == '__main__':
    analizar_instancias()
