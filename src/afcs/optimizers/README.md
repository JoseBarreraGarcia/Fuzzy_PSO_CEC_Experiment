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

Estado: contratos, política legacy_ldiw y transición numérica PSO extraídos.
Los wrappers operativos y el ciclo completo permanecen temporalmente en
`Metaheuristics/` y `Solver/`.

Especificación: `documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md`.
Auditoría legacy: `documentation/architecture/LEGACY_OPTIMIZER_AUDIT.md`.
