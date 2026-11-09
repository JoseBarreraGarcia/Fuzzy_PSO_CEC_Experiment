# AFCS

Paquete del sistema adaptativo de control difuso para configuración de
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

Estado actual: paquete instalable desde `pyproject.toml`, con implementación
activa en `src/afcs` y CLI de campañas. El alcance operativo es continuo,
escalar y sin tratamiento de restricciones: PSO/PSO-FCS y GA real-coded;
problemas CLASSICAL, CEC2017 y OPFUNU_CEC. Selectores superiores, binarización y
discreto permanecen reservados/pausados, no son capacidades ejecutables.

La instalación editable y la suite del checkout no certifican distribución.
R3 verificó wheel/sdist e instalación no editable fuera del checkout en
Windows/Python 3.14.4, con núcleo NumPy y extras. CI y la matriz de soporte
siguen pendientes de R4; esto no autoriza publicación ni campañas científicas.
El estado y decisiones están en el
[plan de finalización](../../documentation/V2_PLATFORM_COMPLETION_PLAN.md).
No se requiere ni se reintroduce el stack histórico para ejecutar v2.
