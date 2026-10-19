# Registro de incidencias técnicas y verificaciones

**Estado reconciliado al 2026-10-15.** Este registro distingue defectos confirmados, resoluciones en el análisis final, verificaciones parciales y mejoras para futuros experimentos. No es una autorización ni una exigencia de reejecutar el batch terminado. RQ3 permanece descriptiva; no se reabre su inferencia ni la interpretación de R1.

La [versión anterior](archive/editorial_material_sources_20261015/Errores_de_implementacion_pre_consolidation.md) conserva íntegros los diagnósticos iniciales. Los estados actuales se apoyan en el conjunto `final_dataset_20261015`, la verificación independiente y la evaluación posterior de Holm; las observaciones históricas no equivalen a pendientes actuales.

## 1. Incidencias confirmadas y resolución

### ISSUE-001: Metadata sintética de semillas y emparejamiento no justificado

- **Status:** Resolved in final data and analysis; runner and database redesign not performed.
- **Severity:** Major
- **Affected files and functions:** `2_main.py::worker_loop`; `BD/sqlite.py`; fuentes históricas `archive/code_legacy_20261015/00_generate_level1_raw_data.py`, `10_run_h4_wilcoxon_vs_baseline.py` y `12_analyze_rule_structure.py`; `code/21_recalculate_final_dataset.py`.
- **Observed behavior:** El runner histórico asignó `seed = 42 + id_experimento`. El exportador asignó después réplicas locales y `seed = 42 * run_id`, metadata sintética que no representaba las semillas ejecutadas. Los identificadores locales iguales entre configuraciones no establecían emparejamiento por semilla común.
- **Expected behavior:** Declarar el diseño realmente ejecutado y conservar semillas efectivas e identificadores trazables. Semillas distintas son compatibles con muestras independientes; usar semillas compartidas es una decisión de diseño, no un requisito universal. Incluso compartir semilla no garantiza trayectorias o consumos aleatorios equivalentes.
- **Scientific or methodological impact:** Las pruebas pareadas y el runtime unido por `run_id` no correspondían al diseño. El análisis final utiliza Mann–Whitney independiente con Bonferroni para RQ4, una familia separada con Holm para Tabla 11 y cocientes de medianas independientes para runtime. RQ3 usa dispersión descriptiva por función, sin bootstrap de bloques comunes de `run_id`.
- **Resolution evidence:** El [dataset consolidado](results/final_dataset_20261015/consolidated_level1.parquet) y el [CSV distribuido](manuscript/SupplementaryData_20261015/run_level_results.csv) contienen las 63.426 semillas distintas reconstruidas mediante `42 + historical_exp_id`. La [verificación independiente](results/final_dataset_20261015/analyses/independent_test_verification_provenance_20261015/verification_report.json) valida las pruebas sobre las muestras finales; la [evaluación Holm posterior](results/final_dataset_20261015/analyses/table11_holm_assessment_20261015/table11_holm_assessment.json) establece la política final de Tabla 11.
- **Remaining scope:** No se modificaron el contrato del runner ni el esquema de persistencia. El exportador antiguo permanece archivado, no corregido ni autorizado como flujo vigente. Las mejoras de persistencia se tratan en ISSUE-004; un futuro diseño con números aleatorios comunes requiere aprobación y verificación separadas.

### ISSUE-002: Pesos incorrectos en F14 (Shekel's Foxholes)

- **Status:** Resolved
- **Severity:** Major
- **Affected files and functions:** `Problem/Benchmark/Problem.py::F14`; `Problem/Benchmark/README_benchmark_functions.md`; `BD/sqlite.py::BD.insertarInstanciasBEN`; `config/experiments_mdpi_full.json` (`dimensiones.BEN.F14`); `FUZZY/ARTICULO_MDPI/manuscript/tables/tab_benchmark_fixed.tex`.
- **Observed behavior:** La implementación anterior usaba `[1,...,24,24]`. `Problem.py::F14` ahora usa `_F14_WEIGHTS = tuple(range(1, 26))`, es decir `[1,...,25]`. Dimensión 2, límites `[-65.536,65.536]` y óptimo de referencia 1 coinciden con la configuración documentada.
- **Expected behavior:** La suma de 25 términos debe usar los pesos `j=1,...,25`, de acuerdo con la definición canónica de Shekel's Foxholes.
- **Supporting evidence:** `Problem/Benchmark/Problem.py::F14`; `tests/test_f14_objective.py`; `FUZZY/ARTICULO_MDPI/code/20_prepare_corrected_f14.py`; `FUZZY/ARTICULO_MDPI/results/f14_corrected_20261014/`. Pasaron 3 pruebas: pesos exactos, evaluación de los 25 centros y valor del mínimo global aproximado `0.9980038378`. El dataset aislado contiene 1.023 corridas completas, 33 configuraciones × 31 réplicas, cero fallos; todos los IDs/semillas históricos son únicos, `actual_seed = 42 + historical_exp_id`, y el hash de `Problem.py` guardado en la procedencia coincide con el corregido. La primera pasada se interrumpió después de persistir 690 resultados; se respaldó la base aislada, se verificó que los seis IDs marcados `ejecutando` no tuvieran resultado/blob, se preservaron sus CSV parciales y se reencolaron solo esos IDs. La reanudación terminó las 333 filas restantes en 20 min 06 s, sin fallos. La comparación con el histórico encontró 4 fitness distintos por más de `1e-6`: ID 53464 / run 20 / FCS-3-R8 / seed 53506: `+2.8778636`; ID 53577 / run 9 / FCS-5-R4 / seed 53619: `+9.5004135`; ID 53954 / run 14 / FCS-7-R8 / seed 53996: `+4.8153639`; ID 54207 / run 19 / FCS-9-R8 / seed 54249: `-4.8153639`. Tres valores subieron y uno bajó; los otros 1.019 coinciden dentro de esa tolerancia. El fitness medio pasa de `4.24010855` a `4.25220853`; las medianas y el mejor valor global permanecen iguales (`2.98210516` y `0.99800384`, respectivamente). La base histórica y `Resultados/full_run.log` conservaron tamaño y fecha.
- **Scientific or methodological impact:** Las ejecuciones históricas de F14 correspondían a una variante de la función. Que el mínimo global permanezca igual no garantiza iguales resultados de optimización, especialmente cerca del centro 25. El conjunto final sustituye esas 1.023 ejecuciones por las corregidas.
- **Required correction or verification:** Corrección y reemplazo aislado completados. `code/21_recalculate_final_dataset.py` incorporó F14 al conjunto consolidado y recalculó los análisis afectados; su incorporación al manuscrito ya está completada, no pendiente.
- **Acceptance criteria:** Cumplidos para corrección, tests y batch F14: pesos `[1,...,25]`; pruebas de centros y mínimo aprobadas; exactamente 1.023 corridas terminadas en 33 configuraciones × 31; sin IDs o seeds ausentes/duplicados; procedencia de instancia/configuración/semilla incluida; dataset comparativo exportado; archivos históricos intactos.
- **Resolution evidence:** `tests/test_f14_objective.py` (3/3 passed); `FUZZY/ARTICULO_MDPI/results/f14_corrected_20261014/validation_report.json`; `final_execution_summary.json`; `corrected_f14_level1.csv`; `historical_vs_corrected_by_config.csv`; `recovery_20261014.json`; hash de la fuente corregida: `c376b83d0075473bfd0f4aa9fc2c3f6a166a59434ee8588026aff4db3dfcd19a`.
- **Final integration evidence:** [Validación del conjunto final](results/final_dataset_20261015/validation_report.json) y [tabla de benchmark vigente](manuscript/tables/tab_benchmark_fixed.tex). La corrección no autoriza otra ejecución del batch completo.

## 2. Verificaciones, procedencia y mejoras futuras

Los estados pendientes de esta sección no afirman por sí mismos un defecto ni ordenan reejecutar el artículo. Se distingue una comprobación parcial de una validación exhaustiva, y una mejora de infraestructura de la resolución estadística ya realizada.

### ISSUE-003: Concordancia matemática de F1–F23

- **Status:** Partially verified; exhaustive F1–F23 reference tests not completed.
- **Severity:** Major
- **Affected files and functions:** `Problem/Benchmark/Problem.py::F1`–`F23`; `Problem/Benchmark/README_benchmark_functions.md`; `BD/sqlite.py::BD.insertarInstanciasBEN`; tablas de benchmark del manuscrito.
- **Observed behavior:** La revisión de F14–F23 cotejó las diez dimensiones y dominios con la base de datos, la ruta del solver y el conjunto consolidado; 25 evaluaciones por función coincidieron con las expresiones tabuladas. Es una comprobación de consistencia, no una validación exhaustiva independiente de F1–F23 contra todas las referencias canónicas.
- **Expected behavior:** Cada función implementada coincide con su definición de referencia y con la dimensión, límites y óptimo documentados.
- **Supporting evidence:** `Problem/Benchmark/README_benchmark_functions.md` contiene la tabla de funciones, dimensiones, dominios y óptimos; F14 es el defecto confirmado separado en ISSUE-002.
- **Scientific or methodological impact:** Una discrepancia en cualquier función puede invalidar sus puntuaciones y alterar resultados agregados por instancia, función o clase.
- **Required correction or verification:** Añadir pruebas deterministas por función, con casos de referencia independientes, esquinas/centros pertinentes, dimensiones permitidas y óptimos conocidos. Registrar por separado cualquier discrepancia que se confirme.
- **Acceptance criteria:** Las 23 funciones pasan pruebas numéricas reproducibles contra referencias canónicas; dimensiones, límites y óptimos concuerdan con la configuración y el artículo.
- **Resolution evidence:** Comprobaciones de solo lectura de la sesión del 2026-10-15; funciones en `Problem/Benchmark/Problem.py`, registro de instancias en `BD/sqlite.py` y tabla `manuscript/tables/tab_benchmark_fixed.tex`. La nota vigente declara F17 sobre `[-5,5]^2`, no sobre el dominio convencional `[-5,10] x [0,15]`; conserva un minimizador global convencional. Las referencias mostradas están redondeadas; los gaps usan los valores configurados y clipping a cero. Las pruebas exhaustivas restantes no se declaran completadas.

### ISSUE-004: Persistencia de réplica, semilla e identificadores

- **Status:** Future infrastructure improvement; final exported identifiers recovered and verified.
- **Severity:** Major
- **Affected files and functions:** `BD/sqlite.py::BD.construirTablas`; `BD/sqlite.py::BD.insertarExperimentos`; `1_0_poblarDB.py::insertar_experimentos`; exportadores de resultados.
- **Observed behavior:** El esquema actual de `experimentos` almacena una clave global `id_experimento` y una clave foránea de instancia; no define columnas explícitas para `run_id`, semilla efectiva o ID de configuración.
- **Expected behavior:** Cada corrida recuperable identifica explícitamente su réplica, semilla efectiva, instancia y configuración, además del ID global del experimento.
- **Supporting evidence:** `BD/sqlite.py:61–73` define `experimentos`; `insertarExperimentos` inserta una fila por corrida sin campo de réplica o semilla; el exportador calcula `run_id` después de leer los resultados.
- **Scientific or methodological impact:** La ausencia de campos explícitos dificulta la trazabilidad directa y obliga a reconstrucción documentada. Las semillas históricas sí fueron recuperadas mediante la fórmula verificada; el conjunto consolidado y la exportación final conservan identificadores y semillas. Esto no equivale a una migración del esquema de SQLite.
- **Required correction or verification:** Diseñar y probar un esquema/versionado que almacene explícitamente `run_id`, semilla efectiva, ID de instancia e ID de configuración; comprobar integridad referencial y exportación sin reconstrucciones sintéticas.
- **Acceptance criteria:** Una consulta de solo lectura puede recuperar los cuatro identificadores para cada registro y comprobar unicidad, cardinalidad y correspondencia con la configuración fuente.
- **Resolution evidence:** Pending until verified.

### ISSUE-005: Reproducibilidad con seis workers

- **Status:** Future verification; no worker-order invariance test claimed.
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

- **Status:** Not required for the current independent-sample analysis; conditional future design check.
- **Severity:** Major
- **Affected files and functions:** `Solver/population/population_BEN.py::initialize_population`; `Solver/solverBEN.py::solverBEN`; `Metaheuristics/Codes/PSO.py::iterarPSO`; `Metaheuristics/Codes/PSO_FCS.py::iterarPSO_FCS`.
- **Observed behavior:** PSO y PSO_FCS usan posiciones generadas con `np.random.uniform`. El experimento terminado utilizó semillas distintas entre configuraciones y no exige poblaciones iniciales compartidas para el análisis independiente adoptado. No se ha implementado ni validado un contrato futuro de inicialización común.
- **Expected behavior:** Si el diseño requiere control por números aleatorios comunes, las configuraciones del mismo bloque instancia-réplica parten de la misma población, independientemente de su configuración y worker.
- **Supporting evidence:** `population_BEN.py:7–23`; el runner actualiza el RNG global antes de procesar cada experimento, pero el uso histórico de `exp_id` asigna semillas distintas a configuraciones del mismo `run_id`.
- **Scientific or methodological impact:** La variación inicial puede confundirse con efectos de configuración y limitar la interpretación de contrastes pareados.
- **Required correction or verification:** Definir si se exige población inicial común; si se exige, crearla una vez por instancia-réplica o usar un flujo RNG explícito y guardarla/reutilizarla sin que el consumo aleatorio posterior la altere.
- **Acceptance criteria:** Prueba que compara los vectores iniciales de todas las configuraciones del bloque confirma igualdad exacta o tolerancia especificada, también con seis workers.
- **Resolution evidence:** Pending until verified.

### ISSUE-007: Conteo de evaluaciones de la función objetivo

- **Status:** Manuscript budget clarified; instrumented call-count test still pending.
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

- **Status:** Future automated verification; no complete equivalence test claimed.
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

- **Status:** Future provenance improvement; historical configuration logging not retroactively repaired.
- **Severity:** Major
- **Affected files and functions:** `config/experiments_mdpi_full.json`; `1_0_poblarDB.py`; `2_main.py`; `Util/util.py::obtener_ruta_config`.
- **Observed behavior:** Ambos entry points aceptan `PSO_EXPERIMENTS_CONFIG`, pero usan `config/experiments.json` como valor por defecto. El log del batch histórico no registra la ruta ni el hash de la configuración cargada.
- **Expected behavior:** Población y ejecución usan exactamente el mismo JSON aprobado para el batch, y su ruta, hash y parámetros quedan registrados como procedencia inmutable.
- **Supporting evidence:** `1_0_poblarDB.py:12–13`; `2_main.py:120–125`; `config/experiments_mdpi_full.json` define el batch completo.
- **Scientific or methodological impact:** Cargar silenciosamente otro perfil puede cambiar número de corridas, dimensiones, workers, variantes, parámetros o semillas y hacer que el resultado no corresponda al protocolo declarado.
- **Required correction or verification:** Validar la variable de entorno antes de poblar y ejecutar; guardar una copia/hash del JSON efectivo en el manifiesto del batch y comprobar que ambos entry points reportan el mismo valor.
- **Acceptance criteria:** Una prueba previa confirma el path y SHA-256 de `experiments_mdpi_full.json` en ambos procesos, y verifica 62 instancias × 33 configuraciones × 31 réplicas = 63.426 experimentos.
- **Resolution evidence:** Pending until verified.

### ISSUE-010: Precisión de exportación y procedencia de Tabla 11

- **Status:** Resolved for the final analysis and distributed data.
- **Severity:** Major
- **Affected files and functions:** [Fuente histórica de Tabla 11](archive/code_legacy_20261015/12_analyze_rule_structure.py); CSV y Parquet históricos de `results/level1_raw/`; `code/21_recalculate_final_dataset.py`; `code/22_verify_independent_statistical_tests.py`; `code/23_table11_holm_assessment.py`.
- **Observed behavior and cause:** La salida histórica se reproduce exactamente desde el CSV que utilizó su generador: cero discrepancias en los 1.984 A12 y p-valores pareados. Al usar el Parquet histórico aparecen 40 discrepancias A12 y 53 de p-valores. La verificación posterior identificó diferencias de precisión en serialización/lectura del CSV, capaces de cambiar empates, rangos y diferencias numéricas. La sustitución de F14 constituye un cambio adicional separado. La afirmación anterior de que ambos formatos descartaban esa explicación queda superada.
- **Scientific or methodological impact:** A12 depende de las muestras y sus empates, no de elegir Wilcoxon o Mann–Whitney. Un resumen redondeado puede ocultar diferencias fila por fila. CSV no implica necesariamente pérdida de precisión: deben verificarse tanto la exportación concreta como su lectura.
- **Resolution evidence:** La [verificación de procedencia](results/final_dataset_20261015/analyses/independent_test_verification_provenance_20261015/verification_report.json) reproduce el archivo histórico y verifica independientemente los 1.984 tests finales de RQ4 y los 1.984 de Tabla 11. El informe registra diferencias máximas de p y A12 del orden de `1.11e-16` respecto del recálculo manual. Sus advertencias sobre una política de multiplicidad todavía pendiente son históricas: la [evaluación Holm posterior](results/final_dataset_20261015/analyses/table11_holm_assessment_20261015/table11_holm_assessment.json) aplica una única corrección a Tabla 11 y conserva 1.200 contrastes significativos. RQ4 mantiene su familia Bonferroni separada.
- **Distributed-data verification:** La comprobación de solo lectura realizada sobre el ZIP final reprodujo desde su CSV las 3.968 pruebas, A12 y decisiones ajustadas; sus 63.426 fitness coincidieron exactamente con el Parquet canónico mediante lectura round-trip. El paquete no necesita duplicar Parquet para resolver esta incidencia. Esta verificación estadística no equivale a distribuir un entorno ejecutable completo de PSO/FCS.
- **Acceptance criteria:** Conservar las entradas finales de precisión suficiente, sus identificadores y procedencia; reproducir efectos, p-valores y decisiones corregidas desde el archivo efectivamente distribuido. No regenerar Tabla 11 ejecutando la rutina pareada archivada.

## Lecciones técnicas reutilizables

- Separar ID global, índice de réplica, semilla efectiva y unidad inferencial; no deducir emparejamiento de nombres coincidentes.
- Verificar el archivo distribuido y la precisión de lectura, no solo hashes o igualdad aproximada de promedios. Contrastar empates, A12, p-valores y decisiones ajustadas.
- Comprobar fórmula, coeficientes, límites efectivos, dimensión y referencia de normalización a lo largo de la ruta ejecutada; una ficha descriptiva o un mínimo coincidente no prueba equivalencia del benchmark.
- Distinguir mínimo matemático, referencia configurada y valor mostrado con redondeo. Un gap recortado a cero no demuestra que se alcanzó exactamente el mínimo.
- Separar semántica nominal de reglas y sensibilidad efectiva del controlador. Consecuentes neutrales en una entrada no garantizan que la inferencia min–max sea independiente de ella; simetría de superficies tampoco implica equivalencia de rendimiento.
- Mantener estados y evidencia fechados: una resolución estadística no demuestra que el software histórico fue rediseñado, y una mejora futura no es por sí misma un defecto del experimento concluido.

## Comprobaciones para un futuro batch, si se autoriza

- [ ] Elegir explícitamente muestras independientes o bloques comunes y verificar el contrato de semillas correspondiente; no imponer retrospectivamente `42 + run_id` al batch cerrado.
- [ ] Persistir IDs y semillas efectivos, configuración y versiones; comprobar unicidad, integridad y exportación sin metadata sintética.
- [ ] Verificar orden de workers y recuperación de fallos con pruebas pequeñas; comparar poblaciones iniciales solo si el diseño exige compartirlas.
- [ ] Completar las pruebas matemáticas y de una iteración PSO/FCS aún no verificadas, además del conteo instrumentado de NFE.
- [ ] Registrar ruta y SHA-256 del JSON realmente cargado, código y dependencias.

Esta lista no inicia tareas ni invalida los cierres documentados de F14, RQ3, RQ4 o Tabla 11. Su ejecución requiere un alcance futuro autorizado.
