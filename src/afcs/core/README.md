# Core

Contratos compartidos y neutrales respecto del algoritmo:

- `OptimizationDirection`, sin tolerancias ocultas;
- `SearchSpace`, con dimensión y límites finitos;
- `Evaluation`, para objetivo, factibilidad, violación y detalles;
- `EvaluationBudget`, contador explícito del número de evaluaciones (NFE).

No contiene algoritmos, problemas, persistencia ni análisis.
`RandomnessConfig` y `ReplicaRandomStreams` implementan el contrato pareado y
sus subflujos; un futuro `RunContext` reunirá este estado con la réplica.

Estado: contratos fundamentales implementados y cubiertos por pruebas.
