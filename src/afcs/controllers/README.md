# Controllers

Coordina métricas, selector, esquema, inferencia y mapeo del resultado al
parámetro del optimizador. Mantiene la separación entre adaptación semántica y
adaptación de parámetros.

No contiene el paso interno de PSO/GA ni implementa por sí mismo Mamdani.
El control es opcional: una metaheurística puede ejecutarse sin adaptación
externa. Las políticas generales no deben asumir nombres como `w` o
`mutation_rate`; cada optimizador declara los parámetros compatibles.

`NoAdaptation`, políticas temporales, adaptación por métricas y control difuso
deben ser configuraciones identificables y persistibles. Las especializaciones
como `InertiaPolicy` pertenecen a la familia del optimizador, aunque puedan
delegar en este módulo.

Estado: contratos ParameterPolicy/ParameterUpdate y NoAdaptation implementados.
La orquestación difusa continúa mezclada en `FUZZY/` y `PSO_FCS.py`.
