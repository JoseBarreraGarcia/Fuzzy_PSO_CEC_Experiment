# Solver CEC Fuzzy PSO — plataforma experimental v2

Este repositorio está evolucionando hacia una plataforma reproducible para
investigar control difuso adaptativo de metaheurísticas. El desarrollo inicial
se concentra en PSO/PSO-FCS y GA real-coded sobre benchmarks continuos.
Otros optimizadores y problemas discretos como SCP, USCP y Knapsack requieren
una ampliación explícita del alcance.

> **Estado:** transición avanzada a v2. CEC2017, PSO, control difuso, semillas,
> GA real-coded, campañas secuenciales y paralelas, métricas y persistencia
> SQLite ya operan en el paquete nuevo y cuentan con pruebas. Todavía no es una
> versión de producción: quedan calidad, CI y autorización de distribución.
> R3 verificó wheel/sdist e instalación limpia local (Windows, Python 3.14.4);
> no certifica otros entornos ni publicación. Recuperación, paralelismo y análisis canónico ya
> tienen validación técnica; no equivale a rendimiento publicable ni autoriza
> campañas científicas. SCP/USCP/KP y selección dinámica siguen fuera del
> alcance operativo actual.

## Preservación del artículo MDPI

El estado utilizado para los experimentos y resultados históricos se conserva
sin reinterpretarlo en:

- rama: `Solver_CEC_Fuzzy_PSO_ARTICULO_MDPI`;
- commit congelado: `f8649134362f9a7b5e04f2f2bf032eb4b5938172`.

La rama `Solver_CEC_Fuzzy_PSO_v2` contiene la reorganización y las mejoras para
nueva experimentación. Los resultados obtenidos con v2 no deben atribuirse
retroactivamente al artículo.

## Orientación rápida

| Necesidad | Ubicación |
|---|---|
| índice de documentación v2 | [`documentation/1_Index.md`](documentation/1_Index.md) |
| visión científica y alcance de la tesis | [`documentation/PROJECT_VISION.md`](documentation/PROJECT_VISION.md) |
| mapa de módulos y migración de rutas | [`documentation/architecture/MODULE_MAP.md`](documentation/architecture/MODULE_MAP.md) |
| optimizadores y control opcional de parámetros | [`documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md`](documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md) |
| GA continuo y referencias de sus operadores | [`documentation/architecture/REAL_CODED_GA.md`](documentation/architecture/REAL_CODED_GA.md) |
| plan general de migración | [`documentation/V2_MIGRATION_PLAN.md`](documentation/V2_MIGRATION_PLAN.md) |
| ruta para terminar la plataforma | [`documentation/V2_PLATFORM_COMPLETION_PLAN.md`](documentation/V2_PLATFORM_COMPLETION_PLAN.md) |
| decisiones de limpieza por archivo | [`documentation/V2_CLEANUP_MANIFEST.md`](documentation/V2_CLEANUP_MANIFEST.md) |
| contrato experimental y estadístico | [`documentation/lessons_learned/EXPERIMENT_DATA_AND_ANALYSIS.md`](documentation/lessons_learned/EXPERIMENT_DATA_AND_ANALYSIS.md) |
| diseño de SQLite v2 | [`documentation/architecture/SQLITE_V2_SCHEMA.md`](documentation/architecture/SQLITE_V2_SCHEMA.md) |
| configuración activa y decisiones sobre formatos retirados | [`config/README.md`](config/README.md) |
| contrato implementado de semillas | [`REPRODUCIBLE_SEEDS.md`](documentation/architecture/REPRODUCIBLE_SEEDS.md) |
| diagnóstico y uso de CEC2017 | [Estado operativo CEC2017](documentation/architecture/CEC2017_OPERATIONAL.md) |
| contexto doctoral incorporado | [`Tesis/CONTEXTO_TESIS_DOCTORAL_CODEX.md`](Tesis/CONTEXTO_TESIS_DOCTORAL_CODEX.md) |

La implementación activa vive bajo [`src/afcs/`](src/afcs/README.md);
sus README documentan responsabilidades, capacidades implementadas y límites.
Los árboles históricos de solvers, problemas, metaheurísticas, controladores,
base de datos y utilidades ya se retiraron. Las referencias seleccionadas
para capacidades futuras están en [`ARCHIVE/`](ARCHIVE/README.md), no en
rutas de compatibilidad. Tesis queda fuera de esta limpieza.

## Capacidades v2 ya preparadas

- registro validado y versionado de métricas, con perfiles y selección explícita;
- fixtures sintéticos para pruebas de análisis y persistencia;
- esquema SQLite v2 idempotente;
- repositorio transaccional para campañas, réplicas, trazas y métricas;
- regresiones y condiciones operativas documentadas para CEC2017;
- mapa de rescate del análisis estadístico reutilizable;
- estructura modular para lógica difusa, selectores, controladores,
  binarización, problemas, optimizadores y análisis.
- semillas pareadas por réplica, subflujos explícitos y hashes de condiciones
  iniciales;
- PSO v2 con políticas fija, lineal heredada y control Mamdani de `w`;
- GA real-coded v2 con SBX y mutación polinómica en benchmarks continuos;
- campañas configurables con `preview`, planificación, ejecución secuencial
  o paralela, recuperación explícita, cancelación, sellado y auditoría;
- trazas y diagnósticos internos del controlador difuso.

## Análisis y fuentes futuras

El análisis activo está en [`src/afcs/analysis/`](src/afcs/analysis/README.md):
`run_campaign_analysis` exporta y reconcilia datos, informe, tablas y figuras
desde una campaña v2 y un directorio de salida explícito.

Los paquetes raíz `analysis_modules` y `analysis_modules_cec` y los
orquestadores `3_0_analisis.py` y `3_3_analisisCEC.py` se retiraron; sus comandos,
flags y nombres de salida históricos ya no están soportados. No se migraron
sus reconstrucciones de métricas ni las conclusiones de campañas antiguas.
También se retiraron los analizadores BEN/SCP, los comandos de creación,
reinicio/población, el runner `2_main.py`, los solvers, BD y Util antiguos:
el punto de entrada operativo es `afcs-campaign`, no el pipeline numerado.
La discretización, SCP/USCP y sus instancias quedan como referencias pasivas
en ARCHIVE, fuera de v2 activo. La integridad de sus respaldos no certifica
óptimos ni derechos de redistribución pública de datasets.
Los gráficos especializados de dinámica del controlador siguen pendientes.
Sólo sus referencias útiles para capacidades futuras quedan organizadas en
[`ARCHIVE/`](ARCHIVE/README.md), como fuentes pasivas, no módulos ejecutables.

## Instalación y validación

Las dependencias se declaran únicamente en [`pyproject.toml`](pyproject.toml).
El snapshot histórico `requirements.txt` se retiró tras verificar su respaldo
en Review; sus versiones no son un lockfile ni requisitos de v2.
Se requiere Python 3.11 o posterior. El núcleo depende de NumPy; los extras
`analysis` y `opfunu` habilitan análisis/figuras y las suites externas OPFUNU,
respectivamente. La implementación CEC2017 autocontenida no necesita OPFUNU.

Desde PowerShell, para preparar un entorno nuevo con todas las capacidades
opcionales y ejecutar las pruebas:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[analysis,opfunu]"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Si `.venv` ya existe, reutilícelo y omita su creación. No ejecute estos pasos
para actualizar dependencias de un entorno validado sin revisar los cambios.
Para instalar sólo el núcleo, use `pip install -e .` con el intérprete elegido.
Estos rangos de dependencias no garantizan compatibilidad con todas las
versiones futuras de Python o bibliotecas. R3 verificó instalaciones no editables
desde wheel y sdist fuera del repositorio en Windows/Python 3.14.4; CI y la matriz
de soporte siguen pendientes de R4. El extra `opfunu` declara
`setuptools>=68,<82`: OPFUNU 1.0.1 importa `pkg_resources`, retirado en
setuptools 82. Esto no añade setuptools al núcleo NumPy ni elimina el aviso de
obsolescencia de OPFUNU.

El sdist incluye código, pruebas con fixtures y configuración; el wheel incluye
sólo el paquete y sus recursos de ejecución. No son un respaldo del repositorio:
documentación completa, Tesis, ARCHIVE, bases, resultados y entornos no se
distribuyen. Los verificadores reproducibles son
[`distribution_contents.py`](tests/distribution_contents.py) y
[`distribution_smoke.py`](tests/distribution_smoke.py); comandos, hashes y límites
están registrados en [el cierre R3](documentation/V2_PLATFORM_COMPLETION_PLAN.md#r3--probar-lo-que-realmente-se-distribuirá).

### Calidad y CI (R4)

El extra `dev` declara versiones exactas de Ruff, Pyright y el frontend de build.
Instale `.[dev,analysis,opfunu]` en un entorno de desarrollo separado si no desea
modificar un entorno experimental ya validado. Desde la raíz:

```powershell
python -m ruff check src\afcs tests
python -m ruff format --check src\afcs tests
python -m pyright --pythonpath (python -c "import sys; print(sys.executable)")
python -m unittest discover -s tests -q
```

Ruff comprueba errores Python/Pyflakes y orden de imports, con formato de 88
columnas y sintaxis objetivo 3.11. Pyright usa `standard` sobre todo
`src/afcs`; las pruebas tienen lint/formato y validación ejecutable, no se
presentan como cubiertas por el gate de tipos. No hay silenciamientos globales
de diagnósticos. Para aplicar el formato use `python -m ruff format src\afcs tests`.
Las pruebas requieren una instalación de AFCS: no insertan `src` en `sys.path`.

El [workflow](.github/workflows/quality.yml) propone Python 3.11–3.14 (último
patch disponible) en Ubuntu 24.04 y Windows Server 2022. No es una declaración
de soporte verificado: la matriz remota debe ejecutarse y pasar antes de cerrar
R4. No incluye macOS, intérpretes alternativos, Python 3.15 ni 32 bits.

[`distribution_ci.py`](tests/distribution_ci.py) ejecuta los mismos controles
de artefactos en cada celda: build aislado, instalación no editable del wheel
con núcleo y del sdist con extras, smokes aislados con uno/dos trabajadores,
`pip check` y suite completa desde el sdist, usando el paquete instalado.
Puede ejecutarse localmente con el extra `dev` instalado:

```powershell
python tests\distribution_ci.py --output (Join-Path $env:TEMP "afcs-ci-local")
```

El directorio de salida debe estar fuera del checkout y reservado para esta
validación. Los entornos y bases temporales se eliminan al terminar; los
artefactos se conservan allí para inspección, sin publicarlos. Las salidas
técnicas de CI no autorizan campañas científicas ni publicación.

Antes de planificar o ejecutar una campaña, revise su tamaño sin crear bases:

```powershell
.\.venv\Scripts\afcs-campaign.exe preview `
  --config config\campaigns\cec2017_pso_v2.example.json `
  --code-commit <commit-git>
```

La [guía de campañas](config/campaigns/README.md) describe planificación,
ejecución y auditoría. Los ejemplos no aprueban automáticamente un protocolo
científico.

La arquitectura ya permite validaciones técnicas pequeñas, pero las campañas
científicas no deben iniciarse hasta terminar la plataforma y congelar el
protocolo metodológico correspondiente. La validación técnica actual no es
evidencia para artículos.

## Regla de evolución

Cada capacidad tendrá una sola implementación autoritativa. El proceso será:
crear contrato y pruebas, migrar una responsabilidad, actualizar consumidores y
documentación, verificar equivalencia y sólo entonces retirar el código
duplicado. Las decisiones que cambien fórmulas, hipótesis, unidad experimental o
metodología se someterán a aprobación antes de implementarse.
