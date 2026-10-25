# Solver CEC Fuzzy PSO — plataforma experimental v2

Este repositorio está evolucionando hacia una plataforma reproducible para
investigar control difuso adaptativo de metaheurísticas. El desarrollo inicial
se concentra en PSO y benchmarks continuos, pero la arquitectura contempla GA,
otros optimizadores clásicos y problemas discretos como SCP, USCP y Knapsack.

> **Estado:** transición avanzada a v2. CEC2017, PSO, control difuso, semillas,
> campañas secuenciales, métricas y persistencia SQLite ya operan en el paquete
> nuevo y cuentan con pruebas. Todavía no es una versión de producción: faltan
> endurecimiento, paralelismo validado, más familias de problemas/optimizadores,
> análisis reutilizable y limpieza final.

## Preservación del artículo MDPI

El estado utilizado para los experimentos y resultados históricos se conserva
sin reinterpretarlo en:

- rama: `Solver_CEC_Fuzzy_PSO_ARTICULO_MDPI`;
- commit congelado: `f8649134362f9a7b5e04f2f2bf032eb4b5938172`.

La rama `Solver_CEC_Fuzzy_PSO_v2` contiene la reorganización y las mejoras para
nueva experimentación. Los resultados obtenidos con v2 no deben atribuirse
retroactivamente al artículo.

## Orientación rápida

| Necesidad | Ubicación |
|---|---|
| visión científica y alcance de la tesis | [`documentation/PROJECT_VISION.md`](documentation/PROJECT_VISION.md) |
| mapa de módulos y migración de rutas | [`documentation/architecture/MODULE_MAP.md`](documentation/architecture/MODULE_MAP.md) |
| optimizadores y control opcional de parámetros | [`documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md`](documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md) |
| plan general de migración | [`documentation/V2_MIGRATION_PLAN.md`](documentation/V2_MIGRATION_PLAN.md) |
| ruta para terminar la plataforma | [`documentation/V2_PLATFORM_COMPLETION_PLAN.md`](documentation/V2_PLATFORM_COMPLETION_PLAN.md) |
| decisiones de limpieza por archivo | [`documentation/V2_CLEANUP_MANIFEST.md`](documentation/V2_CLEANUP_MANIFEST.md) |
| contrato experimental y estadístico | [`documentation/lessons_learned/EXPERIMENT_DATA_AND_ANALYSIS.md`](documentation/lessons_learned/EXPERIMENT_DATA_AND_ANALYSIS.md) |
| diseño de SQLite v2 | [`documentation/architecture/SQLITE_V2_SCHEMA.md`](documentation/architecture/SQLITE_V2_SCHEMA.md) |
| contrato implementado de semillas | [`config/PROPUESTA_IMPLEMENTACION_SEMILLAS.md`](config/PROPUESTA_IMPLEMENTACION_SEMILLAS.md) |
| diagnóstico y uso de CEC2017 | [`Problem/Benchmark/CEC/cec2017/CEC2017_OPERATIONAL.md`](Problem/Benchmark/CEC/cec2017/CEC2017_OPERATIONAL.md) |
| contexto doctoral incorporado | [`Tesis/CONTEXTO_TESIS_DOCTORAL_CODEX.md`](Tesis/CONTEXTO_TESIS_DOCTORAL_CODEX.md) |

La organización objetivo vive bajo [`src/afcs/`](src/afcs/README.md). Por ahora,
sus README funcionan como contratos de responsabilidad y guía de navegación;
el código heredado seguirá en sus rutas actuales hasta que cada migración tenga
pruebas y una sustitución funcional.

## Capacidades v2 ya preparadas

- registro validado y versionado de métricas, con perfiles y selección explícita;
- fixtures sintéticos para pruebas de análisis y persistencia;
- esquema SQLite v2 idempotente;
- repositorio transaccional para campañas, réplicas, trazas y métricas;
- regresiones y condiciones operativas documentadas para CEC2017;
- mapa de rescate del análisis estadístico reutilizable;
- estructura modular para lógica difusa, selectores, controladores,
  binarización, problemas, optimizadores y análisis.
- semillas pareadas por réplica, subflujos explícitos y hashes de condiciones
  iniciales;
- PSO v2 con políticas fija, lineal heredada y control Mamdani de `w`;
- campañas configurables con `preview`, planificación y ejecución secuencial;
- trazas y diagnósticos internos del controlador difuso.

## Validación del estado actual

Desde PowerShell, con el entorno virtual y las dependencias ya instaladas,
instale el paquete v2 en modo editable y ejecute las pruebas:

```powershell
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

La arquitectura ya permite validaciones técnicas pequeñas, pero las campañas
científicas no deben iniciarse hasta terminar la plataforma y congelar el
protocolo metodológico correspondiente. La validación técnica actual no es
evidencia para artículos.

## Regla de evolución

Cada capacidad tendrá una sola implementación autoritativa. El proceso será:
crear contrato y pruebas, migrar una responsabilidad, actualizar consumidores y
documentación, verificar equivalencia y sólo entonces retirar el código
duplicado. Las decisiones que cambien fórmulas, hipótesis, unidad experimental o
metodología se someterán a aprobación antes de implementarse.
