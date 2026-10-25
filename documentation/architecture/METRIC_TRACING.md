# Instrumentación y trazas v2

## Semántica temporal

Una observación representa siempre una población completamente evaluada:

```text
checkpoint 0: población inicial evaluada, NFE = N, sin w aplicado
checkpoint 1: población tras transición 0→1, NFE = 2N, w usado en 0→1
...
checkpoint t: población tras transición t-1→t, NFE = (t+1)N
```

`checkpoint_index` identifica el orden de las filas almacenadas e
`iteration_index` conserva la iteración algorítmica. Ambos sólo coinciden cuando
se registra cada iteración. NFE es el eje principal para comparar algoritmos.

La ausencia de `inertia_weight` en el checkpoint 0 significa “no aplicable”; no
se almacena `NaN` ni un valor programado que todavía no haya sido usado.

## Muestreo

`TraceSampling` implementa el bloque `trace` de la campaña. La configuración
aprobada registra el estado inicial, todas las iteraciones y el estado final. Si
`every_iterations` es mayor que uno, el punto final se registra aunque no sea
múltiplo de la frecuencia. La configuración resuelta queda congelada en SQLite.

## Métricas PSO operativas

`PSOTraceCollector` calcula exclusivamente métricas seleccionadas y no consume
RNG ni modifica el estado del enjambre. Actualmente produce:

- iteración, tiempo y NFE;
- mejor objetivo, media y desviación poblacional;
- diversidad global de Hussain;
- porcentajes de exploración y explotación;
- entropía poblacional;
- diversidad media, mínima y máxima por dimensión;
- peso de inercia efectivamente aplicado.

Para `fuzzy_inertia_mamdani` también persiste desde la primera transición:

- progreso exacto `iter/maxIter` y entrada Hussain normalizada;
- grados de pertenencia por antecedente;
- reglas activas y sus fuerzas de disparo;
- salida normalizada anterior al escalamiento de `w`;
- reglas evaluadas y omitidas por el modo de inferencia;
- tiempo exclusivo de cada llamada al FIS;
- eventos de frontera `tie → upper`, ausencia de activación y fallbacks.

Estas variables no aparecen en el checkpoint 0 porque el controlador todavía
no ha sido consultado. La diversidad poblacional de ese checkpoint sí se
registra y sirve para inicializar el máximo histórico de la primera decisión.

Las fórmulas se migraron a `afcs.metrics.tracing` con sufijo de versión `v1` y
pruebas de equivalencia frente al código heredado. Sus definiciones pasaron a
versión 2 en el registro, y el registro completo a `schema_version=2`.

La implementación v2 corrige el error heredado de `solverBEN.py` que escribía
`divj_max0` en todas las iteraciones: ahora cada checkpoint almacena el máximo
por dimensión de su propia población.

## Atomicidad y procedencia

Todas las trazas de una réplica y su resultado final se escriben en una misma
transacción. Si falla la validación o persistencia de una métrica, no queda una
traza parcialmente aceptada como resultado completo y la réplica se marca como
fallida. Cada valor conserva el ID y la versión de su definición.

## Pendiente

- medir el costo de instrumentación en campañas representativas;
- validar estrategias de reducción de frecuencia para experimentos masivos;
- implementar métricas equivalentes para GA y otras metaheurísticas;
- acordar la política de recuperación de una réplica interrumpida en `running`.

El tiempo exclusivo del FIS y los resúmenes por réplica ya están implementados.
También se registran reglas evaluadas y omitidas para distinguir el costo lógico
de `dense_v1` y `sparse_v1`; su comparación de rendimiento requiere todavía el
microbenchmark controlado.

## Fundamento metodológico

La separación entre inicialización evaluada y primera transición sigue el
algoritmo PSO estándar: primero se evalúan las partículas y se establecen los
mejores; después se actualizan velocidad y posición. Para comparación entre
algoritmos se prioriza NFE, coherente con los loggers de COCO/BBOB activados por
evaluaciones. El seguimiento separado de parámetros adaptativos sigue la
motivación de IOHprofiler.

Referencias:

- Kennedy, J. y Eberhart, R. (1995), *Particle Swarm Optimization*,
  DOI `10.1109/ICNN.1995.488968`.
- COCO/BBOB, implementación oficial de `logger_bbob`:
  <https://github.com/numbbo/coco/blob/master/code-experiments/src/logger_bbob.c>.
- Doerr et al., *IOHprofiler: A Benchmarking and Profiling Tool for Iterative
  Optimization Heuristics*: <https://arxiv.org/abs/1810.05281>.
