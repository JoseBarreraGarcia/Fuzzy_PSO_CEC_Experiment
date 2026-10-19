# AFCS

Paquete objetivo del sistema adaptativo de control difuso para configuración de
metaheurísticas. Consulte cada módulo para saber qué responsabilidad posee.

| Módulo | Responsabilidad |
|---|---|
| `core` | contratos y modelos compartidos |
| `problems` | evaluación de problemas e instancias |
| `optimizers` | estado y pasos de metaheurísticas |
| `metrics` | indicadores online y catálogo |
| `fuzzy` | semántica e inferencia difusa pura |
| `selectors` | selección superior de esquemas |
| `controllers` | coordinación adaptativa e inyección de parámetros |
| `binarization` | transferencia, discretización y reparación |
| `experiments` | planificación y ejecución |
| `persistence` | almacenamiento y procedencia |
| `analysis` | análisis posterior y visualización |

Estado actual: estructura reservada y documentada; todavía no es un paquete
instalable ni sustituye los módulos heredados.
