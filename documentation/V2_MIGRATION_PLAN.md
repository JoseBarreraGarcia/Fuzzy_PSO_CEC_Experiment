# Plan de migración a Solver CEC Fuzzy PSO v2

**Rama:** `Solver_CEC_Fuzzy_PSO_v2`  
**Punto de partida:** `f8649134362f9a7b5e04f2f2bf032eb4b5938172`  
**Fecha:** 19 de octubre de 2026  
**Estado:** limpieza inicial, CEC2017, contratos, métricas y persistencia
migrados; auditoría y separación de optimizadores/runner pendiente.

## 1. Propósito

La versión 2 debe convertir el repositorio usado para el artículo MDPI en una
base mantenible, reproducible y compartible para nuevas campañas
experimentales. La rama MDPI conserva el estado reportado y no debe
reescribirse. Esta rama v2 puede retirar material específico del artículo
porque siempre podrá recuperarse desde el commit de congelación.

## 2. Principios de la migración

1. No alterar resultados históricos ni atribuirles el nuevo contrato de
   reproducibilidad.
2. No eliminar archivos antes de clasificarlos y aprobar su destino.
3. Separar código operativo, configuración, resultados y documentación.
4. Mantener las pruebas verdes después de cada cambio estructural.
5. Realizar limpieza, semillas y refactorización en commits independientes.
6. Conservar las lecciones aprendidas en documentos breves para agentes y
   colaboradores.
7. Los artefactos regenerables no deben almacenarse en Git.

## 3. Alcance de la primera etapa

La primera etapa incluyó:

- creación de la rama v2 desde el estado MDPI congelado;
- inventario del contenido versionado;
- clasificación preliminar;
- ejecución de la batería de pruebas existente;
- propuesta de limpieza y arquitectura objetivo.

En etapas posteriores ya se retiraron artefactos regenerables aprobados y se
migraron CEC2017, el registro de métricas y la persistencia SQLite v2. Todavía
no se incluyen:

- migración de optimizadores y runner;
- cambios al sistema de semillas;
- cambios en resultados o análisis del artículo.

## 4. Arquitectura objetivo

La visión doctoral y la navegación completa se mantienen en
`documentation/PROJECT_VISION.md` y
`documentation/architecture/MODULE_MAP.md`. El nombre conceptual del paquete
objetivo es `afcs` y las carpetas bajo `src/afcs/` documentan desde ahora la
responsabilidad de cada módulo.

```text
src/
└── afcs/
    ├── core/
    ├── problems/
    │   ├── benchmarks/
    │   ├── scp/
    │   ├── uscp/
    │   └── knapsack/
    ├── optimizers/
    │   ├── pso/
    │   └── ga/
    ├── metrics/
    ├── fuzzy/
    ├── selectors/
    ├── controllers/
    ├── binarization/
    ├── experiments/
    ├── persistence/
    └── analysis/

configs/
├── examples/
├── experiments/
└── schemas/

scripts/
tests/
documentation/
├── architecture/
├── lessons_learned/
├── migration/
└── reproducibility/
```

La estructura es un objetivo, no una instrucción para mover todo de una sola
vez. Cada módulo debe migrarse con sus imports y pruebas en un cambio acotado.

## 5. Clasificación y tratamiento propuesto

### 5.1 Conservar y convertir en núcleo v2

- Implementaciones CEC2017 y benchmarks clásicos.
- PSO, PSO_FCS y componentes realmente utilizados.
- Controladores difusos activos.
- Utilidades de diversidad requeridas por los solvers.
- Pruebas existentes y nuevas pruebas de integración.
- Configuraciones de ejemplo mínimas.
- Scripts de análisis que puedan operar sobre un esquema documentado.

### 5.2 Conservar como conocimiento para agentes

- Diagnósticos de CEC2017.
- Errores de implementación ya identificados.
- Decisiones metodológicas reutilizables.
- Recomendaciones sobre reproducibilidad, presupuestos y análisis estadístico.
- Explicaciones sobre archivos que no deben reutilizarse sin validación.

Estos contenidos deben consolidarse posteriormente en
`documentation/lessons_learned/`, evitando múltiples copias históricas.

### 5.3 Preservar solamente en la rama MDPI

- Manuscrito y versiones PDF fechadas.
- Material suplementario enviado o preparado para el artículo.
- Resultados finales y parciales específicos de esa campaña.
- Figuras, tablas y exportaciones del manuscrito.
- Archivos de revisión editorial.
- Copias archivadas de scripts previos.
- Literatura en PDF.

Antes de retirarlos de v2 se debe confirmar que están presentes en `f864913`.

### 5.4 Eliminar de v2 o ignorar

- Bases SQLite, `-wal` y `-shm`.
- Logs, temporales y salidas de consola.
- Figuras y tablas regenerables.
- CSV/Parquet derivados que puedan recrearse desde datos fuente autorizados.
- Directorios `attempt*_partial`.
- Duplicados exactos por SHA-256.
- Scripts temporales `_tmp_*` y `_fix_*` ya absorbidos en código estable.
- Configuración local de IDE, salvo una configuración compartida justificada.

## 6. Orden de implementación

### Fase A — Inventario y reglas

1. Aprobar este plan y el inventario asociado.
2. Definir qué constituye dato fuente y qué es resultado derivado.
3. Crear una lista explícita de conservación.
4. Completar `.gitignore` sin borrar todavía material versionado.
5. Crear guía de recuperación desde la rama MDPI.

### Fase B — Limpieza del artículo

1. Retirar de v2 archivos exclusivos del manuscrito.
2. Retirar duplicados y resultados parciales.
3. Conservar únicamente ejemplos pequeños de análisis.
4. Verificar que ninguna importación operativa apunta a archivos retirados.
5. Ejecutar pruebas y un smoke test.

### Fase C — Empaquetado y configuración

1. Introducir `pyproject.toml`.
2. Definir paquete `src/` e imports absolutos estables.
3. Añadir esquema de configuración validado. La expansión/persistencia tipada ya
   está implementada; falta la entrada humana y su lector.
4. Sustituir scripts numerados por una CLI documentada.
5. Separar configuración de benchmark, algoritmo, campaña y análisis.

### Fase D — Reproducibilidad y semillas

Implementar `config/PROPUESTA_IMPLEMENTACION_SEMILLAS.md` como un cambio
independiente:

1. Persistir `replica_index` y `master_seed`.
2. Eliminar la dependencia de `id_experimento`.
3. Validar orden de inserción y paralelismo.
4. Migrar a generadores explícitos y subflujos.
5. Registrar procedencia y hashes de condiciones iniciales.

### Fase E — Ejecutor y persistencia

1. Separar solver, runner, base de datos y exportación.
2. Introducir presupuesto explícito de evaluaciones.
3. Marcar `NaN`, `inf` y excepciones como fallos.
4. Versionar el esquema de base de datos mediante migraciones.
5. Añadir ejecución reanudable e idempotente.
6. Permitir optimizadores con o sin política externa de parámetros.
7. Separar configuración inicial, adaptación dinámica e instrumentación.
8. Registrar costes del evaluador, optimizador, métricas y controlador.

La separación de optimizadores seguirá
`documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md`. PSO será la
primera integración, pero los contratos no se limitarán al parámetro `w`.

### Fase F — Calidad compartible

1. Formateador, linter y comprobación de tipos.
2. CI con pruebas unitarias y smoke test.
3. Documentación de instalación y contribución.
4. Ejemplo reproducible pequeño sin bases externas.
5. Política de versiones y changelog.

## 7. Estrategia de commits

```text
docs(v2): inventory repository and define migration plan
chore(v2): remove article-specific generated artifacts
chore(v2): consolidate reusable analysis and lessons learned
build(v2): introduce package metadata and quality tooling
refactor(config): add validated configuration model
feat(seeding): persist replica and master seed
refactor(rng): introduce explicit random generators
refactor(benchmarks): define common benchmark interface
refactor(runner): separate execution and persistence
test(v2): add reproducibility and parallel execution tests
docs(v2): add contributor and agent guidance
```

## 8. Gates de aceptación

La limpieza estructural no se considera terminada hasta que:

- las pruebas existentes sigan pasando;
- exista un smoke test extremo a extremo;
- el repositorio pueda clonarse e instalarse desde cero;
- no dependa de archivos del artículo para ejecutar un experimento nuevo;
- no contenga resultados regenerables o bases de datos versionadas;
- las funciones CEC2017 conserven su batería de regresión;
- la configuración inválida falle antes de crear experimentos;
- la ejecución secuencial y paralela sea reproducible.

## 9. Decisiones aprobadas

### 9.1 Referencia histórica del artículo

Se retirará de v2 el material específico del artículo que no sea necesario para
operar o entender el framework. En su lugar se conservará un README que indique:

- rama histórica: `Solver_CEC_Fuzzy_PSO_ARTICULO_MDPI`;
- commit congelado: `f8649134362f9a7b5e04f2f2bf032eb4b5938172`;
- contenido disponible allí: manuscrito, resultados, figuras, suplementos,
  archivos editoriales y versiones históricas de los análisis.

### 9.2 Código de análisis

Se conservará todo código estadístico o analítico que pueda reutilizarse en
nuevas campañas. La conservación no implica mantener todas las copias actuales:

1. identificar la versión más reciente y fiable de cada análisis;
2. consolidar duplicados;
3. desacoplar rutas y nombres específicos del artículo;
4. parametrizar entradas y salidas;
5. añadir pruebas con datos pequeños;
6. documentar supuestos, unidad experimental y formato esperado.

Se priorizarán análisis de agregación, rankings, convergencia, pruebas no
paramétricas, comparaciones pareadas/no pareadas, Pareto, escalabilidad,
diversidad, dinámica del controlador y generación de tablas o figuras.

### 9.3 Familias de problemas

BEN/CEC, SCP y USCP seguirán formando parte del núcleo. La arquitectura debe
permitir añadir otros problemas de ingeniería, en particular Knapsack Problem
(KP), sin incorporar casos especiales en el runner principal.

Cada familia deberá implementar un contrato común para:

- carga o construcción de instancia;
- dominio y representación de soluciones;
- evaluación y dirección de optimización;
- restricciones y reparación;
- óptimo o referencia conocida, cuando exista;
- metadatos y serialización de resultados.

### 9.4 Metaheurísticas

No se eliminarán las metaheurísticas distintas de PSO/PSO_FCS. La versión 2
debe permitir aplicar control difuso inicialmente a PSO y posteriormente a GA y
otras metaheurísticas clásicas.

Durante la limpieza se distinguirá entre:

- metaheurística soportada y cubierta por pruebas;
- implementación experimental que necesita adaptación;
- código duplicado u obsoleto sustituido por una versión consolidada.

No se borrará una implementación solamente por no estar incluida en la primera
campaña v2.

### 9.5 Fixtures de pruebas

Un *fixture* es un conjunto de datos pequeño, estable y versionado que permite
comprobar automáticamente una ruta del sistema. No representa una campaña ni
se utiliza para obtener conclusiones científicas.

Decisión adoptada: conservar o crear fixtures mínimos y preferentemente
sintéticos, no datasets completos del artículo. Como mínimo:

- uno o dos benchmarks deterministas de dimensión pequeña;
- una instancia SCP pequeña con óptimo conocido;
- una instancia USCP pequeña;
- una instancia KP pequeña cuando se formalice su integración;
- un extracto tabular artificial para probar el pipeline estadístico;
- salidas esperadas y tolerancias explícitas.

Los fixtures deben caber cómodamente en Git, evitar información redundante y
tener procedencia o método de generación documentado.

## 10. Condición para comenzar la limpieza

Las decisiones de alcance están aprobadas. Antes de eliminar archivos se debe
producir una lista concreta por ruta con una de estas acciones:

- conservar sin cambios;
- consolidar o refactorizar;
- mover a documentación de lecciones aprendidas;
- retirar de v2 porque permanece en la rama MDPI;
- ignorar por ser generado o temporal.

La primera limpieza deberá separar el material histórico del artículo sin
eliminar código reutilizable de análisis, familias de problemas ni
metaheurísticas.

La clasificación concreta está documentada en
[`V2_CLEANUP_MANIFEST.md`](V2_CLEANUP_MANIFEST.md). Ese manifiesto es la lista
de control para ejecutar la limpieza por olas y exige verificación histórica,
pruebas y smoke tests antes de retirar cada bloque.
