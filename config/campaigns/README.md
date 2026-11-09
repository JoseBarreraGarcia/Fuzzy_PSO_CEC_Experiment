# Configuración de campañas v2

Los JSON de esta carpeta son declaraciones humanas validadas. El lector
`afcs.experiments.load_campaign_config` comprueba el contrato completo antes de
crear una campaña. Un campo desconocido se rechaza para evitar que un error de
escritura cambie silenciosamente la metodología.

El archivo `cec2017_pso_v2.example.json` es ejecutable y también funciona como
plantilla. Su propiedad `$schema` permite que editores compatibles ofrezcan
autocompletado, descripciones y validación usando
`config/schemas/campaign_v1.schema.json`. `_documentation` es exclusivamente
informativa y el lector la ignora.
El ejemplo [real_coded_ga_v2.example.json](real_coded_ga_v2.example.json)
ejecuta el GA real-coded de v2. Su identidad, operadores y fundamento
bibliográfico se describen en
[`REAL_CODED_GA.md`](../../documentation/architecture/REAL_CODED_GA.md).

## Bloques configurables

| Bloque | Qué controla | Opciones v1 |
|---|---|---|
| `campaign` | Identidad, réplicas y métricas | `replicas >= 1`; perfiles `minimal`, `convergence`, `optimizer`, `fuzzy`, `timing`, `all`, lista u objeto selectivo |
| `randomness` | Pareamiento y reproducibilidad | `paired_by_replica_v1`, semilla base no negativa, `numpy_seedsequence_pcg64_v1` |
| `problems` | Matriz de problemas | `CEC2017`: F1 y F3-F30 en 10/30/50/100; `CLASSICAL`: F1-F23; `OPFUNU_CEC`: exige `suite_year` y valida cada función/dimensión en OPFUNU |
| `treatments` | Configuraciones del optimizador | `PSO` y `GA` real-coded; GA usa `no_adaptation` en esta versión |
| `execution` | Recursos de ejecución | `parallel_workers >= 1`; 1 es secuencial y valores mayores usan procesos aislados |
| `trace` | Muestreo de la trayectoria | Activación, frecuencia, checkpoint inicial y checkpoint final obligatorio |

Los parámetros PSO obligatorios son `population_size` y `max_iterations`. Los
opcionales y sus valores efectivos por defecto son `cognitive=2.0`,
`social=2.0` y `velocity_factor=0.1`. `fixed_inertia` requiere `value`;
`legacy_ldiw` acepta `maximum=0.9` y `minimum=0.1`.

### Variantes recomendadas para campañas nuevas (R2-G)

La [plantilla técnica recomendada](classical_pso_recommended_v2.example.json)
declara explícitamente:

- `parameters.velocity_rule="domain_width_v1"`: límite por amplitud de cada
  dimensión, optimizador `2.0.0a1-domain-width`;
- `parameter_policy.id="linear_endpoints_v1"`: máximo en primer movimiento y
  mínimo en último si T>=2; T=1 usa máximo;
- FCS con `parameter_policy.parameters.diversity_metric="hussain_diversity_v2"`:
  no redondea diversidad internamente y declara `policy_version=2`.

Estas elecciones científicas están aprobadas como definiciones, no como
configuración de un artículo ni campañas autorizadas. Los ejemplos anteriores
conservan deliberadamente las variantes históricas. Omitir las nuevas opciones
equivale a `legacy_upper0_v1` y `hussain_diversity_v1`, respectivamente, para no
cambiar trayectorias sin consentimiento; los defaults se resuelven en preview.
El Vmax antiguo usa **el primer límite superior**, no la amplitud del dominio;
si es cero no hay movimiento y si produce un límite negativo se rechaza.
Elegir `domain_width_v1` evita esa dependencia de la ubicación del dominio.
No cambiar la regla entre comparadores que pretenden aislar sólo la inercia.

Los parámetros del GA real-coded son `population_size` y `max_iterations`.
SBX y mutación polinómica usan índices de distribución 20 por defecto; la
probabilidad de cruce por apareamiento es 0.9 y la probabilidad de mutación por
variable es `1/d` por defecto. El presupuesto exacto es
`population_size * (max_iterations + 1)`. La selección es por torneo y se
conserva un individuo élite. Estos valores son una configuración inicial, no
un protocolo científico confirmado. El GA binario heredado permanece intacto y
fuera de v2 mientras la fase discreta siga pausada.

Una suite distribuida por OPFUNU se declara sin codificar el año dentro del
nombre de la función:

```json
{
  "family": "OPFUNU_CEC",
  "suite_year": 2014,
  "functions": [1, 3],
  "dimensions": [10, 30]
}
```

La versión y clase concretas de OPFUNU quedan materializadas en la
configuración resuelta y en SQLite. `CEC2017` sigue siendo la implementación
autocontenida del repositorio y no es un alias de `OPFUNU_CEC`/2017.

PSO-FCS se declara con `fuzzy_inertia_mamdani`. El ejemplo específico está en
`cec2017_pso_fcs_overlap.example.json`. El modo `shared` aplica el mismo overlap
a diversidad, progreso y salida, como exige el factorial principal:

```json
{
  "id": "fuzzy_inertia_mamdani",
  "parameters": {
    "minimum": 0.1,
    "maximum": 0.9,
    "granularity": 3,
    "rule_base": "R1",
    "membership_family": "triangular_v1",
    "overlap": {"mode": "shared", "value": 0.0},
    "zero_overlap_boundary_policy": "nearest_center_tie_upper",
    "centroid_grid_points": 501
  }
}
```

El modo `independent` acepta campos `diversity`, `progress` y `output`, pero se
reserva para ablaciones. El factorial aprobado usa triangulares y niveles
0/0.5/1. `gaussian_v1` está disponible con la definición ±2σ, fuera del
factorial principal. La configuración resuelta añade automáticamente las
identidades versionadas de diversidad Hussain, normalización, progreso e
inferencia.

La configuración inicial de trazas es:

```json
{
  "enabled": true,
  "every_iterations": 1,
  "include_initial": true,
  "include_final": true
}
```

El checkpoint 0 se registra después de evaluar la población inicial y consume
`population_size` evaluaciones. `inertia_weight` no aparece en ese punto porque
todavía no se ha aplicado en ningún movimiento. En el checkpoint `t >= 1`, su
valor corresponde al utilizado para producir la población observada en `t`.
`every_iterations` puede reducir la frecuencia, pero el punto final se conserva.

La selección de métricas siempre incorpora las métricas obligatorias del
registro `src/afcs/metrics/definitions.json`. El objeto selectivo tiene esta
forma:

```json
{
  "profile": "optimizer",
  "include": ["inertia_weight"],
  "exclude": ["population_entropy"]
}
```

No se permite excluir métricas obligatorias. Los IDs disponibles y su origen,
unidad, rango y política de ausencia se encuentran en el registro citado.
`all` selecciona las métricas disponibles para cálculo v2, no los metadatos
históricos `legacy_gap_percent`/`legacy_rdp_percent`: solicitarlos explícitamente
es un error. Las métricas se registran según scope y aplicabilidad; inercia no
aplica a GA ni inferencia difusa a PSO fijo. El objetivo final observado sigue
siendo obligatorio aunque `trace.enabled=false`.

La selección de la campaña congela versiones y definiciones. Un registro
ejecutor incompatible bloquea la reanudación, no actualiza la evidencia ni
reinterpreta métricas antiguas. Los detalles están en
[instrumentación](../../documentation/architecture/METRIC_TRACING.md).

## Semillas y tamaño de la campaña

La réplica `i` usa `base_seed + i`. Esa misma semilla se comparte entre todas
las configuraciones para posibilitar análisis pareados. Con 31 réplicas y
`base_seed=42` se utilizan 42-72; con 100 se utilizarían 42-141.

El total de ejecuciones se calcula como:

```text
instancias de problema × configuraciones algorítmicas × réplicas
```

La plantilla actual declara 2 problemas, 2 configuraciones y 31 réplicas: 124
ejecuciones y 1.242.480 evaluaciones de función objetivo.

Para validar el sistema sin ejecutar un piloto se dispone de
`cec2017_pso_fcs_validation_smoke.json`: 42 corridas, 8.820 evaluaciones y
semillas 42-44. Cubre CEC2017 F1/F21, baseline fijo, overlap 0/50/100 % y los
modos denso/disperso. Sus resultados son diagnóstico técnico descartable y no
deben incorporarse a inferencia científica ni al artículo.

Las configuraciones de este directorio demuestran capacidades de la plataforma;
no fijan por sí mismas el diseño de futuros artículos. Presupuestos, funciones,
tratamientos, comparadores y análisis confirmatorios deberán aprobarse en una
etapa científica posterior.

## Flujo de uso seguro

La previsualización no crea ni modifica una base de datos:

```powershell
afcs-campaign preview `
  --config config/campaigns/cec2017_pso_v2.example.json `
  --code-commit <commit-git>
```

La planificación y la ejecución son acciones separadas deliberadamente. Esto
permite revisar el tamaño de la campaña antes de consumir recursos:

```powershell
afcs-campaign plan `
  --config config/campaigns/cec2017_pso_v2.example.json `
  --code-commit <commit-git> `
  --database Resultados/cec2017_v2.db

afcs-campaign run `
  --database Resultados/cec2017_v2.db `
  --campaign-id cec2017-pso-v2-example
```

`run` lee `execution.parallel_workers` desde la configuración resuelta y ya
persistida. Cada proceso abre su propia conexión SQLite y reconstruye el
optimizador desde la réplica almacenada; no comparte generadores aleatorios ni
estado mutable. Cambiar el número de trabajadores no cambia las semillas ni los
resultados científicos. Los tiempos de ejecución sí pueden variar y no forman
parte de la equivalencia numérica.

`run` ejecuta únicamente filas `planned`, por lo que puede retomarse después de
una detención entre réplicas. Una fila que haya quedado en estado `running`
requiere una decisión explícita de recuperación y nunca se reinicia sola. Use
`afcs-campaign recover --database <db> --campaign-id <id> --run-id <ids...>
--reason <motivo>`; después, `run` ejecutará nuevamente esas réplicas con la
misma configuración y semilla.

Una exclusión deliberada se registra con `afcs-campaign cancel --database <db>
--campaign-id <id> --run-id <ids...> --reason <motivo>`. Puede aplicarse a
réplicas planificadas o activas, no equivale a un fallo y no se reintenta.

Tras finalizar, `afcs-campaign seal` sólo acepta campañas completas. Si existen
fallos o cancelaciones, exige `--waiver-reason <justificación>` y persiste esa
excepción para auditoría; no debe usarse para ocultar datos ausentes.

Para comprobar una base después de ejecutarla:

```powershell
afcs-campaign audit `
  --database Resultados/cec2017_v2.db `
  --campaign-id cec2017-pso-v2-example
```

La auditoría no modifica resultados y devuelve un informe JSON con los códigos
de cualquier inconsistencia encontrada.
