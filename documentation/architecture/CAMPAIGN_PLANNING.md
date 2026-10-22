# Planificación de campañas v2

## Responsabilidades

La planificación no sustituye `config/`. Separa cuatro etapas:

```text
config/*.json (declaración humana)
          ↓
lector y esquema validado (pendiente)
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

El planificador asigna índices de réplica consecutivos desde cero, pero persiste
`random_seed = NULL`. No interpreta los campos heredados `use_seed` o `seed`, no
genera semillas maestras y no deriva subflujos. El contrato descrito en
`config/PROPUESTA_IMPLEMENTACION_SEMILLAS.md` seguirá siendo un cambio separado.

## Trabajo pendiente

- Definir el esquema v2 legible por humanos para campañas, problemas,
  algoritmos, políticas, métricas y recursos de ejecución.
- Implementar el lector que traduzca ese esquema a las definiciones tipadas.
- Decidir la migración de los JSON heredados; no deben interpretarse
  silenciosamente con semántica nueva.
- Añadir la versión del optimizador como campo normalizado del esquema SQLite.
- Incorporar reanudación y ejecución completa de campañas después de aprobar el
  protocolo de semillas.
