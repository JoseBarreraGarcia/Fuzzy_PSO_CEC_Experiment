# Problems

Implementaciones y adaptadores de problemas de optimización: benchmarks
clásicos, CEC, SCP, USCP, KP y selección de características.

El contrato inicial incluye:

- `ProblemMetadata`: identidad, familia, espacio, dirección, óptimo conocido y
  parámetros de procedencia;
- `OptimizationProblem`: interfaz estructural consumida por optimizadores;
- `CallableProblem`: adaptador mínimo para objetivos escalares.

La evaluación no rechaza automáticamente puntos fuera de los límites: decidir
entre limitar, reparar o penalizar corresponde al optimizador o al problema y
debe quedar registrado. Sí rechaza dimensiones incorrectas y valores no
finitos.

Estado: contrato base implementado. CEC2017 ya fue migrado de forma
autocontenida a `benchmarks/cec2017/` y dispone de un adaptador probado; las
demás familias siguen en `Problem/`.
