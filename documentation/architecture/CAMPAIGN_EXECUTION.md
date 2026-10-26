# Ejecución secuencial de campañas v2

## Flujo implementado

`CampaignOrchestrator` conecta las piezas ya validadas. El nombre histórico
`SequentialCampaignOrchestrator` se conserva temporalmente como alias compatible:

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

## Cancelación y sellado

Una exclusión intencional no se registra como fallo. El operador puede cancelar
réplicas `planned` o `running`, siempre con un motivo explícito:

```powershell
afcs-campaign cancel `
  --database Resultados/campaign.db `
  --campaign-id campaign-id `
  --run-id 17 18 `
  --reason "tratamientos retirados del alcance aprobado"
```

La cancelación de una réplica activa cierra el intento como `cancelled`, guarda
el motivo y el número de observaciones parciales descartadas, y limpia las
trazas canónicas. Una réplica cancelada no se reintenta automáticamente. La
campaña sí puede finalizar operativamente cuando todas sus réplicas son
terminales.

El sellado científico exige que no existan fallos ni cancelaciones. Una campaña
incompleta sólo puede sellarse mediante una excepción explícita y auditada:

```powershell
afcs-campaign seal `
  --database Resultados/campaign.db `
  --campaign-id campaign-id `
  --waiver-reason "uso limitado a validación de infraestructura"
```

La excepción conserva el motivo, fecha y conteos de estados terminales en el
momento del sellado. La auditoría informa cancelaciones y fallos como
advertencias, y considera error de integridad un sellado incompleto sin esa
excepción.

## Auditoría de integridad

Una campaña puede inspeccionarse sin alterar sus resultados:

```powershell
afcs-campaign audit `
  --database Resultados/campaign.db `
  --campaign-id campaign-id
```

El comando verifica `integrity_check`, claves foráneas, coherencia entre
campaña/réplicas/intentos, secuencia de intentos y checkpoints, presupuesto NFE,
NFE final de la traza, finitud del resultado y dimensión de la solución. Devuelve
código 0 si no encuentra problemas de integridad y 2 cuando informa
inconsistencias. Las advertencias operativas no cambian por sí solas el código.

El runner y el repositorio también impiden preventivamente completar una réplica
si el NFE observado no coincide exactamente con el presupuesto persistido. Los
objetivos, soluciones y métricas no finitos se rechazan y la ejecución queda
registrada como `failed`.

## Paralelismo reproducible

`execution.parallel_workers=1` mantiene la ejecución secuencial. Un valor mayor
distribuye réplicas completas mediante procesos; nunca paraleliza operaciones
dentro de una réplica. Cada trabajador abre una conexión propia a la base WAL,
lee el plan persistido y crea localmente el problema, el optimizador y sus
subflujos RNG.

La identidad aleatoria depende de la semilla de réplica, no del trabajador, del
orden de envío ni del orden de finalización. La prueba de equivalencia compara
objetivo, solución, NFE y hashes de condiciones iniciales entre ejecuciones con
uno y dos trabajadores. Se excluyen deliberadamente los tiempos de reloj porque
la contención y planificación del sistema operativo los hacen no deterministas.

## Límites deliberados de esta etapa

- El paralelismo está disponible sólo para bases SQLite respaldadas por archivo;
  las bases `:memory:` se rechazan porque no pueden compartirse entre procesos.
- La ejecución se detiene ante el primer error, después de registrar la réplica
  como `failed`. Una invocación posterior continúa con las demás pendientes.
- Las trazas PSO, las métricas poblacionales y los diagnósticos internos del
  controlador difuso se persisten según el perfil seleccionado.
- La validación técnica acotada del controlador se mantiene separada del piloto
  y de la campaña confirmatoria.
- La equivalencia secuencial/paralela está cubierta por una prueba técnica
  acotada; esto no sustituye pruebas de rendimiento ni autoriza una campaña
  científica.

Estas restricciones evitan anunciar capacidades que todavía no han sido
verificadas experimentalmente.
