# Ejecución secuencial de campañas v2

## Flujo implementado

`SequentialCampaignOrchestrator` conecta las piezas ya validadas:

```text
preview (sin escritura)
        ↓
CampaignPlanner → SQLite: draft + runs planned
        ↓
start_campaign
        ↓
PlannedRun → OptimizerFactory → ExperimentRunExecutor
        ↓
completed o failed por réplica → campaña completed
```

La fábrica reconstruye cada ejecución desde SQLite, no desde estado transitorio
del proceso. En la primera versión soporta CEC2017, PSO
`2.0.0a0-legacy-compatible`, `fixed_inertia`, `legacy_ldiw` y
`fuzzy_inertia_mamdani`. La versión del
optimizador queda normalizada en `algorithm_configurations` mediante la migración
003 y se comprueba antes de ejecutar.

## Reanudación

Volver a ejecutar `afcs-campaign run` procesa solamente filas `planned`. Las
filas `completed`, `failed` o `cancelled` no se repiten. Esto permite retomar una
campaña detenida entre réplicas y preserva los resultados ya registrados.

Una interrupción abrupta dentro de una réplica puede dejarla en `running`. El
orquestador informa `CampaignRecoveryRequired` y no cambia ese estado por sí
solo. La recuperación aprobada debe invocarse explícitamente:

```powershell
afcs-campaign recover `
  --database Resultados/campaign.db `
  --campaign-id campaign-id `
  --run-id 17 `
  --reason "worker interrumpido por reinicio del sistema"
```

La operación marca el intento activo como `abandoned`, registra fechas, motivo
y cantidad de datos parciales descartados, limpia las trazas canónicas
incompletas y devuelve la misma réplica lógica a `planned`. El reintento conserva
configuración, `replica_index`, semilla y presupuesto, y genera un nuevo intento
numerado. No se recuperan automáticamente filas por antigüedad ni se reintentan
fallos terminales.

## Límites deliberados de esta etapa

- Sólo se ejecuta `parallel_workers=1`; otros valores se rechazan tanto en el
  esquema como en el lector.
- La ejecución se detiene ante el primer error, después de registrar la réplica
  como `failed`. Una invocación posterior continúa con las demás pendientes.
- Las trazas PSO, las métricas poblacionales y los diagnósticos internos del
  controlador difuso se persisten según el perfil seleccionado.
- La validación técnica acotada del controlador se mantiene separada del piloto
  y de la campaña confirmatoria.
- La validación técnica de equivalencia secuencial/paralela continúa pendiente;
  no requiere ni autoriza una campaña científica.

Estas restricciones evitan anunciar capacidades que todavía no han sido
verificadas experimentalmente.
