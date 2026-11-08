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

Para figuras históricas basadas en iteraciones, `summarize_convergence_curve`
calcula media y desviación estándar poblacional por checkpoint. Exige el número
esperado de corridas y trazas de longitud idéntica; no trunca ni completa datos.
Este resumen por iteración es distinto de `summarize_convergence`, que resume
puntos observados en conteos exactos de evaluaciones mediante mediana y cuartiles.
`aggregate_iteration_values` proporciona la agregación agrupada de trazas
heredadas con desviación estándar muestral, ignorando valores faltantes y
reteniendo grupos sin observaciones válidas; no sustituye al resumen
poblacional de curvas de longitud fija.
