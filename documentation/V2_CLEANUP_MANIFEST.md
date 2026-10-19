# Manifiesto de limpieza y conservación para v2

**Rama de trabajo:** `Solver_CEC_Fuzzy_PSO_v2`  
**Referencia histórica:** `Solver_CEC_Fuzzy_PSO_ARTICULO_MDPI`  
**Commit histórico congelado:** `f8649134362f9a7b5e04f2f2bf032eb4b5938172`  
**Fecha de clasificación:** 19 de octubre de 2026  
**Estado:** propuesta revisable; este documento no ejecuta eliminaciones ni movimientos.

**Ejecución:** la primera ola comenzó tras la aprobación del manifiesto. Los
avances se registran en la sección 10 sin alterar la clasificación histórica.

## 1. Objetivo y reglas

Este manifiesto traduce el inventario inicial a decisiones concretas por ruta.
Su finalidad es limpiar la rama v2 sin perder implementaciones, análisis
estadísticos reutilizables ni conocimiento necesario para futuras campañas.

Las acciones utilizadas son:

| Código | Acción |
|---|---|
| `KEEP` | Conservar en v2 mientras se estabiliza la arquitectura. |
| `REFACTOR` | Conservar la funcionalidad, pero mover, parametrizar, probar o consolidar. |
| `LESSONS` | Extraer conocimiento estable hacia `documentation/lessons_learned/`. |
| `HISTORICAL` | Retirar de v2 después de comprobar su presencia en el commit histórico. |
| `GENERATED` | Retirar del control de versiones y añadir una regla de exclusión. |
| `REVIEW` | No actuar hasta resolver una dependencia o comprobar su procedencia. |

Una acción sobre una carpeta se aplica a su contenido salvo que exista una
excepción explícita. `HISTORICAL` no significa destruir: el archivo continúa
recuperable desde la rama y el commit indicados arriba.

## 2. Resumen ejecutivo

| Bloque | Acción dominante | Motivo |
|---|---|---|
| Núcleo de ejecución | `KEEP` + `REFACTOR` | Debe evolucionar sin una reescritura simultánea. |
| CEC2017 | `KEEP` | Ya dispone de correcciones y pruebas de regresión. |
| SCP y USCP | `KEEP` + `REFACTOR` | Son familias aprobadas para el núcleo v2. |
| Metaheurísticas | `KEEP` + `REFACTOR` | Se conservarán PSO, GA y el resto de implementaciones. |
| Controladores difusos | `KEEP` + `REFACTOR` | Son funcionalidad central y deberán independizarse de cada artículo. |
| Código de análisis | `REFACTOR` | Se reutilizará, unificará y probará con fixtures pequeños. |
| Artículos y manuscritos | `HISTORICAL` | No son necesarios para operar el framework compartible. |
| Resultados, figuras y temporales | `GENERATED` o `HISTORICAL` | Son regenerables o pertenecen a campañas cerradas. |

## 3. Núcleo y puntos de entrada

| Ruta | Acción | Tratamiento v2 |
|---|---|---|
| `2_main.py` | `REFACTOR` | Conservar comportamiento y migrarlo gradualmente a un runner/CLI probado. |
| `0_0_reiniciar.py`, `0_1_reiniciarDB.py`, `0_2_limpiarEntorno.py` | `REFACTOR` | Sustituir operaciones implícitas por comandos explícitos y seguros. |
| `1_0_poblarDB.py`, `1_1_crearBD.py` | `REFACTOR` | Integrar creación y población mediante migraciones/versionado de esquema. |
| `3_0_analisis.py` | `REFACTOR` | Convertirlo en orquestador de análisis parametrizable. |
| `3_1_analisisBEN.py`, `3_2_analisisSCP.py`, `3_3_analisisCEC.py` | `REFACTOR` | Extraer lógica reusable; retirar rutas globales y configuración al importar. |
| `9_db_scanner.py` | `REFACTOR` | Mantener como herramienta de diagnóstico bajo `scripts/`. |
| `Solver/` | `REFACTOR` | Conservar los solvers BEN/SCP y definir interfaces comunes para problemas y optimizadores. |
| `BD/sqlite.py` | `REFACTOR` | Conservar; separar repositorio, esquema, migraciones y conexión. |
| `Util/` | `REFACTOR` | Consolidar utilidades activas; convertir diagnósticos en comandos documentados. |
| `Discretization/discretization.py` | `KEEP` | Requerido por problemas binarios; añadir pruebas antes de moverlo. |
| `Diversity/` | `REFACTOR` | Conservar métricas usadas y validar nombres, fórmulas y contrato común. |

No se cambiarán en la primera limpieza los imports ni la ubicación de estos
archivos. El traslado a `src/` se hará después, módulo por módulo y con pruebas.

## 4. Familias de problemas

| Ruta | Acción | Tratamiento v2 |
|---|---|---|
| `Problem/Benchmark/Problem.py` | `REFACTOR` | Mantener el dispatcher actual hasta introducir una interfaz de benchmark. |
| `Problem/Benchmark/README_benchmark_functions.md` | `KEEP` + `LESSONS` | Conservar como contexto y trasladar advertencias estables a documentación técnica. |
| `Problem/Benchmark/CEC/cec2017/*.py` | `KEEP` | Implementación operativa; preservar las validaciones y pesos corregidos. |
| `Problem/Benchmark/CEC/cec2017/data.pkl` | `KEEP` | Dato funcional requerido por CEC2017 (aprox. 23,47 MB). |
| `Problem/Benchmark/CEC/cec2017/LICENSE.txt` | `KEEP` | Mantener licencia y atribución junto con la implementación. |
| `Problem/Benchmark/CEC/cec2017/CEC2017_OPERATIONAL.md` | `KEEP` | Documento operativo actual. |
| `Problem/Benchmark/CEC/cec2017/Diagnostico_CEC2017_PreExperimentos_Paper2.md` | `LESSONS` | Conservar el diagnóstico y consolidarlo sin perder trazabilidad. |
| `Problem/Benchmark/CEC/cec2017/example.py` | `REFACTOR` | Convertir en ejemplo mínimo ejecutable o prueba; evitar código suelto. |
| `Problem/Benchmark/CEC/cec2017/extra/plots.jpg` | `HISTORICAL` | Imagen auxiliar no necesaria para ejecutar las funciones. |
| `Problem/Benchmark/CEC/cec2017.rar` | `HISTORICAL` | Copia comprimida redundante con el árbol versionado. |
| `Problem/SCP/problem.py`, `Problem/USCP/problem.py` | `REFACTOR` | Adaptar al contrato común de problemas con restricciones y reparación. |
| `Problem/SCP/Instances/` | `KEEP` | Conservar inicialmente las 65 instancias; documentar origen/licencia y crear fixture mínimo aparte. |
| `Problem/USCP/Instances/` | `KEEP` | Conservar inicialmente las 75 instancias; documentar origen/licencia y crear fixture mínimo aparte. |
| `Problem/KP/` | futuro | Añadir después del contrato común, no como caso especial del runner. |

Los datasets completos de SCP/USCP suman aproximadamente 84,41 MB. No se
retirarán por tamaño mientras sean la única fuente operativa disponible. Una
decisión posterior podrá distribuirlos como paquete de datos, pero requiere
documentar primero procedencia, licencia y mecanismo de descarga verificable.

## 5. Metaheurísticas y control difuso

| Ruta | Acción | Tratamiento v2 |
|---|---|---|
| `Metaheuristics/Codes/PSO.py` | `REFACTOR` | Implementación de referencia inicial para el contrato de optimizador. |
| `Metaheuristics/Codes/PSO_FCS.py` | `REFACTOR` | Separar PSO del controlador y de la persistencia de trazas. |
| `Metaheuristics/Codes/GA.py` | `REFACTOR` | Conservar para la futura extensión del control difuso. |
| `Metaheuristics/Codes/*.py` | `KEEP` + `REVIEW` | Conservar todas las MH; clasificar luego como soportadas o experimentales mediante pruebas. |
| `Metaheuristics/Codes/PSO_tradicional.txt` | `LESSONS` | Comparar con `PSO.py`; extraer sólo explicación o lógica no incorporada. |
| `Metaheuristics/imports.py` | `REFACTOR` | Reemplazar el registro monolítico por descubrimiento/registro explícito. |
| `FUZZY/fuzzy_controller_auto.py` | `REFACTOR` | Conservar como controlador activo y definir interfaz independiente del optimizador. |
| `FUZZY/fuzzy_controller_w_3L.py` | `REFACTOR` | Conservar reglas 3L y añadir pruebas de propiedades. |
| `FUZZY/fuzzy_controller_w_5L.py` | `REFACTOR` | Conservar reglas 5L y añadir pruebas de propiedades. |
| `FUZZY/__init__.py` | `KEEP` | Mantener hasta la migración de paquete. |
| `FUZZY/0_limpiar_fuzzy_plots.py` | `REFACTOR` | Integrar la limpieza segura en una CLI; no mantener borrados ad hoc. |
| `FUZZY/1_generate_fuzzy_plots.py` a `FUZZY/7_compare_schemes.py` | `REFACTOR` | Conservar generadores y verificadores, parametrizar I/O y separar cálculo de presentación. |
| `FUZZY/compare_all_sets_w_values.py` | `REFACTOR` | Integrar comparaciones reutilizables en el paquete de análisis. |
| `FUZZY/fuzzy_plots.py`, `FUZZY/fuzzy_plots_06_10_parametric.py` | `REFACTOR` | Consolidar versiones y cubrir cálculos con pruebas. |
| `FUZZY/generate_mdpi_panels.py` | `HISTORICAL` + `REVIEW` | Extraer primero cualquier generador genérico; retirar el ensamblado específico MDPI. |
| `FUZZY/plots/tmp_plots_output.txt` | `GENERATED` | Salida temporal. |
| `FUZZY/prompt_pendientes` | `HISTORICAL` | Nota de trabajo no operativa. |

Ninguna metaheurística se elimina en la limpieza inicial. La condición para
declararla “soportada” será disponer de importación estable, smoke test y
contrato de retorno; las restantes podrán quedar marcadas como experimentales.

## 6. Código de análisis reusable

### 6.1 Módulos generales y CEC

| Ruta | Acción | Tratamiento v2 |
|---|---|---|
| `analysis_modules/` | `REFACTOR` | Conservar los 7 archivos; unificar carga de datos, rutas, estadísticas y salidas. |
| `analysis_modules_cec/` | `REFACTOR` | Conservar los 16 archivos; corregir métricas, eliminar rutas fijas y definir un pipeline único. |
| `analysis_modules_cec/README*.md` | `REFACTOR` | Actualizar tras consolidar; hoy documenta sólo parte de los módulos reales. |

La migración debe retener como capacidades, no necesariamente como archivos
separados: extracción de datos crudos, agregaciones, rankings, convergencia,
diversidad, dinámica de `w`, activación de reglas, escalabilidad, comparaciones
3L/5L, gráficos y pruebas estadísticas.

Antes de considerarlos núcleo v2, los análisis deberán:

1. recibir rutas o `DataFrame` como parámetros;
2. no abrir la base ni escribir resultados al importar;
3. validar columnas, número de réplicas y unidad experimental;
4. distinguir error absoluto, relativo y *gap* sin dividir por óptimos cero;
5. escribir sólo en un directorio de salida indicado;
6. probarse con fixtures tabulares pequeños y sintéticos.

### 6.2 Código rescatable del artículo MDPI

| Ruta | Acción | Tratamiento v2 |
|---|---|---|
| `FUZZY/ARTICULO_MDPI/code/04_run_scaling_curves.py` | `REFACTOR` | Extraer ajuste de pendientes y resumen de escalabilidad. |
| `FUZZY/ARTICULO_MDPI/code/15_generate_mean_dispersion_maps.py` | `REFACTOR` | Conservar cálculo/visualización; parametrizar entradas, réplicas y salidas. |
| `FUZZY/ARTICULO_MDPI/code/16_generate_benchmark_landscapes.py` | `REFACTOR` | Reubicar como visualización opcional de benchmarks; no recrear el suplemento por defecto. |
| `FUZZY/ARTICULO_MDPI/code/20_prepare_corrected_f14.py` | `LESSONS` + `REVIEW` | Preservar validaciones de F14; convertirlas en regresiones si aún no están cubiertas. |
| `FUZZY/ARTICULO_MDPI/code/21_recalculate_final_dataset.py` | `REFACTOR` | Extraer agregación, rankings, dinámica y contrastes sin rutas MDPI. |
| `FUZZY/ARTICULO_MDPI/code/22_verify_independent_statistical_tests.py` | `REFACTOR` | Convertir verificaciones Mann–Whitney/A12 en funciones y tests. |
| `FUZZY/ARTICULO_MDPI/code/23_table11_holm_assessment.py` | `REFACTOR` | Generalizar la corrección Holm por familia explícita de hipótesis. |
| `FUZZY/ARTICULO_MDPI/code/_naming.py` | `REFACTOR` | Conservar sólo convenciones generales; eliminar nombres editoriales. |
| `FUZZY/ARTICULO_MDPI/code/README.md` | `LESSONS` | Preservar orden y procedencia del pipeline histórico. |

Estos nueve archivos (aprox. 0,20 MB) permanecerán temporalmente donde están
hasta que cada capacidad tenga destino, prueba y documentación. Sólo entonces
se retirará el directorio MDPI completo de v2.

### 6.3 Análisis de WEA que debe rescatarse

| Ruta | Acción | Tratamiento v2 |
|---|---|---|
| `FUZZY/3.-WEA2026/wea_analysis.py` | `REFACTOR` | Extraer análisis factorial, Friedman, Wilcoxon, efecto de granularidad y reconstrucción de `w`. |
| `FUZZY/2.-CLEI2026/b2_convergence_*.py` | `REVIEW` | Comparar con el pipeline de convergencia CEC y consolidar la mejor versión. |
| Otros scripts `_debug_*`, `_inspect_*`, `_verify_*` dentro de artículos | `HISTORICAL` + `REVIEW` | Convertir comprobaciones útiles en tests antes de retirar el artículo. |

## 7. Material histórico de publicaciones

| Ruta | Archivos / tamaño aprox. | Acción | Excepción |
|---|---:|---|---|
| `FUZZY/ARTICULO_MDPI/archive/` | 232 / 192,96 MB | `HISTORICAL` | Extraer lecciones aún no consolidadas antes de retirar. |
| `FUZZY/ARTICULO_MDPI/results/` | 493 / 153,59 MB | `HISTORICAL` | No usar como fixtures; conservar hashes/esquema necesarios. |
| `FUZZY/ARTICULO_MDPI/manuscript/` | 77 / 54,11 MB | `HISTORICAL` | Ninguna dependencia operativa debe apuntar aquí. |
| Documentos raíz de `FUZZY/ARTICULO_MDPI/` | 9 | `LESSONS` + `HISTORICAL` | Consolidar errores, decisiones y reproducibilidad útiles. |
| `FUZZY/1.-OLA2026/` | 36 / 13,60 MB | `HISTORICAL` | Revisar `build_pptx.py` sólo si aporta utilidad general. |
| `FUZZY/2.-CLEI2026/` | 30 / 2,22 MB | `HISTORICAL` | Aplican las excepciones de análisis indicadas arriba. |
| `FUZZY/3.-WEA2026/` | 41 / 16,72 MB | `HISTORICAL` | Rescatar primero `wea_analysis.py`. |
| `FUZZY/ARTICULO_OVERLAP/` | 1 | `LESSONS` o `HISTORICAL` | Extraer roadmap general si sigue vigente. |
| `FUZZY/Literature_review/*.pdf` | parte de 18,37 MB | `HISTORICAL` | Sustituir por bibliografía/citas, respetando licencias. |
| `FUZZY/Literature_review/*.txt` | parte de 18,37 MB | `LESSONS` | Consolidar notas vigentes y registrar fuentes. |
| `documentation/Tesis_DII/` | 6 fuentes | `HISTORICAL` + `REVIEW` | Mantener sólo decisiones de arquitectura/metodología general. |
| `Explicaciones_Manuales/` | 5 / 9,14 MB | `LESSONS` + `HISTORICAL` | Extraer instrucciones útiles; retirar binarios/documentos redundantes. |

Antes de retirar cada bloque se ejecutará `git cat-file -e
f864913:<ruta>` o una comprobación equivalente. Además, el README principal
de v2 enlazará explícitamente la rama y el commit histórico.

## 8. Generados, binarios y temporales

| Ruta o patrón | Acción | Comprobación previa |
|---|---|---|
| `Graficos_Benchmark/**/*.pdf` | `GENERATED` | Conservar y probar `graficar_cec2017.py` y `graficosBenchmark.py`. |
| `Graficos_Benchmark/graficar_cec2017.py` | `REFACTOR` | Parametrizar salida y omitir CEC2017 F2. |
| `Graficos_Benchmark/graficosBenchmark.py` | `REFACTOR` | Mantener generador clásico. |
| `Graficos_Benchmark/w_strategy_comparison.py` | `REFACTOR` | Mover al análisis de dinámica si es general. |
| `Resultados/` | `GENERATED` | Ya está ignorado; no contiene archivos versionados. |
| `BD/*.db`, `BD/*.db-wal`, `BD/*.db-shm`, backups | `GENERATED` | Mantener solamente esquema/migraciones y datos fixture. |
| `tmp_plots_output.txt` | `GENERATED` | Ninguna. |
| `_fix_plot10.py`, `_fix_plots_08_10.py` | `HISTORICAL` | Los cambios de etiquetas ya aparecen en `wea_analysis.py`. |
| `_tmp_inspect_iter.py` | `HISTORICAL` | Es una inspección ad hoc de la base. |
| `tmp_verify_rules.py` | `REFACTOR` | Convertir sus comprobaciones de reglas/monotonicidad en tests antes de retirarlo. |
| `.vscode/` | `GENERATED` + `REVIEW` | Retirar configuración local; conservar sólo ajustes compartibles justificados. |
| `texput.log` | `GENERATED` | Ya está cubierto por `*.log`. |

Los artefactos duplicados identificados en el inventario (aprox. 158 MB sólo
en tres grupos SHA-256) quedan cubiertos por la retirada de resultados,
archivos y suplementos históricos; no se necesita elegir una copia para v2.

## 9. Configuración, documentación y calidad

| Ruta | Acción | Tratamiento v2 |
|---|---|---|
| `config/experiments_cec2017.json` | `KEEP` | Ejemplo mínimo válido para CEC2017. |
| `config/experiments.json` | `REFACTOR` | Separar problema, algoritmo, campaña y análisis. |
| `config/directories.json` | `REFACTOR` | Evitar rutas ligadas al directorio de ejecución. |
| `config/analysis.json` | `REFACTOR` | Sustituir flags implícitos por configuración validada. |
| `config/fuzzy_partitions.json`, `config/fuzzy_plots.json` | `REFACTOR` | Mantener parámetros generales y validar esquema. |
| `config/analysis_mdpi.json` | `HISTORICAL` | Configuración de una campaña cerrada. |
| `config/experiments_mdpi_full.json`, `config/experiments_mdpi_smoke.json` | `HISTORICAL` + `LESSONS` | Conservar en la rama histórica; derivar ejemplos v2 sin afirmar reproducibilidad retroactiva. |
| `config/PROPUESTA_IMPLEMENTACION_SEMILLAS.md` | `KEEP` | Contrato aprobado para la fase independiente de semillas. |
| `documentation/1_*` a `documentation/6_*` | `REFACTOR` | Corregir instrucciones obsoletas y consolidar guía del sistema difuso. |
| `documentation/hierarchical_analysis_guide.md` | `REFACTOR` | Integrar con la documentación del pipeline estadístico. |
| `documentation/V2_*.md` | `KEEP` | Registro de decisiones y migración. |
| `tests/` | `KEEP` + `EXPAND` | Mantener regresiones CEC/F14 y agregar runner, BD, MH, control difuso y análisis. |
| `.github/` | `REVIEW` | Conservar únicamente automatización válida; crear CI v2 después del empaquetado. |
| `requirements.txt` | `REFACTOR` | Fijar dependencias directas y migrar después a `pyproject.toml`. |
| `README.md` | `REFACTOR` | Reescribir para v2 e incluir recuperación del estado MDPI. |

## 10. Orden seguro de ejecución

### Ola 1 — reglas y basura inequívoca

1. Ampliar `.gitignore` para temporales, salidas de análisis y figuras.
2. Convertir `tmp_verify_rules.py` en pruebas.
3. Retirar temporales raíz y scripts `_fix_*` ya absorbidos.
4. Retirar PDFs generados de `Graficos_Benchmark/` conservando generadores.
5. Ejecutar las pruebas actuales y nuevos tests de reglas.

Avance ejecutado:

- [x] Se añadieron exclusiones para gráficos de benchmark y temporales.
- [x] `tmp_verify_rules.py` se convirtió en pruebas automáticas para las ocho
  matrices 3L y 5L.
- [x] Se corrigió la integración numérica de los controladores para NumPy 2.4.
- [x] Se retiraron los temporales raíz y los dos scripts `_fix_*` absorbidos.
- [x] Se retiraron 106 PDFs regenerables de `Graficos_Benchmark/` (aprox.
  89,62 MB), conservando sus generadores.
- [x] El generador CEC2017 omite F2, retirada de la suite oficial.
- [x] La batería ampliada aprueba 15 de 15 pruebas.

### Ola 2 — rescate de conocimiento y análisis

1. Crear `documentation/lessons_learned/`.
2. Consolidar diagnósticos CEC2017, errores del artículo y decisiones de
   reproducibilidad sin modificar el registro histórico.
3. Crear un paquete único de análisis con I/O parametrizable.
4. Migrar capacidades de `analysis_modules*`, MDPI y WEA con fixtures.
5. Verificar equivalencia numérica sobre extractos pequeños autorizados.

Avance ejecutado:

- [x] Se creó `documentation/lessons_learned/` con trazabilidad histórica.
- [x] Se consolidaron las condiciones operativas y regresiones de CEC2017.
- [x] Se formalizaron réplica, SQLite autoritativa, sellado de campaña,
  selección de métricas y análisis jerárquico con familias Holm explícitas.
- [x] Se inventariaron las capacidades estadísticas y sus fuentes actuales en
  `documentation/V2_ANALYSIS_RESCUE_MAP.md`.
- [x] Se identificaron reconstrucciones de métricas que deberán etiquetarse y
  el defecto de trazas `Divj_max0` pendiente de corrección.
- [x] Se implementó el registro versionado inicial de 28 métricas y el
  resolvedor validado para perfiles, `all` y listas explícitas.
- [x] Se crearon fixtures tabulares sintéticos para réplicas y trazas.
- [ ] Falta integrar el registro con los solvers y el futuro esquema SQLite.
- [ ] Falta migrar las funciones autoritativas de análisis sobre los fixtures.
- [ ] No se ha retirado todavía ningún árbol histórico de análisis.

### Ola 3 — separación de publicaciones

1. Añadir al README la guía de recuperación histórica.
2. Comprobar todas las rutas `HISTORICAL` contra `f864913`.
3. Retirar resultados, manuscritos, archivos, figuras y literatura binaria.
4. Confirmar que `rg` no encuentra imports ni rutas operativas hacia los
   árboles retirados.
5. Ejecutar pruebas y un smoke test extremo a extremo.

### Ola 4 — arquitectura v2

1. Introducir `pyproject.toml` y el paquete `src/`.
2. Migrar problemas, optimizadores, controladores, runner y persistencia en
   cambios pequeños.
3. Implementar después, en commit independiente, la propuesta de semillas.

## 11. Criterios de aceptación de la limpieza

La limpieza estará terminada cuando:

- el README identifique claramente v2 y cómo recuperar el artículo MDPI;
- ningún módulo operativo dependa de rutas de un manuscrito o campaña;
- no haya bases, resultados masivos, figuras regenerables ni temporales
  versionados;
- CEC2017, BEN, SCP y USCP tengan al menos un smoke test representativo;
- PSO y PSO_FCS ejecuten un caso pequeño; GA tenga al menos prueba de carga;
- las demás MH estén inventariadas como soportadas o experimentales, no
  eliminadas silenciosamente;
- el análisis estadístico opere con entradas y salidas configurables;
- las pruebas no utilicen datasets completos del artículo;
- `python -m unittest discover -s tests -v` permanezca verde durante la
  transición.

## 12. Decisiones aún pendientes, sin bloquear la primera ola

1. Licencia y canal futuro de distribución de las instancias SCP/USCP.
2. Qué metaheurísticas cumplen el contrato v2 sin adaptación.
3. Formato tabular canónico para resultados y trazas de iteración.
4. Qué análisis MDPI/WEA son equivalentes y cuál será su implementación
   autoritativa.
5. Si los documentos de tesis vivirán en otro repositorio o sólo en la rama
   histórica.
6. Política para artefactos científicos publicados fuera de Git (release,
   repositorio institucional o almacenamiento con DOI).

Estas decisiones no autorizan borrar contenido adicional. Cualquier ruta no
incluida aquí conserva por defecto el estado `REVIEW`.
