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

Estado: registro y catálogo inicial de 28 métricas migrados a este módulo:

- `definitions.json`: catálogo versionado y perfiles;
- `registry.py`: carga, validación y resolución de selecciones;
- `__init__.py`: API pública estable.

El catálogo se incluye en el paquete instalable. `Util/metrics_registry.py`
es únicamente un puente temporal para consumidores externos heredados.
