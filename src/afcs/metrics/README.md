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

Estado: registro versionado de métricas migrado a este módulo:

- `definitions.json`: catálogo versionado y perfiles;
- `registry.py`: carga, validación y resolución de selecciones;
- `tracing.py`: muestreo tipado y métricas poblacionales PSO versionadas;
- `__init__.py`: API pública estable.

Las fórmulas `hussain_diversity_v1`, `population_entropy_v1` y
`diversity_per_dimension_v1` conservan valores de referencia capturados de
las implementaciones heredadas antes de retirarlas. Las pruebas no dependen
de `Diversity/` y cubren poblaciones constantes, un individuo y entradas
inválidas. `exploration_exploitation_v1` conserva los porcentajes y define
explícitamente el caso de diversidad máxima cero.

El catálogo mantiene `legacy_gap_percent` y `legacy_rdp_percent` sólo como
metadatos históricos: no hay calculador v2 ni migración de sus ceros ante
denominadores inválidos. Las fórmulas requieren una decisión metodológica,
no una restauración del código retirado.
Sus definiciones siguen consultables, pero `all` no las selecciona y una
selección explícita falla por ausencia de calculador v2.

El repositorio contrasta versión y definición completa con la selección
persistida antes de iniciar/escribir. Observaciones obligatorias ausentes y
versiones incompatibles bloquean cierre, auditoría, exportación y sellado,
según scope y aplicabilidad; no se convierten en valores observados.
PSO y GA emiten explícitamente el objetivo final incluso sin trazas.
Véase el [contrato de instrumentación](../../../documentation/architecture/METRIC_TRACING.md).

El perfil `optimizer` registra además el peso de
inercia efectivamente aplicado. El checkpoint inicial no contiene `w` porque
todavía no se ha realizado una transición.

El perfil `fuzzy` añade entradas, membresías, reglas, salida, casos borde,
tiempos y resúmenes del controlador. `GATraceCollector` ya registra las
observaciones comunes del GA real-coded; la extensión para las demás
metaheurísticas permanece pendiente.

El catálogo se incluye en el paquete instalable. Los consumidores deben importar
el registro desde `afcs.metrics`; el puente heredado se retiró al no tener
consumidores dentro del repositorio.
