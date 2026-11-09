# Optimizers

Metaheurísticas desacopladas de problemas concretos y persistencia, con
políticas externas inyectables. Cada optimizador puede ejecutarse sin
adaptación y declara su
configuración inicial, estado observable y parámetros potencialmente
adaptables.

El contrato operativo se valida con PSO continuo y GA real-coded, y distingue:

- núcleo PSO compartido;
- políticas de inercia para comparaciones controladas;
- variantes completas como APSO, que modifican otros operadores.

Las implementaciones legacy restantes se conservan como experimentales
archivadas. No se exponen por defecto en el catálogo v2 ni se consideran
soportadas hasta migrarlas y probarlas explícitamente.

Estado: PSO v2 y GA real-coded están registrados en `OptimizerFactory`, con
ciclo de ejecución, presupuesto NFE, semillas, trazas y persistencia. Los
wrappers históricos se retiraron; los algoritmos archivados no son parte del
catálogo operativo.

## Contratos de lanzamiento (R2-G)

- PSO `velocity_rule=domain_width_v1`: Vmax por dimensión = factor por amplitud
  del dominio; versión `2.0.0a1-domain-width`. Recomendado para nuevas campañas.
- `legacy_upper0_v1` conserva Vmax = factor por primer límite superior y
  versión `2.0.0a0-legacy-compatible`. Omitir la opción conserva esta variante,
  no actualiza fórmulas. Vmax cero puede inmovilizar; límites negativos se
  rechazan. No anunciarla como invariante a desplazamientos del dominio.
- `linear_endpoints_v1`: movimientos 1..T incluyen máximo/mínimo para T>=2;
  T=1 usa máximo. `legacy_ldiw` conserva su primer peso máximo-(rango/T).
- FCS con `diversity_metric=hussain_diversity_v2` usa precisión completa y
  `policy_version=2`. Omitir conserva v1 redondeada/version 1. No cambia t/T
  ni la normalización por máximo histórico. No se normalizan dimensiones
  silenciosamente.
- PSO y GA rechazan la primera evaluación con `feasible=False` o violación
  distinta de cero. No implementan dominancia por factibilidad, reparación ni
  penalización; un escalar penalizado externo no declara soporte de restricciones.
- Cada objeto ejecuta un solo intento. `rng=` sigue como API in-memory con
  generador compartido, sin semilla/motor de réplica declarados. Las campañas
  usan `ReplicaRandomStreams`; determinismo local no equivale a procedencia.

La [plantilla recomendada](../../../config/campaigns/classical_pso_recommended_v2.example.json)
declara las tres definiciones nuevas explícitamente, con mismo Vmax/NFE entre
comparadores. Es técnica, no autoriza ni prescribe una campaña científica.

Especificación: [control de parámetros](../../../documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md).
Auditoría: [optimizadores históricos](../../../documentation/architecture/LEGACY_OPTIMIZER_AUDIT.md).
