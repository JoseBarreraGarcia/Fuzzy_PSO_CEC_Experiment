# Optimizers

Metaheurísticas independientes del problema, persistencia y control externo.
Cada optimizador puede ejecutarse sin política de adaptación y declara su
configuración inicial, estado observable y parámetros potencialmente
adaptables.

El primer contrato se validará con PSO continuo y distinguirá:

- núcleo PSO compartido;
- políticas de inercia para comparaciones controladas;
- variantes completas como APSO, que modifican otros operadores.

GA será la segunda integración. Las demás implementaciones se conservarán como
experimentales y podrán ejecutarse inicialmente sin control mediante
adaptadores.

Estado: PSO v2 es la implementación continua de referencia, con ciclo completo,
presupuesto NFE, semillas, trazas y persistencia integrados. Los wrappers
históricos permanecen temporalmente en `Metaheuristics/` para regresión. GA es
la siguiente integración y todavía no se declara operativo en v2.

Especificación: `documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md`.
Auditoría legacy: `documentation/architecture/LEGACY_OPTIMIZER_AUDIT.md`.
