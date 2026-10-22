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

Estado: destinos definidos; implementaciones aún en `Metaheuristics/`.

Especificación: `documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md`.
