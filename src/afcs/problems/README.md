# Problems

Implementaciones y adaptadores de problemas de optimización: benchmarks
clásicos, CEC, SCP, USCP, KP y selección de características.

El contrato inicial incluye:

- `ProblemMetadata`: identidad, familia, espacio, dirección, óptimo conocido y
  parámetros de procedencia;
- `OptimizationProblem`: interfaz estructural consumida por optimizadores;
- `CallableProblem`: adaptador mínimo para objetivos escalares.
- `ProblemFactory`: registro extensible y fuente única para reconstruir una
  instancia desde su familia, dimensión, parámetros y subflujos aleatorios,
  independiente del optimizador que la consumirá.

La evaluación no rechaza automáticamente puntos fuera de los límites: decidir
entre limitar, reparar o penalizar corresponde al optimizador o al problema y
debe quedar registrado. Sí rechaza dimensiones incorrectas y valores no
finitos.

Estado: contrato base implementado. CEC2017 está autocontenido en
`benchmarks/cec2017/`. La suite clásica F1-F23 está consolidada en
`benchmarks/classical.py`, conserva equivalencia numérica con las fórmulas
históricas y valida dimensiones fijas. F7 conserva su ruido uniforme mediante
el subflujo RNG explícito `problem`, sin consumir el estado global de NumPy.
Las suites CEC suministradas por OPFUNU se integran mediante
`benchmarks/opfunu_cec.py` como familia separada `OPFUNU_CEC`; el año, la
función, la clase y la versión del paquete forman parte de su identidad
persistida. No se consideran intercambiables con la implementación CEC2017
autocontenida.
SCP, USCP y KP se conservan en `Problem/` como legado disponible, pero su
migración está pausada por decisión metodológica desde 2026-10-26. La siguiente
ampliación se evaluará primero entre problemas de ingeniería o benchmarks
continuos, evitando introducir por ahora binarización, transferencia y
reparación en el núcleo v2.
