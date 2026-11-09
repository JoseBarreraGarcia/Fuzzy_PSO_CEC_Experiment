# PSO

Implementación modular de Particle Swarm Optimization para AFCS v2.

## Componentes operativos

- `core.py`: transición numérica pura de posiciones y velocidades. No genera
  aleatoriedad, no evalúa objetivos y no conoce controladores ni persistencia.
- `policies.py`: `fixed_inertia`, los calendarios `legacy_ldiw`/`linear_endpoints_v1`
  y `FuzzyInertiaPolicy` sobre el controlador canónico de `afcs.fuzzy`.
- `optimizer.py`: ciclo completo en memoria, evaluación por NFE y actualización
  de `pbest`/`gbest` para minimización o maximización.
- Los wrappers históricos `PSO.py` y `PSO_FCS.py` ya se retiraron, junto
  con los controladores de `FUZZY/`; no son APIs v2. La ecuación y el clipping
  se caracterizan directamente en `tests/test_pso_motion_characterization.py`;
  el orden de matrices aleatorias se prueba en el optimizador en memoria.

Esta separación permite comparar políticas de inercia sin duplicar la ecuación
PSO ni acoplarla a SQLite, al sistema difuso o a una campaña particular.

## Compatibilidad histórica

Sin `velocity_rule` explícita, `LegacyCompatiblePSO` conserva:

- `c1 = c2 = 2` por defecto;
- `Vmax = 0.1 × ub[0]`, escalar;
- velocidad inicial igual a cero;
- clipping de posición después del movimiento;
- evaluación inicial más una población por iteración;
- comparación estricta al actualizar `pbest` y `gbest`;
- `legacy_ldiw` desde 0.9 hasta 0.1 según `max_iterations`.

El uso del primer límite superior para `Vmax` es una regla legacy, no una
recomendación general. El optimizador rechaza dominios cuyo primer límite
superior sea negativo porque esa fórmula produciría una velocidad máxima
inválida; no la sustituye silenciosamente por otra metodología.

## Aleatoriedad y semillas

El flujo v2 recibe `ReplicaRandomStreams`, construido desde la semilla persistida
de la réplica. Deriva mediante `SeedSequence` subflujos independientes para
`initialization` y `dynamics`; el consumo de uno no desplaza al otro. La vía
`rng=` se conserva como API in-memory soportada para inyección local, pero no
declara procedencia de réplica y no debe usarse en campañas v2. El lector la
usa también para obtener metadatos de plantilla, sin ejecutar el optimizador.

## Identidad de ejecución

Cada objeto PSO expone `OptimizerRunMetadata`, que describe de forma canónica:

- identidad y versión del optimizador;
- metadatos del problema;
- `cognitive`, `social` y `velocity_factor`;
- identidad, versión y configuración completa de la política de inercia;
- población y presupuestos de iteraciones y evaluaciones.

El runner compara estos datos con SQLite antes de iniciar una réplica. La
semilla y el motor RNG forman parte de los metadatos de ejecución, aunque no de
la firma compartida de la configuración algorítmica.

La identidad histórica congelada es `2.0.0a0-legacy-compatible` y se define
mediante `PSO_IMPLEMENTATION_VERSION`. Cambiar fórmulas, orden de operaciones,
inicialización, fronteras, velocidad o presupuesto exige una versión nueva y
pruebas de equivalencia o caracterización separadas.

Desde R2-G, `velocity_rule=domain_width_v1` selecciona
`2.0.0a1-domain-width`: Vmax[j]=factor*(ub[j]-lb[j]), recomendado para nuevos
experimentos. La política `linear_endpoints_v1` aplica máximo en movimiento
1 y mínimo en T para T>=2; T=1 usa máximo. FCS con
`diversity_metric=hussain_diversity_v2` conserva precisión interna y declara
política versión 2, sin cambiar progreso t/T. Se mantienen los defaults
históricos para no reinterpretar configuraciones omitidas ni bases existentes.
Ver [plantilla técnica](../../../../config/campaigns/classical_pso_recommended_v2.example.json).

## Límites actuales

- No se soporta tratamiento de restricciones. Una evaluación infactible o con
  violación no nula produce error explícito; no se selecciona silenciosamente
  sólo por objetivo ni se introduce penalización/reparación.
- `OptimizationTraceCollector` comparte checkpoints y observaciones
  poblacionales entre PSO y GA; `PSOTraceCollector` añade inercia y telemetría
  difusa. No se atribuyen estas métricas específicas a otros métodos.
- Las variantes que alteran algo más que la política de inercia requieren otra
  implementación o versión y no deben presentarse como una simple política.
