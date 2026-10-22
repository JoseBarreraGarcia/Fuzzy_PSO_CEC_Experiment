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

## Bloques configurables

| Bloque | Qué controla | Opciones v1 |
|---|---|---|
| `campaign` | Identidad, réplicas y métricas | `replicas >= 1`; perfiles `minimal`, `convergence`, `optimizer`, `fuzzy`, `all`, lista u objeto selectivo |
| `randomness` | Pareamiento y reproducibilidad | `paired_by_replica_v1`, semilla base no negativa, `numpy_seedsequence_pcg64_v1` |
| `problems` | Matriz de problemas | `CEC2017`; F1 y F3-F30; dimensiones 10, 30, 50, 100 |
| `treatments` | Configuraciones del optimizador | `PSO`; políticas `fixed_inertia` y `legacy_ldiw` |
| `execution` | Recursos de ejecución | `parallel_workers=1`; otros valores se rechazan hasta validar el piloto paralelo |

Los parámetros PSO obligatorios son `population_size` y `max_iterations`. Los
opcionales y sus valores efectivos por defecto son `cognitive=2.0`,
`social=2.0` y `velocity_factor=0.1`. `fixed_inertia` requiere `value`;
`legacy_ldiw` acepta `maximum=0.9` y `minimum=0.1`.

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

`run` ejecuta únicamente filas `planned`, por lo que puede retomarse después de
una detención entre réplicas. Una fila que haya quedado en estado `running`
requiere una decisión explícita de recuperación y nunca se reinicia sola.
