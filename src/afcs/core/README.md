# Core

Contratos compartidos y neutrales respecto del algoritmo:

- `OptimizationDirection`, sin tolerancias ocultas;
- `SearchSpace`, con dimensión y límites finitos;
- `Evaluation`, para objetivo, factibilidad, violación y detalles;
- `EvaluationBudget`, contador explícito del número de evaluaciones (NFE).

No contiene algoritmos, problemas, persistencia, análisis ni generación de
semillas. El futuro `RunContext` se añadirá junto con el contrato de semillas
aprobado, para no anticipar esa decisión.

Estado: contratos fundamentales implementados y cubiertos por pruebas.
