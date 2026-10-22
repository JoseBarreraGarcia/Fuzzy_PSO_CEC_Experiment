# Planificación de campañas v2

## Responsabilidades

La planificación no sustituye `config/`. Separa cuatro etapas:

```text
config/campaigns/*.json (declaración humana)
          ↓
load_campaign_config + campaign_v1.schema.json
          ↓
CampaignDefinition + TreatmentDefinition
          ↓
CampaignPlanner
          ↓
SQLite v2 (plan canónico expandido)
```

`CampaignDefinition` conserva identidad, nombre, commit, selección de métricas,
número de réplicas y una copia de la configuración fuente. Cada
`TreatmentDefinition` une una configuración algorítmica canónica con una
instancia de problema.

`CampaignPlanner` valida toda la matriz antes de escribir y después crea, en una
sola transacción:

- la campaña y la selección congelada de métricas;
- las instancias de problema sin duplicados;
- las configuraciones algorítmicas sin duplicados;
- una fila por tratamiento y `replica_index`.

Si una misma `configuration_id` describe parámetros, versión, población o
presupuestos diferentes, la campaña se rechaza antes de tocar SQLite. Un error
posterior también revierte la transacción completa, evitando campañas parciales.

## Semillas

El planificador asigna índices consecutivos desde cero y calcula
`random_seed = base_seed + replica_index`. Con la configuración inicial aprobada
de 31 réplicas y `base_seed=42`, cada tratamiento recibe 42–72. El protocolo
`paired_by_replica_v1` y el motor `numpy_seedsequence_pcg64_v1` quedan
persistidos en la campaña. Los JSON heredados aún no se reinterpretan.

## Configuración validada

El contrato v1 está definido en `config/schemas/campaign_v1.schema.json` y su
plantilla ejecutable en `config/campaigns/cec2017_pso_v2.example.json`. El
lector rechaza claves desconocidas, valida las opciones contra los catálogos
vigentes y genera una configuración resuelta con todos los valores por defecto.
Esa versión resuelta, no la plantilla con valores implícitos, es la que se
entrega a `CampaignDefinition.source_config` para persistirla.

Actualmente el catálogo ejecutable incluye CEC2017, PSO, `fixed_inertia` y
`legacy_ldiw`. La ampliación a otros problemas, optimizadores y controladores
debe incorporar conjuntamente implementación, esquema, documentación y pruebas.

## Trabajo pendiente

- Decidir la migración de los JSON heredados; no deben interpretarse
  silenciosamente con semántica nueva.
- Añadir la versión del optimizador como campo normalizado del esquema SQLite.
- Incorporar reanudación y ejecución completa de campañas y validar el piloto
  secuencial/paralelo.
