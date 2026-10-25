# Mapa modular y transición de rutas

## Cómo orientarse

El paquete objetivo se denomina provisionalmente `afcs`, por *Adaptive Fuzzy
Control System*. Cada carpeta responde a una pregunta concreta:

| Si necesito… | Debo ir a… |
|---|---|
| modelos compartidos, contratos y contexto de ejecución | `src/afcs/core/` |
| una función benchmark o problema de ingeniería | `src/afcs/problems/` |
| PSO, GA u otra metaheurística | `src/afcs/optimizers/` |
| políticas opcionales de ajuste de parámetros | `src/afcs/controllers/` y especializaciones del optimizador |
| calcular indicadores del proceso de búsqueda | `src/afcs/metrics/` |
| particiones, reglas o inferencia Mamdani | `src/afcs/fuzzy/` |
| elegir dinámicamente un esquema difuso | `src/afcs/selectors/` |
| coordinar selector, FIS y parámetro adaptado | `src/afcs/controllers/` |
| transferir, binarizar o reparar una solución | `src/afcs/binarization/` |
| planificar y ejecutar campañas | `src/afcs/experiments/` |
| guardar campañas, réplicas y trazas | `src/afcs/persistence/` |
| agregar, contrastar o visualizar resultados | `src/afcs/analysis/` |

## Rutas actuales y destinos

| Ruta actual | Destino v2 | Estado |
|---|---|---|
| `Problem/Benchmark/CEC/cec2017/` | `src/afcs/problems/benchmarks/cec2017/` | migrado; diagnóstico histórico permanece en origen |
| `Problem/Benchmark/Problem.py` | `src/afcs/problems/benchmarks/` | requiere separar dispatcher e implementaciones |
| `Problem/SCP/` | `src/afcs/problems/scp/` | pendiente de contrato común |
| `Problem/USCP/` | `src/afcs/problems/uscp/` | pendiente de contrato común |
| futuro KP | `src/afcs/problems/knapsack/` | planificado |
| `Metaheuristics/Codes/PSO.py` | `src/afcs/optimizers/pso/` | núcleo v2 y RNG aislados; wrapper heredado pendiente de retiro |
| `Metaheuristics/Codes/PSO_FCS.py` | PSO + `fuzzy/` + política PSO | separación v2 implementada; ruta histórica pendiente de clasificación final |
| `Metaheuristics/Codes/GA.py` | `src/afcs/optimizers/ga/` | planificado tras PSO |
| otras `Metaheuristics/Codes/*.py` | `src/afcs/optimizers/experimental/` | conservar y validar individualmente |
| `FUZZY/fuzzy_controller_auto.py` | `src/afcs/fuzzy/` + política del optimizador | primitivas e integración v2 disponibles; falta retirar/conservar la referencia heredada |
| controladores 3L/5L | `src/afcs/fuzzy/schemes/` | referencia y regresión de esquemas |
| `Discretization/` | `src/afcs/binarization/` | pendiente de clasificar transferencias y reglas |
| reparación en `Problem/SCP` | `src/afcs/binarization/repair/` o problema | decidir según dependencia del dominio |
| `Diversity/` | `src/afcs/metrics/diversity/` | primera familia de métricas existente |
| `Util/metrics_registry.py` | `src/afcs/metrics/registry.py` | migrado; puente temporal en origen |
| `BD/persistence_v2.py` | `src/afcs/persistence/database.py` | migrado; puente temporal en origen |
| `BD/repository_v2.py` | `src/afcs/persistence/repository.py` | migrado; puente temporal en origen |
| `BD/migrations/` | `src/afcs/persistence/migrations/` | migrado |
| `Solver/` | `src/afcs/experiments/` + optimizadores | flujo PSO v2 separado; otros solvers y consumidores heredados pendientes |
| `analysis_modules*` | `src/afcs/analysis/` | rescate guiado por `V2_ANALYSIS_RESCUE_MAP.md` |
| scripts numerados raíz | CLI + `scripts/` | no retirar hasta tener reemplazo probado |

## Estrategia de migración

1. Crear contrato y pruebas en el destino.
2. Migrar una responsabilidad, no una carpeta completa por nombre.
3. Mantener un adaptador temporal si hay consumidores heredados.
4. Actualizar imports, README y mapa.
5. Verificar que no quedan referencias a la ruta anterior.
6. Retirar la implementación duplicada.

No se mantendrán indefinidamente dos implementaciones autoritativas de la misma
capacidad.

La relación entre optimizadores, políticas opcionales y runner se especifica
en [`OPTIMIZER_PARAMETER_CONTROL.md`](OPTIMIZER_PARAMETER_CONTROL.md).
