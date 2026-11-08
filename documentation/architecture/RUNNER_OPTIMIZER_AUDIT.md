# Auditoría del runner y congelamiento de PSO v2

**Fecha:** 8 de noviembre de 2026  
**Alcance:** plataforma v2 continua; SCP, USCP, KP y binarización permanecen en
pausa.

## Resultado

El ciclo de ejecución y la persistencia son neutrales respecto de la
metaheurística. `ExperimentRunExecutor` recibe cualquier objeto que cumpla
`RunnableOptimizer`, valida su identidad contra el plan persistido y registra
resultado, métricas, trazas o fallo sin inspeccionar PSO, CEC u OPFUNU.

El acoplamiento encontrado estaba en la reconstrucción: `_build_pso` contenía
la selección completa entre `CLASSICAL`, `CEC2017` y `OPFUNU_CEC`. Integrar GA
habría obligado a duplicar esa lógica y habría permitido divergencias entre
algoritmos sobre una misma instancia.

## Corrección aplicada

`afcs.problems.ProblemFactory` es ahora la fuente única para construir problemas
desde familia, dimensión, parámetros persistidos y subflujos aleatorios. Su
registro inicial contiene las tres familias matemáticas, pero acepta registros
alternativos sin modificar PSO ni el runner.

```text
PlannedRun
├── ProblemFactory   → OptimizationProblem
├── OptimizerFactory → RunnableOptimizer
└── ExperimentRunExecutor
    ├── valida plan ↔ ejecutable
    ├── ejecuta run()
    └── persiste resultado, trazas, métricas o fallo
```

La función clásica estocástica F7 obtiene exclusivamente el subflujo `problem`.
Las demás familias no consumen ese subflujo. Esto conserva el protocolo pareado
y evita desplazar la inicialización o dinámica del optimizador.

## PSO congelado como referencia

La implementación vigente se identifica como
`PSO/2.0.0a0-legacy-compatible`. La constante
`PSO_IMPLEMENTATION_VERSION` es la fuente única usada por los metadatos y la
reconstrucción desde SQLite.

Permanecen congelados bajo esa versión:

- población inicial uniforme dentro de los límites y velocidad inicial cero;
- subflujos separados `initialization` y `dynamics`;
- evaluación inicial seguida de una población por iteración;
- presupuesto `population_size × (max_iterations + 1)`;
- actualización común de velocidad, posición, `pbest` y `gbest`;
- comparación estricta y soporte de minimización/maximización;
- `Vmax = velocity_factor × ub[0]` y clipping de posición heredados;
- políticas `fixed_inertia`, `legacy_ldiw` y `fuzzy_inertia_mamdani`;
- checkpoint inicial posterior a evaluar la población inicial;
- validación exacta de NFE, problema, configuración y semilla.

Cualquier cambio en estas reglas requiere otra versión y una decisión
metodológica explícita. Una nueva política de `w` puede conservar la versión si
no altera el núcleo y posee identidad y versión propias.

## Acoplamientos restantes antes de GA

1. El JSON v1 sólo admite tratamientos `PSO`; debe extenderse con esquemas
   discriminados, sin convertir todos los campos PSO en opcionales.
2. `PSOTraceCollector` mezcla métricas poblacionales reutilizables con métricas
   de velocidad, inercia y controlador; deben declararse capacidades comunes y
   métricas no aplicables por optimizador.
3. Las políticas de inercia pertenecen al adaptador PSO, no al runner general.
4. GA debe entrar primero sin control externo y probar presupuesto NFE,
   dirección, semillas y replay antes de habilitar adaptación.

## Puerta para comenzar GA

La migración de GA puede comenzar cuando las pruebas confirmen:

- reconstrucción de las tres familias mediante `ProblemFactory`;
- igualdad de resultados PSO antes y después de la separación;
- una única identidad de versión PSO;
- ausencia de familias concretas en `ExperimentRunExecutor`.

No es necesario elegir todavía otro benchmark continuo ni reactivar problemas
binarios.

## Verificación

La separación quedó cubierta por pruebas de las tres familias, reproducción de
F7 con el subflujo `problem`, registro de familias externas y rechazo de
identidades inconsistentes. La regresión completa posterior al cambio ejecutó
144 pruebas satisfactoriamente.
