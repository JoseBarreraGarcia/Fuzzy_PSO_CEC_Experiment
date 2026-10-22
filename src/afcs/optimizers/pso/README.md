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

El constructor exige un `numpy.random.Generator` creado por el llamador. Esta
inyección elimina el estado aleatorio global del nuevo ciclo, pero **no**
implementa el protocolo de semillas: no genera semillas maestras, no deriva
subflujos y no asigna semillas a campañas o réplicas. Esa integración sigue
reservada para su fase independiente.

## Límites actuales

- Sólo se utiliza el valor objetivo retornado por el problema; la política para
  restricciones todavía debe definirse para problemas de ingeniería.
- Aún no existe recolección de métricas ni persistencia durante la corrida.
- El controlador difuso todavía no está adaptado a `ParameterPolicy`.
- El runner de campañas todavía no consume este optimizador.
