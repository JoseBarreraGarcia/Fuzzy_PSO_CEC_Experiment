# Esquema SQLite v2

**Estado:** infraestructura preparada y probada; todavía no conectada al runner
ni a los solvers heredados.

## Propósito

El esquema v2 convierte la base SQLite en la fuente autoritativa de una
campaña. Se implementa en paralelo a `BD/sqlite.py`: no abre, modifica ni migra
automáticamente bases históricas.

Archivos:

- `BD/migrations/001_initial_schema.sql`;
- `BD/persistence_v2.py`;
- `tests/test_persistence_v2.py`.

## Modelo

```text
campaigns
├── algorithm_configurations
├── campaign_metrics ── metric_definitions
└── runs
    ├── problem_instances
    ├── run_metric_values ── metric_definitions
    └── trace_points
        └── trace_metric_values ── metric_definitions
```

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
instancia y `replica_index` es única. `random_seed` está reservada pero admite
`NULL`: el esquema no calcula ni asigna semillas antes de implementar el
contrato específico.

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

- derivación y persistencia definitiva de semillas;
- API transaccional completa para crear y ejecutar campañas;
- frecuencia predeterminada de trazas;
- fórmula v2 definitiva de error, GAP y RDP;
- forma de agregación de violaciones por familia de problemas;
- sellado criptográfico externo de una campaña finalizada;
- importación explícita de bases históricas.

Ninguno de estos puntos se resolverá implícitamente en una migración.
