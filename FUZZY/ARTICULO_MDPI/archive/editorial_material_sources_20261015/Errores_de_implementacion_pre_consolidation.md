# Registro de errores de implementación y verificaciones previas

Este documento registra defectos confirmados y controles pendientes antes de volver a ejecutar el batch de 63.426 experimentos de Mathematics. Los elementos de la sección 1 son defectos confirmados; los de la sección 2 son requisitos de verificación y no afirman que exista un defecto.

## 1. Defectos confirmados

### ISSUE-001: Asignación de semillas por ID global del experimento

- **Status:** Confirmed
- **Severity:** Major
- **Affected files and functions:** `config/experiments_mdpi_full.json`; `2_main.py::main`; `2_main.py::worker_loop`; `BD/sqlite.py::BD.insertarExperimentos`; `BD/sqlite.py::BD.obtenerExperimento`; `FUZZY/ARTICULO_MDPI/code/00_generate_level1_raw_data.py::enrich_meta`; `FUZZY/ARTICULO_MDPI/code/10_run_h4_wilcoxon_vs_baseline.py`; `FUZZY/ARTICULO_MDPI/code/12_analyze_rule_structure.py`.
- **Observed behavior:** El perfil especifica `use_seed=true`, `seed=42`, `num_experimentos=31` y `parallel_workers=6`. `worker_loop` asigna `exp_id = int(data[0][0])` y calcula `exp_seed = base_seed + exp_id`; `exp_id` es `id_experimento`, la clave primaria global AUTOINCREMENT, no el número de réplica. Por tanto, IDs distintos entre configuraciones reciben semillas distintas aunque el exportador posteriormente les asigne el mismo `run_id`. El exportador deriva `run_id` con `groupby(["mh_raw", "exp_name"]).cumcount() + 1` y crea `seed = 42 * run_id`; ese valor es metadata sintética, no la semilla usada durante la ejecución. El comentario original de que la primera réplica usaría semilla 42 también contradice la fórmula prevista `42 + run_id`: para `run_id=1,...,31`, las semillas previstas son 43–73.
- **Expected behavior:** Para cada instancia, todas las configuraciones deben usar la misma semilla correspondiente a la réplica: `seed = 42 + run_id` (43–73 para 31 réplicas). La ejecución debe conservar el `run_id` y la semilla efectiva asignados a cada registro, sin reconstruir semillas en el exportador.
- **Supporting evidence:** `2_main.py:100,104–106,124–125`; `BD/sqlite.py:61–73,107–122,354–365`; `1_0_poblarDB.py:102–116,142,150`; `00_generate_level1_raw_data.py:142–143`. En la base archivada, para F1×10, PSO tiene IDs 1–31, FCS-3-R1 32–62, FCS-5-R1 280–310 y FCS-9-R8 993–1023: bajo la fórmula histórica, esas configuraciones reciben bloques de semillas distintos. `Resultados/full_run.log` registra los seis workers y los experimentos 1–63.426. La reanálisis independiente archivada en `FUZZY/ARTICULO_MDPI/results/tests/independent_seed_reanalysis_20261014/` conserva los mismos A12 de RQ4, pero cambia conteos: FCS-3-R1 pasa de 13 a 16 victorias Bonferroni; el resultado no valida el emparejamiento histórico.
- **Scientific or methodological impact:** Las comparaciones RQ4 y los ocho contrastes de reglas no están emparejados por semilla común. Sus p-valores Wilcoxon y afirmaciones de significancia requieren reemplazo o justificación independiente; el reanálisis Mann–Whitney produjo conteos distintos. Los resúmenes de runtime emparejados por `run_id` y el bootstrap H3 que agrupa por `run_id` también deben revisarse metodológicamente. Una semilla común tampoco garantiza trayectorias idénticas si los algoritmos consumen números aleatorios de forma distinta.
- **Required correction or verification:** Crear/preservar un identificador explícito de réplica y calcular la semilla efectiva desde él, no desde `id_experimento`. Persistir `run_id` y `seed` efectiva junto con IDs de instancia y configuración. Eliminar toda reconstrucción de semillas como `42 * run_id`. Antes de reutilizar resultados, repetir los análisis afectados con un método compatible con el diseño realmente ejecutado.
- **Acceptance criteria:** En una prueba de preparación (sin ejecutar el batch completo), verificar que las 33 configuraciones de una instancia comparten semilla para cada réplica, que las 31 semillas son exactamente 43–73 bajo la convención `42 + run_id`, que el resultado no cambia con el orden de asignación a seis workers y que cada registro exportado conserva los valores efectivos almacenados. Resolver y documentar explícitamente la convención de índice antes de autorizar la ejecución.
- **Resolution evidence:** Pending until verified.

### ISSUE-002: Pesos incorrectos en F14 (Shekel's Foxholes)

- **Status:** Resolved
- **Severity:** Major
- **Affected files and functions:** `Problem/Benchmark/Problem.py::F14`; `Problem/Benchmark/README_benchmark_functions.md`; `BD/sqlite.py::BD.insertarInstanciasBEN`; `config/experiments_mdpi_full.json` (`dimensiones.BEN.F14`); `FUZZY/ARTICULO_MDPI/manuscript/tables/tab_benchmark_fixed.tex`.
- **Observed behavior:** La implementación anterior usaba `[1,...,24,24]`. `Problem.py::F14` ahora usa `_F14_WEIGHTS = tuple(range(1, 26))`, es decir `[1,...,25]`. Dimensión 2, límites `[-65.536,65.536]` y óptimo de referencia 1 coinciden con la configuración documentada.
- **Expected behavior:** La suma de 25 términos debe usar los pesos `j=1,...,25`, de acuerdo con la definición canónica de Shekel's Foxholes.
- **Supporting evidence:** `Problem/Benchmark/Problem.py::F14`; `tests/test_f14_objective.py`; `FUZZY/ARTICULO_MDPI/code/20_prepare_corrected_f14.py`; `FUZZY/ARTICULO_MDPI/results/f14_corrected_20261014/`. Pasaron 3 pruebas: pesos exactos, evaluación de los 25 centros y valor del mínimo global aproximado `0.9980038378`. El dataset aislado contiene 1.023 corridas completas, 33 configuraciones × 31 réplicas, cero fallos; todos los IDs/semillas históricos son únicos, `actual_seed = 42 + historical_exp_id`, y el hash de `Problem.py` guardado en la procedencia coincide con el corregido. La primera pasada se interrumpió después de persistir 690 resultados; se respaldó la base aislada, se verificó que los seis IDs marcados `ejecutando` no tuvieran resultado/blob, se preservaron sus CSV parciales y se reencolaron solo esos IDs. La reanudación terminó las 333 filas restantes en 20 min 06 s, sin fallos. La comparación con el histórico encontró 4 fitness distintos por más de `1e-6`: ID 53464 / run 20 / FCS-3-R8 / seed 53506: `+2.8778636`; ID 53577 / run 9 / FCS-5-R4 / seed 53619: `+9.5004135`; ID 53954 / run 14 / FCS-7-R8 / seed 53996: `+4.8153639`; ID 54207 / run 19 / FCS-9-R8 / seed 54249: `-4.8153639`. Tres valores subieron y uno bajó; los otros 1.019 coinciden dentro de esa tolerancia. El fitness medio pasa de `4.24010855` a `4.25220853`; las medianas y el mejor valor global permanecen iguales (`2.98210516` y `0.99800384`, respectivamente). La base histórica y `Resultados/full_run.log` conservaron tamaño y fecha.
- **Scientific or methodological impact:** Los valores y trayectorias de las 1.023 ejecuciones de F14 (33 configuraciones × 31 réplicas) corresponden a una variante de la función, no exactamente a la fórmula canónica declarada. Que el mínimo global permanezca igual no garantiza iguales resultados de optimización, especialmente cerca del centro 25. Los análisis que agregan F14 también pueden cambiar.
- **Required correction or verification:** Corrección aplicada en `Problem.py`. El dataset corregido quedó separado en `FUZZY/ARTICULO_MDPI/results/f14_corrected_20261014/`; los análisis y tablas del manuscrito siguen pendientes de decisión/regeneración y no se modificaron en esta tarea.
- **Acceptance criteria:** Cumplidos para corrección, tests y batch F14: pesos `[1,...,25]`; pruebas de centros y mínimo aprobadas; exactamente 1.023 corridas terminadas en 33 configuraciones × 31; sin IDs o seeds ausentes/duplicados; procedencia de instancia/configuración/semilla incluida; dataset comparativo exportado; archivos históricos intactos.
- **Resolution evidence:** `tests/test_f14_objective.py` (3/3 passed); `FUZZY/ARTICULO_MDPI/results/f14_corrected_20261014/validation_report.json`; `final_execution_summary.json`; `corrected_f14_level1.csv`; `historical_vs_corrected_by_config.csv`; `recovery_20261014.json`; hash de la fuente corregida: `c376b83d0075473bfd0f4aa9fc2c3f6a166a59434ee8588026aff4db3dfcd19a`.

## 2. Verificaciones pendientes (no son defectos confirmados)

### ISSUE-003: Concordancia matemática de F1–F23

- **Status:** Under investigation
- **Severity:** Major
- **Affected files and functions:** `Problem/Benchmark/Problem.py::F1`–`F23`; `Problem/Benchmark/README_benchmark_functions.md`; `BD/sqlite.py::BD.insertarInstanciasBEN`; tablas de benchmark del manuscrito.
- **Observed behavior:** Existe una implementación y una ficha para las 23 funciones; no se ha completado aquí una validación independiente exhaustiva de cada fórmula, dominio, dimensión y óptimo.
- **Expected behavior:** Cada función implementada coincide con su definición de referencia y con la dimensión, límites y óptimo documentados.
- **Supporting evidence:** `Problem/Benchmark/README_benchmark_functions.md` contiene la tabla de funciones, dimensiones, dominios y óptimos; F14 es el defecto confirmado separado en ISSUE-002.
- **Scientific or methodological impact:** Una discrepancia en cualquier función puede invalidar sus puntuaciones y alterar resultados agregados por instancia, función o clase.
- **Required correction or verification:** Añadir pruebas deterministas por función, con casos de referencia independientes, esquinas/centros pertinentes, dimensiones permitidas y óptimos conocidos. Registrar por separado cualquier discrepancia que se confirme.
- **Acceptance criteria:** Las 23 funciones pasan pruebas numéricas reproducibles contra referencias canónicas; dimensiones, límites y óptimos concuerdan con la configuración y el artículo.
- **Resolution evidence:** Pending until verified.

### ISSUE-004: Persistencia de réplica, semilla e identificadores

- **Status:** Under investigation
- **Severity:** Major
- **Affected files and functions:** `BD/sqlite.py::BD.construirTablas`; `BD/sqlite.py::BD.insertarExperimentos`; `1_0_poblarDB.py::insertar_experimentos`; exportadores de resultados.
- **Observed behavior:** El esquema actual de `experimentos` almacena una clave global `id_experimento` y una clave foránea de instancia; no define columnas explícitas para `run_id`, semilla efectiva o ID de configuración.
- **Expected behavior:** Cada corrida recuperable identifica explícitamente su réplica, semilla efectiva, instancia y configuración, además del ID global del experimento.
- **Supporting evidence:** `BD/sqlite.py:61–73` define `experimentos`; `insertarExperimentos` inserta una fila por corrida sin campo de réplica o semilla; el exportador calcula `run_id` después de leer los resultados.
- **Scientific or methodological impact:** Sin estos identificadores no se puede auditar la correspondencia de réplicas, recuperar semillas históricas ni garantizar trazabilidad entre configuración, instancia y resultado.
- **Required correction or verification:** Diseñar y probar un esquema/versionado que almacene explícitamente `run_id`, semilla efectiva, ID de instancia e ID de configuración; comprobar integridad referencial y exportación sin reconstrucciones sintéticas.
- **Acceptance criteria:** Una consulta de solo lectura puede recuperar los cuatro identificadores para cada registro y comprobar unicidad, cardinalidad y correspondencia con la configuración fuente.
- **Resolution evidence:** Pending until verified.

### ISSUE-005: Reproducibilidad con seis workers

- **Status:** Under investigation
- **Severity:** Major
- **Affected files and functions:** `2_main.py::worker_loop`; `2_main.py::main`; `BD/sqlite.py::BD.obtenerExperimento`.
- **Observed behavior:** El runner admite seis procesos y reclama filas pendientes por ID ascendente de forma exclusiva; no existe aún un criterio de aceptación documentado que compruebe asignaciones y resultados reproducibles frente al orden de ejecución.
- **Expected behavior:** Cada registro recibe una única réplica y semilla preasignadas; reordenar workers no cambia la asignación. Deben distinguirse reproducibilidad de asignación y reproducibilidad bit a bit del resultado.
- **Supporting evidence:** `2_main.py:84–106,139–152`; `BD/sqlite.py:354–365`; `Resultados/full_run.log` documenta el batch histórico con seis workers, pero no registra semillas efectivas por experimento.
- **Scientific or methodological impact:** Asignación dependiente del worker, colisiones o registros duplicados dificultarían repetir y verificar el batch.
- **Required correction or verification:** Ejecutar pruebas pequeñas y no científicas con seis workers, semillas e IDs explícitos; comparar manifiestos de entrada/salida bajo órdenes de asignación distintos y auditar fallos/reintentos.
- **Acceptance criteria:** Ninguna réplica queda duplicada u omitida; cada ID conserva la semilla prevista con cualquier orden de workers; los resultados son reproducibles dentro de una tolerancia declarada para el mismo entorno.
- **Resolution evidence:** Pending until verified.

### ISSUE-006: Inicialización común bajo semilla compartida

- **Status:** Under investigation
- **Severity:** Major
- **Affected files and functions:** `Solver/population/population_BEN.py::initialize_population`; `Solver/solverBEN.py::solverBEN`; `Metaheuristics/Codes/PSO.py::iterarPSO`; `Metaheuristics/Codes/PSO_FCS.py::iterarPSO_FCS`.
- **Observed behavior:** PSO y PSO_FCS llaman al inicializador que genera posiciones con `np.random.uniform`; no se ha verificado que todas las configuraciones comparadas reciban exactamente la misma población inicial para una réplica común después de corregir el flujo de semillas.
- **Expected behavior:** Si el diseño requiere control por números aleatorios comunes, las configuraciones del mismo bloque instancia-réplica parten de la misma población, independientemente de su configuración y worker.
- **Supporting evidence:** `population_BEN.py:7–23`; el runner actualiza el RNG global antes de procesar cada experimento, pero el uso histórico de `exp_id` asigna semillas distintas a configuraciones del mismo `run_id`.
- **Scientific or methodological impact:** La variación inicial puede confundirse con efectos de configuración y limitar la interpretación de contrastes pareados.
- **Required correction or verification:** Definir si se exige población inicial común; si se exige, crearla una vez por instancia-réplica o usar un flujo RNG explícito y guardarla/reutilizarla sin que el consumo aleatorio posterior la altere.
- **Acceptance criteria:** Prueba que compara los vectores iniciales de todas las configuraciones del bloque confirma igualdad exacta o tolerancia especificada, también con seis workers.
- **Resolution evidence:** Pending until verified.

### ISSUE-007: Conteo de evaluaciones de la función objetivo

- **Status:** Under investigation
- **Severity:** Minor
- **Affected files and functions:** `Solver/solverBEN.py::solverBEN`; `Solver/population/population_BEN.py::evaluate_population`; reporte de NFE en CSV y manuscrito.
- **Observed behavior:** El flujo contabiliza una población inicial de 20 evaluaciones antes de las 1.000 iteraciones de 20 individuos; la cifra de 20.000 representa evaluaciones de actualización, no el total incluyendo inicialización.
- **Expected behavior:** Cada corrida informa con claridad tanto evaluaciones por iteración como el total, sin omitir las evaluaciones iniciales ni contarlas dos veces.
- **Supporting evidence:** `solverBEN.py` crea `nfe_counter`, evalúa la población inicial y registra NFE; la documentación experimental diferencia 20.000 actualizaciones más 20 iniciales.
- **Scientific or methodological impact:** Presupuestos computacionales o comparaciones por evaluación pueden quedar mal descritos si se informa 20.000 como total.
- **Required correction or verification:** Verificar que la métrica NFE coincide con el número real de llamadas a la función en casos pequeños y que el manuscrito distingue el total de las evaluaciones de actualización.
- **Acceptance criteria:** Para población 20 e iteraciones 1.000, total contabilizado 20.020 si cada individuo se evalúa una vez por iteración y una vez en inicialización; el CSV y la prosa identifican ambas cantidades.
- **Resolution evidence:** Pending until verified.

### ISSUE-008: Correspondencia entre PSO/FCS ejecutable y ecuaciones

- **Status:** Under investigation
- **Severity:** Major
- **Affected files and functions:** `Solver/solverBEN.py::solverBEN`; `Solver/population/population_BEN.py`; `Metaheuristics/Codes/PSO.py::iterarPSO`; `Metaheuristics/Codes/PSO_FCS.py::iterarPSO_FCS`; `FUZZY/fuzzy_controller_auto.py`; `FUZZY/ARTICULO_MDPI/manuscript/sections/03_framework.tex`.
- **Observed behavior:** El manuscrito presenta las ecuaciones de diversidad, control difuso y actualización PSO; no se mantiene aún una prueba automatizada de equivalencia completa entre cada ecuación y el camino ejecutado.
- **Expected behavior:** Dominios vectoriales, coeficientes, límites, normalización de diversidad, calendario de progreso, defuzzificación, clipping y momento de evaluación coinciden con las ecuaciones declaradas.
- **Supporting evidence:** La implementación de PSO y PSO_FCS está en los módulos indicados; el controlador usado por el solver se crea mediante la fábrica `get_fuzzy_controller`.
- **Scientific or methodological impact:** Una discrepancia altera el método realmente evaluado y la reproducibilidad de las afirmaciones del artículo.
- **Required correction or verification:** Crear pruebas unitarias de una iteración con entradas controladas para PSO/FCS y comparar paso a paso con las ecuaciones y límites documentados.
- **Acceptance criteria:** Las pruebas verifican velocidades, posiciones, clipping, valor de `w`, diversidad y número de evaluaciones dentro de tolerancias numéricas declaradas; el camino del solver usa el controlador descrito en el artículo.
- **Resolution evidence:** Pending until verified.

### ISSUE-009: Carga del archivo de configuración previsto

- **Status:** Under investigation
- **Severity:** Major
- **Affected files and functions:** `config/experiments_mdpi_full.json`; `1_0_poblarDB.py`; `2_main.py`; `Util/util.py::obtener_ruta_config`.
- **Observed behavior:** Ambos entry points aceptan `PSO_EXPERIMENTS_CONFIG`, pero usan `config/experiments.json` como valor por defecto. El log del batch histórico no registra la ruta ni el hash de la configuración cargada.
- **Expected behavior:** Población y ejecución usan exactamente el mismo JSON aprobado para el batch, y su ruta, hash y parámetros quedan registrados como procedencia inmutable.
- **Supporting evidence:** `1_0_poblarDB.py:12–13`; `2_main.py:120–125`; `config/experiments_mdpi_full.json` define el batch completo.
- **Scientific or methodological impact:** Cargar silenciosamente otro perfil puede cambiar número de corridas, dimensiones, workers, variantes, parámetros o semillas y hacer que el resultado no corresponda al protocolo declarado.
- **Required correction or verification:** Validar la variable de entorno antes de poblar y ejecutar; guardar una copia/hash del JSON efectivo en el manifiesto del batch y comprobar que ambos entry points reportan el mismo valor.
- **Acceptance criteria:** Una prueba previa confirma el path y SHA-256 de `experiments_mdpi_full.json` en ambos procesos, y verifica 62 instancias × 33 configuraciones × 31 réplicas = 63.426 experimentos.
- **Resolution evidence:** Pending until verified.

### ISSUE-010: Salida archivada de Tabla 11 no reproducible desde los datos nivel 1 actuales

- **Status:** Under investigation
- **Severity:** Major
- **Affected files and functions:** `FUZZY/ARTICULO_MDPI/code/12_analyze_rule_structure.py::compare_pairs`; `FUZZY/ARTICULO_MDPI/results/level1_raw/experiments_meta.csv`; `FUZZY/ARTICULO_MDPI/results/level1_raw/experiments_meta.parquet`; `FUZZY/ARTICULO_MDPI/results/level3_rankings/rule_pair_per_instance.csv`; `FUZZY/ARTICULO_MDPI/results/level3_rankings/rule_pair_summary.csv`; `FUZZY/ARTICULO_MDPI/manuscript/tables/tab_rule_pairs.tex`.
- **Observed behavior:** La comparación fila por fila entre el detalle archivado y los tests pareados recalculados con los datos nivel 1 actuales encontró discrepancias en 40 de 1.984 A12 y en 53 de 1.984 p-valores; 69 filas difieren en al menos uno de esos campos. Los A12 difieren en F14 (3 filas), F15 (3), F20 (13), F21 (6) y F22 (15). Los p-valores difieren en F8 (1), F9 (2), F12 (1), F13 (1), F14 (1), F18 (24), F20 (13), F21 (6) y F22 (4). Los CSV y Parquet nivel 1 actuales tienen los mismos datos de ejecuciones, así que la diferencia no se explica por elegir uno u otro formato. El resumen global de Tabla 11 oculta estos deltas porque los A12 medianos por contraste coinciden a la precisión publicada; al recomputar las clasificaciones pareadas solo R1 vs R2 cambia un caso (187/61/0 archivado frente a 188/60/0 recalculado).
- **Expected behavior:** La salida archivada debe reproducirse desde una versión identificada de los datos, script, parámetros y reglas de agrupación; cualquier cambio de versión debe generar una salida nueva trazable, sin presentar artefactos de distintas ejecuciones como un único análisis.
- **Supporting evidence:** `12_analyze_rule_structure.py:110–145,284–305` lee `experiments_meta.csv`, ordena muestras por `run_id`, calcula A12 y Wilcoxon y escribe `rule_pair_per_instance.csv`. `FUZZY/ARTICULO_MDPI/results/tests/independent_seed_reanalysis_20261014/summary.json` registra 40 discrepancias A12, 53 discrepancias de p-valores pareados y 69 filas con al menos una diferencia; `rule_pairs_independent_details.csv` conserva el detalle de comparación. El control de RQ4 reproduce los 1.984 A12 y p-valores archivados desde el mismo nivel 1, por lo que la falta de reproducción no es general a todos los análisis.
- **Scientific or methodological impact:** La causa no está determinada. El delta de A12 no puede atribuirse al cambio de Wilcoxon a Mann–Whitney, porque A12 se calcula sobre las distribuciones de ambas muestras y no depende del emparejamiento. Hasta reconciliar los artefactos, las magnitudes y algunas clasificaciones de significancia publicadas para los contrastes de reglas no tienen una procedencia reproducible demostrada.
- **Required correction or verification:** Rastrear la procedencia y hashes de los datos y scripts que generaron la salida archivada; verificar las 31 puntuaciones por configuración/instancia y sus IDs antes del test; ejecutar `12_analyze_rule_structure.py` contra una copia controlada de los datos en una carpeta nueva; comparar cada A12, p-valor, ganador y resumen. No sobrescribir resultados originales ni la tabla del manuscrito durante la investigación. Registrar qué versión de entrada y código es la autoritativa.
- **Acceptance criteria:** Para cada una de las 1.984 filas, A12, estadístico/p-valor, tratamiento de empates, ganador y agrupación se reproducen desde una entrada y commit identificados dentro de tolerancia declarada; cualquier delta restante queda explicado y vinculado a una versión distinta. Los nuevos artefactos se guardan separadamente y se someten a revisión antes de actualizar el artículo.
- **Resolution evidence:** Pending until verified.

## Lista de autorización previa al batch

- [ ] Aprobar y probar el contrato de semillas `42 + run_id` (43–73) y su persistencia por registro.
- [x] Corregir y probar F14; ejecutar y validar su reemplazo aislado de 1.023 corridas. Reanalizar las estadísticas/tablas del manuscrito sigue pendiente y no se realizó aquí.
- [ ] Completar las pruebas de referencia matemática de F1–F23.
- [ ] Verificar IDs explícitos de réplica, semilla efectiva, instancia y configuración, además de integridad y exportación.
- [ ] Validar asignación determinista y ausencia de omisiones/duplicados con seis workers.
- [ ] Confirmar población inicial común para el mismo bloque, si forma parte del diseño.
- [ ] Verificar NFE total incluyendo la población inicial y su descripción.
- [ ] Aprobar pruebas de equivalencia entre ecuaciones del manuscrito y código PSO/FCS ejecutado.
- [ ] Confirmar ruta y SHA-256 del JSON efectivo en población y ejecución.
- [ ] Reconciliar los artefactos de Tabla 11 con los datos nivel 1 y el script versionados antes de reutilizar sus afirmaciones.
- [ ] No autorizar el batch completo hasta que cada criterio aplicable tenga evidencia archivada y revisión aprobada.
