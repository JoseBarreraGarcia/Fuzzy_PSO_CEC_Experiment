# Configuración

## Contrato activo v2

- [campaigns/](campaigns/README.md): ejemplos PSO, PSO-FCS y GA real-coded,
  además de una validación técnica acotada. Son declaraciones de capacidades,
  no protocolos científicos aprobados automáticamente.
- [schemas/campaign_v1.schema.json](schemas/campaign_v1.schema.json): contrato
  para el editor; el lector `afcs.experiments.load_campaign_config` valida y
  resuelve la campaña antes de planificarla.
- [Contrato de semillas](../documentation/architecture/REPRODUCIBLE_SEEDS.md):
  documentación de arquitectura, trasladada fuera de esta carpeta.

La previsualización no ejecuta experimentos ni crea una base:

```powershell
afcs-campaign preview `
  --config config\campaigns\cec2017_pso_v2.example.json `
  --code-commit <commit-git>
```

Los formatos antiguos no se reinterpretan como campañas v2.

## Configuración histórica retirada

`experiments.json` y `directories.json` se retiraron al cerrar `Util/`,
después del runner, poblador y analizadores antiguos. No tenían consumidores
restantes fuera de ese grupo. El primero coincide con Review; la versión
modificada del segundo se preservó allí como
`config/directories_v2_snapshot_20261109.json`, sin sobrescribir el original.
No se convierten en plantillas v2 ni se duplican en ARCHIVE. Las APIs v2
reciben rutas explícitas y declaraciones de campaña validadas.
Las fuentes discretas e instancias están en
[ARCHIVE](../ARCHIVE/problems/set_cover/README.md), sin redirigir lectores
antiguos al archivo. Las bases históricas están preservadas en Review,
no disponibles para ejecutar el pipeline antiguo aquí.

Se retiraron `analysis.json`, cuyo orquestador ya no existe, y
`experiments_cec2017.json`, un ejemplo del formato antiguo sin consumidores
fijos. Ambos originales se verificaron idénticos en Review; no se duplican en
ARCHIVE. Los futuros usos de CEC2017 se declaran con el esquema de campañas
v2, sin convertir silenciosamente presupuestos ni semillas históricos.

También se retiró `fuzzy_plots.json` con sus cuatro generadores/launchers:
las copias originales coinciden con Review. El diagnóstico activo es
[`write_fuzzy_diagnostics`](../src/afcs/analysis/fuzzy.py), que recibe un
`MamdaniController` v2 y una ruta explícita; no carga ese JSON ni los antiguos
sets I1/O1. Su uso y sus límites se describen en
[afcs.analysis](../src/afcs/analysis/README.md).

`fuzzy_partitions.json` se retiró con los tres controladores históricos y
el wrapper PSO-FCS, tras verificar sus respaldos en Review. La política
[`FuzzyInertiaPolicy`](../src/afcs/optimizers/pso/policies.py) utiliza el
controlador canónico; no interpreta particiones I1/O1 del formato retirado.
