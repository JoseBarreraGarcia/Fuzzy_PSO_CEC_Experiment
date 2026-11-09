# Analysis

Análisis posterior sobre datos autoritativos: validación tabular, descriptivos,
rankings, convergencia, dinámica, estadística, corrección por multiplicidad,
tablas y visualización.

Las figuras son consumidoras de resultados; nunca son fuente de datos. Las
familias de hipótesis y unidades experimentales deben estar declaradas.

Estado: en desarrollo. La exportación canónica, reconciliación de ambos CSV
contra SQLite, carga de filas canónicas verificadas y un informe JSON
reproducible (descriptivos, rangos por instancia, Friedman y post hoc Nemenyi)
están implementados. El informe se genera solo después de reconciliar ambas
exportaciones; también se puede volver a calcular y contrastar contra SQLite
para detectar un artefacto ausente, inválido o desactualizado. Se reportan
familias omitidas y limitaciones inferenciales en vez de fabricar resultados.
Se generan ocho tablas CSV deterministas desde el informe, incluyendo
resúmenes y cobertura de convergencia, con manifiesto de hashes y conteos de
filas; también se reconcilian contra el informe. La convergencia usa únicamente
puntos observados en los conteos exactos de evaluaciones, sin interpolar, y
mantiene la procedencia de los valores. Se generan y reconcilian tres figuras
PNG: rangos descriptivos agregados, rangos Friedman por familia y curvas de
convergencia separadas por instancia/dimensión/dirección. Los manifiestos
incluyen versión de Matplotlib y hashes de cada imagen.
`run_campaign_analysis` automatiza exportación, reconciliación, informe,
tablas, figuras y verificación final. El análisis pareado también informa el
estimador Hodges-Lehmann además del rank-biserial. Los resúmenes de
`objective_best` y las curvas de convergencia conservan conteos por
procedencia; si el dato no trae procedencia, se informa explícitamente como no
disponible en el análisis directo de filas. La construcción del informe
canónico desde SQLite es más estricta: si falta la procedencia de una corrida
completada o su valor no coincide con el objetivo almacenado, se detiene con
error explícito en vez de producir un informe ambiguo.

Se conservan dos utilidades públicas de análisis directo, no adaptadores del
stack histórico ni dependencias del informe canónico:

- `summarize_convergence_curve` calcula media y desviación poblacional por
  **posición** de muestra. Exige número de corridas y longitudes iguales.
  Su campo `iterations` es `range(n)`, no índices observados ni NFE; el llamador
  debe demostrar alineación. No usarlo para reconstruir ejes de campañas.
- `aggregate_iteration_values` agrega campos explícitos con desviación
  muestral. Omite claves de grupo/iteración presentes pero nulas y valores
  numéricos faltantes/no finitos; los campos inexistentes y valores no numéricos
  fallan. Conserva grupos sin valores válidos. Es descriptivo, no una puerta
  de integridad experimental ni un sustituto de identidad/procedencia.

Esta conservación explícita evita retirar API pública útil sin necesidad.
No se conectan artificialmente al informe: para campañas, usar
`summarize_convergence` sobre filas reconciliadas con identidad, NFE y cobertura.
La inferencia pareada es también una API separada: elegir baseline/candidato
y su familia de hipótesis explícitamente antes de llamarla con filas canónicas.
Con dos tratamientos el informe automático no inventa Wilcoxon ni prueba
todos los pares: informa Friedman omitido y conserva los descriptivos.

La importación de bases históricas no forma parte del alcance activo de esta
API. El lector temporal y sus consumidores de `analysis_modules_cec` se
retiraron, junto con los orquestadores `3_0_analisis.py` y `3_3_analisisCEC.py`.
Mantener un consumidor antiguo funcionando no es motivo suficiente para integrar una
capacidad ni para declararla útil para una fase futura.

También se retiraron los analizadores `3_1_analisisBEN.py` y
`3_2_analisisSCP.py`, con sus originales verificados en Review. La exportación
de corridas, descriptivos y convergencia se realiza con los contratos canónicos
anteriores, no mediante lectores del esquema histórico. No se promete
equivalencia de nombres de salida, boxplots, violines ni gráficos de tiempos
por iteración. El análisis SCP sigue fuera del alcance activo.
No se conserva la agrupación BEN sólo por nombre de función/MH, que omite
dimensión y parámetros, ni el promedio de objetivos crudos entre funciones.
La identidad de corrida no se reconstruye por posición de fila. Los datos
ausentes o ilegibles no se reemplazan por XPL/XPT 50/50, fitness infinito
o tiempo cero como hacía el analizador SCP; las métricas v2 conservan su
procedencia y sus contratos de validación.

Desde R2-F, las estadísticas también conservan `InstanceIdentity`: ID local
positivo, familia/nombre/dimensión/dirección, óptimo, parámetros JSON canónicos,
hash opcional de datos y huella semántica versionada `problem_instance_v1`.
No se fusionan variantes distintas que comparten etiquetas ni se reconstruye
un ID ausente. Entradas directas requieren `instance_id` y
`problem_parameters_json`; metadatos contradictorios para un ID/campaña fallan.
La huella semántica no incluye ID local/campaña y no implica deduplicación
automática de bases ni certificación de equivalencia científica.

El informe y los manifiestos de tablas/figuras usan esquema 4: resúmenes y
cobertura conservan la identidad completa, Friedman lista identidades de
bloques incluidos/excluidos y los rangos agregados enumeran su cobertura exacta.
Las tablas usan celdas JSON para estas estructuras; la convergencia tiene un
panel por identidad, con ID y prefijo de huella en el título. Regenerar
artefactos anteriores desde SQLite; no renombrar su versión.
Pareado, Wilcoxon/Holm y Nemenyi mantienen sus fórmulas/protocolos, pero ahora
operan sobre los bloques correctos. La integridad best-so-far y del resultado
final se exige en el gate canónico de exportación/reconciliación/informe.
Véase el [contrato de análisis](../../../documentation/architecture/ANALYSIS_EXPORT.md#instance-identity-r2-f).

El paquete raíz `analysis_modules` se retiró: su exportación, descriptivos y
rankings están superados por los contratos anteriores, no incorporados mediante
adaptadores. Los paneles y resúmenes específicos de dinámica de `w` todavía no
están implementados aquí; sus fuentes de referencia y limitaciones quedan
en [ARCHIVE](../../../ARCHIVE/analysis/pso_dynamics/README.md), fuera de la API
y de las dependencias v2.

## Diagnóstico matemático de controladores

[`write_fuzzy_diagnostics`](fuzzy.py) recibe un `MamdaniController` canónico
y una carpeta explícita, sin base de datos ni JSON históricos:

```python
from afcs.analysis import write_fuzzy_diagnostics
from afcs.fuzzy import MamdaniController

controller = MamdaniController(
    granularity=5,
    rule_base="R5",
    membership_family="triangular_v1",
    diversity_overlap=0.5,
    progress_overlap=0.5,
    output_overlap=0.5,
)
manifest = write_fuzzy_diagnostics(controller, r"outputs\fuzzy_g5_r5")
```

Requiere el extra `analysis`. Produce `diagnostics.json`, tres PNG
(`memberships`, `rules`, `response`) y `manifest.json` con hashes SHA-256
y versión de Matplotlib. El JSON conserva particiones completas, política
de fronteras, modo de evaluación, malla del centroide, grados crudos,
matriz de consecuentes, coordenadas de respuesta, salida normalizada y
conteos de eventos de frontera. Los índices de etiquetas son cero-basados.
Las membresías crudas no incluyen el reemplazo categórico de la política
de frontera; la respuesta sí usa `controller.infer` y registra esos eventos.
En la respuesta, filas = progreso y columnas = diversidad; en las reglas,
filas = diversidad y columnas = progreso. Las figuras usan esos mismos
datos, sin interpolación visual de la respuesta ni recorte de sumas >1.

`grid_points` (entero >=2, predeterminado 41) controla la malla de respuesta
con extremos 0/1 incluidos. No implica un barrido exhaustivo ni garantiza
que se muestreen todas las fronteras de todas las granularidades. Las
membresías usan la malla del centroide del controlador. La respuesta es
normalizada: **no es `w` físico ni una observación de una corrida**; no prueba
rendimiento del optimizador y no se añade automáticamente al análisis de
campañas. Usar una carpeta distinta por configuración; una nueva llamada
reemplaza los archivos de diagnóstico, sin borrar archivos ajenos.

Como en las figuras de campañas, se prepara en staging y se instala el
manifiesto al final, mediante reemplazos individuales, no una transacción
atómica de directorio. Un fallo de renderizado no instala archivos; un fallo
durante los reemplazos puede dejar una mezcla que no coincida con los hashes
del manifiesto anterior. Los errores se propagan, no se devuelven figuras
vacías como éxito. No hay reconciliador automático de este diagnóstico;
los hashes detectan cambios de archivos, no certifican la verdad científica.
La identidad de PNG depende también del entorno; no se promete determinismo
binario entre versiones de Matplotlib.
