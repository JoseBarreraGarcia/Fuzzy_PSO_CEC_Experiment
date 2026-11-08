# PSO

Implementación modular de Particle Swarm Optimization para AFCS v2.

## Componentes operativos

- `core.py`: transición numérica pura de posiciones y velocidades. No genera
  aleatoriedad, no evalúa objetivos y no conoce controladores ni persistencia.
- `policies.py`: `fixed_inertia` y el calendario histórico `legacy_ldiw`.
- `optimizer.py`: ciclo completo en memoria, evaluación por NFE y actualización
  de `pbest`/`gbest` para minimización o maximización.
- Los wrappers de `Metaheuristics/Codes` conservan temporalmente sus firmas y
  delegan la ecuación de movimiento al núcleo común.

Esta separación permite comparar políticas de inercia sin duplicar la ecuación
PSO ni acoplarla a SQLite, al sistema difuso o a una campaña particular.

## Compatibilidad histórica

`LegacyCompatiblePSO` conserva las decisiones ya aprobadas:

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
`rng=` se conserva temporalmente para pruebas y compatibilidad incremental, pero
no identifica una réplica reproducible y no debe usarse en campañas v2.

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

La identidad congelada es `2.0.0a0-legacy-compatible` y se define una sola vez
mediante `PSO_IMPLEMENTATION_VERSION`. Cambiar fórmulas, orden de operaciones,
inicialización, fronteras, velocidad o presupuesto exige una versión nueva y
pruebas de equivalencia o caracterización separadas.

## Límites actuales

- Sólo se utiliza el valor objetivo retornado por el problema; la política para
  restricciones todavía debe definirse para problemas de ingeniería.
- La instrumentación disponible es poblacional y específica de PSO; debe
  separarse en observaciones comunes y específicas antes de integrar GA.
- Las variantes que alteran algo más que la política de inercia requieren otra
  implementación o versión y no deben presentarse como una simple política.
