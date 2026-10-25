# Esquema SQLite v2

**Estado:** infraestructura preparada y probada; conectada al runner secuencial
de campañas v2 y al optimizador PSO. Otros solvers heredados siguen pendientes.

## Propósito

El esquema v2 convierte la base SQLite en la fuente autoritativa de una
campaña. Se implementa en paralelo a `BD/sqlite.py`: no abre, modifica ni migra
automáticamente bases históricas.

Archivos:

- `src/afcs/persistence/migrations/001_initial_schema.sql`;
- `src/afcs/persistence/database.py`;
- `src/afcs/persistence/repository.py`;
- `tests/test_persistence_v2.py`.
- `tests/test_repository_v2.py`.

Las rutas `BD/persistence_v2.py` y `BD/repository_v2.py` permanecen sólo
como puentes de importación durante la transición.

`src/afcs/experiments/runner.py` conecta una réplica planificada con cualquier
optimizador que implemente `RunnableOptimizer`. Actualmente persiste resultados,
hashes de condiciones iniciales, trazas seleccionadas, métricas de réplica y
fallos estructurados.

Antes de iniciar, el ejecutor compara el plan normalizado de SQLite con
`OptimizerRunMetadata`: algoritmo, problema, dimensión, dirección, óptimo,
parámetros, hash de datos, población y presupuestos. Una discrepancia detiene la
ejecución y conserva la réplica como `planned`. La migración 003 añadió la
versión del optimizador y el runner también la contrasta.

`CampaignPlanner` persiste de forma atómica campañas ya validadas, elimina
duplicados de instancias/configuraciones y expande tratamientos por índice de
réplica. Asigna semillas pareadas mediante `base_seed + replica_index`. El
lector estricto y el JSON Schema de campañas están implementados en
`afcs.experiments.configuration` y `config/schemas/`.

## Modelo

```text
campaigns
├── algorithm_configurations
├── campaign_metrics ── metric_definitions
└── runs
    ├── run_attempts
    ├── problem_instances
    ├── run_metric_values ── metric_definitions
    └── trace_points
        └── trace_metric_values ── metric_definitions
```

### `run_attempts`

Separa la réplica científica de sus intentos operativos. Cada transición
`planned → running` crea un `attempt_index` nuevo. Los intentos pueden terminar
como `completed`, `failed`, `cancelled` o `abandoned`; un índice único parcial
impide más de un intento `running` por réplica.

La recuperación explícita conserva el intento abandonado y sus metadatos, pero
retira de las tablas canónicas cualquier traza parcial antes de reencolar la
misma fila de `runs`. Así no se duplican unidades experimentales ni se mezclan
trayectorias de procesos diferentes.

### `campaigns`

Conserva la configuración resuelta, su SHA-256, commit del código, versiones de
esquema y registro de métricas, estado y fechas del ciclo de vida. Una campaña
sellada debe tener `sealed_at`.

### `algorithm_configurations`

Registra el algoritmo, parámetros canónicos y presupuesto. Una configuración
pertenece a una sola campaña. La clave foránea compuesta impide que una corrida
de otra campaña la reutilice accidentalmente.

### `problem_instances`

Describe familia, nombre, dimensión, sentido de optimización, óptimo conocido,
parámetros y hash opcional del dato funcional.

### `runs`

Una fila representa una réplica. La combinación campaña, configuración,
instancia y `replica_index` es única. En campañas `paired_by_replica_v1`, un
trigger exige `random_seed = base_seed + replica_index`. Las campañas anteriores
pueden conservar `NULL` y no se reinterpretan como pareadas.

La migración 002 añade además protocolo, motor RNG y hashes SHA-256 de población
y velocidades iniciales. Los hashes permiten auditar condiciones comunes sin
almacenar matrices completas.

### Métricas

`metric_definitions` guarda snapshots canónicos e inmutables del catálogo. Si
cambia una fórmula o semántica debe aumentar su versión.

`campaign_metrics` congela las métricas seleccionadas para una campaña. La API
de preparación sólo permite cambiar esa selección mientras el estado sea
`draft`.

`run_metric_values` conserva métricas escalares/finales y
`trace_metric_values` conserva métricas asociadas a puntos de control. Cada
valor utiliza exactamente una representación tipada: real, entero, texto o
JSON.

Toda métrica almacenada declara su procedencia:

- `observed`: capturada durante la ejecución;
- `reconstructed`: calculada posteriormente a partir de otros datos;
- `expected`: respuesta teórica o esperada del componente.

Esta distinción evita presentar reconstrucciones de diversidad o del
controlador como observaciones originales.

## Migraciones

`apply_migrations` descubre archivos con nombres `NNN_nombre.sql`, exige
versiones consecutivas y registra cada aplicación en `schema_migrations`. Una
segunda ejecución es idempotente.

Las conexiones habilitan claves foráneas y modo WAL. Las pruebas usan bases
temporales y comprueban `integrity_check` sin crear una base versionada en el
repositorio.

## Decisiones todavía no implementadas

- API de planificación y ejecución completa de campañas;
- prueba real de invariancia ante ejecución paralela;
- frecuencia predeterminada de trazas;
- fórmula v2 definitiva de error, GAP y RDP;
- forma de agregación de violaciones por familia de problemas;
- sellado criptográfico externo de una campaña finalizada;
- importación explícita de bases históricas.

Ninguno de estos puntos se resolverá implícitamente en una migración.

## API transaccional preparada

`ExperimentRepository` implementa el ciclo de vida sin conectarlo todavía al
runner heredado:

1. crear campaña y congelar su configuración canónica;
2. registrar instancias y configuraciones;
3. planificar réplicas y persistir su semilla pareada;
4. iniciar campaña y réplica;
5. registrar puntos de control y métricas seleccionadas;
6. completar o marcar como fallida cada réplica;
7. finalizar y sellar la campaña.

La API rechaza transiciones inválidas, métricas no seleccionadas, ámbitos
incorrectos, valores no finitos o incompatibles con el tipo registrado y
presupuestos de traza no monotónicos. Las escrituras compuestas son
transaccionales para no dejar puntos de control parciales.
