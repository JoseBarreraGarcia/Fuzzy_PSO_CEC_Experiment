# Contrato de configuración de campañas v2

## Propósito

La configuración v2 separa lo que el investigador declara de lo que finalmente
se persiste. El JSON conserva una interfaz legible; el lector lo valida y
produce objetos tipados más una copia resuelta con los valores por defecto
explícitos. Ningún campo desconocido se ignora silenciosamente.

```text
JSON humano + JSON Schema
          ↓ validación estricta
LoadedCampaignConfig
          ├─ CampaignDefinition
          ├─ TreatmentDefinition[]
          ├─ ExecutionConfig
          ├─ CampaignSummary
          └─ resolved_config → SQLite
```

## Fuentes de verdad

- `config/schemas/campaign_v1.schema.json`: forma, tipos, opciones y ayuda para
  editores.
- `src/afcs/experiments/configuration.py`: validación ejecutable y traducción a
  contratos internos.
- `src/afcs/metrics/definitions.json`: IDs y perfiles de métricas.
- `config/campaigns/cec2017_pso_v2.example.json`: plantilla de partida.
- `config/campaigns/cec2017_pso_fcs_overlap.example.json`: integración mínima
  del controlador difuso aprobada para pruebas, no campaña exhaustiva.

El esquema facilita la edición, pero el lector Python sigue siendo la barrera
obligatoria antes de planificar o persistir una campaña. Ambos contratos deben
actualizarse juntos.

El bloque `trace` separa la selección de métricas de su frecuencia de muestreo.
La selección responde qué variables se registran; `every_iterations` responde
cada cuánto se crea un checkpoint. El punto final es obligatorio cuando la
traza está activa.

## Expansión de la matriz

Cada combinación función-dimensión crea una instancia de problema. Cada
entrada de `treatments` crea una configuración algorítmica y se cruza con todas
las instancias. Finalmente se crean las réplicas:

```text
total_runs = problem_instances × algorithm_configurations × replicas
```

`CampaignSummary` permite revisar estos números y el intervalo de semillas
antes de escribir en la base de datos. Para la plantilla actual el resumen es
2 instancias, 2 configuraciones, 31 réplicas, 124 ejecuciones, 1.242.480
evaluaciones y semillas 42-72.

La interfaz `afcs-campaign preview` presenta este resumen sin tocar SQLite.
`plan` persiste la expansión y `run` ejecuta exclusivamente las filas pendientes.

## Reglas de extensión

Agregar una opción no consiste sólo en aceptar otro texto en el JSON. Cada
nueva familia, metaheurística o política debe aportar:

1. contrato e implementación tipada;
2. entrada en el lector y en el JSON Schema;
3. serialización completa en `resolved_config`;
4. prueba positiva, pruebas de rechazo y documentación;
5. revisión metodológica cuando altere la comparabilidad experimental.

Los JSON heredados de `config/` permanecen congelados y no se reinterpretan
automáticamente con esta semántica.

## Política difusa PSO-FCS

`fuzzy_inertia_mamdani` materializa en la configuración resuelta todas las
decisiones que afectan la inferencia: límites de `w`, granularidad, R1-R8,
familia de membresía, definición y acoplamiento de overlap, frontera en cero,
Hussain v1, máximo histórico, `iter/maxIter`, Mamdani min-max y centroide.

El modo compartido es el aprobado para el factorial 0/50/100. El esquema admite
un modo independiente para diversidad/progreso/salida sin convertirlo en valor
predeterminado ni incorporarlo silenciosamente al estudio. Véase
[FUZZY_CONTROLLER_METHODOLOGY.md](FUZZY_CONTROLLER_METHODOLOGY.md).
