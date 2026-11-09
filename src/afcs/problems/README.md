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

La [guía de familias](../../../documentation/architecture/BENCHMARK_FAMILIES.md)
separa configuración, identidad, dimensiones y límites de la evidencia
matemática. El dispatcher y el catálogo duplicado de `Problem/Benchmark/`
se retiraron; los valores de regresión capturados ya no importan ese legado.

La evaluación no rechaza automáticamente puntos fuera de los límites: decidir
entre limitar, reparar o penalizar corresponde al optimizador o al problema y
debe quedar registrado. Sí rechaza dimensiones incorrectas y valores no
finitos.

Estado: contrato base implementado. CEC2017 está autocontenido en
`benchmarks/cec2017/`. La suite clásica F1-F23 está consolidada en
`benchmarks/classical.py`, conserva equivalencia numérica con las fórmulas
históricas y valida dimensiones fijas. F7 conserva su ruido uniforme mediante
el subflujo RNG explícito `problem`, sin consumir el estado global de NumPy.
Los óptimos se obtienen de los metadatos de cada instancia, incluida su
dimensión. La tabla de referencias exclusivas de informes antiguos se retiró
junto con sus consumidores; no es un segundo catálogo de óptimos v2.
Las suites CEC suministradas por OPFUNU se integran mediante
`benchmarks/opfunu_cec.py` como familia separada `OPFUNU_CEC`; el año, la
función, la clase y la versión del paquete forman parte de su identidad
persistida. No se consideran intercambiables con la implementación CEC2017
autocontenida.
SCP y USCP se conservan como
[fuentes pasivas e instancias archivadas](../../../ARCHIVE/problems/set_cover/README.md),
con integridad verificada contra Review. `Problem/` y sus consumidores
históricos ya se retiraron, sin imports desde ARCHIVE. KP sigue
como ampliación futura, no como una implementación local existente.
No son problemas operativos de la API v2: su migración está
pausada por decisión metodológica desde 2026-10-26. La siguiente ampliación se
evaluará primero entre problemas de ingeniería o benchmarks continuos,
evitando introducir por ahora binarización, transferencia y reparación en el
núcleo v2.
