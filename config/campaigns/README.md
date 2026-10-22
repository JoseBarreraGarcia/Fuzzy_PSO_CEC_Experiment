# Campañas v2

Esta carpeta contiene ejemplos de la futura configuración humana v2. El lector
JSON todavía no está implementado: estos archivos documentan el contrato y no
deben pasarse a los scripts heredados.

La sección `randomness` vigente usa:

- `paired_by_replica_v1`;
- `base_seed = 42`;
- `replicas = 31`, que produce semillas 42–72;
- la misma semilla para todos los tratamientos con igual `replica_index`;
- subflujos NumPy separados para inicialización, dinámica y controlador.

Cambiar `replicas` cambia únicamente la cantidad de semillas consecutivas. Por
ejemplo, 100 réplicas usarían 42–141.
