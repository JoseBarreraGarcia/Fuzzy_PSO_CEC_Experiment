# PSO

Implementación incremental del núcleo Particle Swarm Optimization.

## Componentes actuales

- core.py contiene exclusivamente la transición numérica de posiciones y
  velocidades.
- policies.py contiene legacy_ldiw, la política histórica 0.9 → 0.1.
- PSOConfig declara los coeficientes cognitivo y social.
- Los wrappers de Metaheuristics/Codes conservan temporalmente las firmas
  históricas y generan r1/r2 antes de llamar al núcleo.

El núcleo:

- no genera números aleatorios;
- no evalúa la función objetivo;
- no calcula diversidad;
- no aplica límites de posición;
- no escribe archivos o bases de datos;
- no conoce controladores difusos.

Esta separación permite comparar políticas de inercia sin duplicar la ecuación
de movimiento.

## Compatibilidad

legacy_ldiw reproduce wMax=0.9, wMin=0.1 y el calendario por maxIter. Los
wrappers siguen aplicando Vmax=0.1×ub y c1=c2=2 para conservar la trayectoria
histórica. Esto no define la configuración recomendada para campañas nuevas.

## Pendiente

- política de inercia fija configurable;
- estado completo del enjambre y ciclo de evaluación;
- política explícita de límites de posición;
- inyección futura de generadores aleatorios, tras aprobar semillas;
- adaptador del controlador difuso;
- runner en memoria con presupuesto NFE.

