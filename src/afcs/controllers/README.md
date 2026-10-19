# Controllers

Coordina métricas, selector, esquema, inferencia y mapeo del resultado al
parámetro del optimizador. Mantiene la separación entre adaptación semántica y
adaptación de parámetros.

No contiene el paso interno de PSO/GA ni implementa por sí mismo Mamdani.

Estado: planificado; parte de esta responsabilidad está mezclada actualmente en
`FUZZY/` y `PSO_FCS.py`.
