# Metrics

Indicadores calculados durante o después de la búsqueda. Subfamilias previstas:

- objetivo y convergencia;
- diversidad global y por dimensión;
- mejora, estancamiento y velocidad de convergencia;
- exploración y explotación;
- población y entropía;
- restricciones y reparación;
- dinámica difusa y switching;
- coste computacional y estabilidad.

Cada métrica debe declarar fórmula/versión, dependencias, ámbito, unidad,
normalización, fase de muestreo, coste y banderas de validez. Las fórmulas
abiertas en la tesis no se asumirán como definitivas.

Estado: registro versionado de 36 métricas migrado a este módulo:

- `definitions.json`: catálogo versionado y perfiles;
- `registry.py`: carga, validación y resolución de selecciones;
- `tracing.py`: muestreo tipado y métricas poblacionales PSO versionadas;
- `__init__.py`: API pública estable.

Las fórmulas `hussain_diversity_v1`, `population_entropy_v1` y
`diversity_per_dimension_v1` tienen pruebas de equivalencia con las
implementaciones heredadas. El perfil `optimizer` registra además el peso de
inercia efectivamente aplicado. El checkpoint inicial no contiene `w` porque
todavía no se ha realizado una transición.

El perfil `fuzzy` añade entradas, membresías, reglas, salida, casos borde,
tiempos y resúmenes del controlador. La extensión de observaciones equivalentes
a GA y otras metaheurísticas permanece pendiente.

El catálogo se incluye en el paquete instalable. `Util/metrics_registry.py`
es únicamente un puente temporal para consumidores externos heredados.
