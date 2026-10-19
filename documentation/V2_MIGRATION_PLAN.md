# Plan de migración a Solver CEC Fuzzy PSO v2

**Rama:** `Solver_CEC_Fuzzy_PSO_v2`  
**Punto de partida:** `f8649134362f9a7b5e04f2f2bf032eb4b5938172`  
**Fecha:** 19 de octubre de 2026  
**Estado:** fase inicial de inventario; no se ha eliminado ni reorganizado código.

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

Esta etapa incluye solamente:

- creación de la rama v2 desde el estado MDPI congelado;
- inventario del contenido versionado;
- clasificación preliminar;
- ejecución de la batería de pruebas existente;
- propuesta de limpieza y arquitectura objetivo.

No incluye todavía:

- eliminación de archivos;
- movimientos de módulos;
- cambios al sistema de semillas;
- migraciones de base de datos;
- cambios en resultados o análisis del artículo.

## 4. Arquitectura objetivo

```text
src/
├── benchmarks/
│   ├── classical/
│   └── cec2017/
├── optimizers/
│   ├── pso/
│   └── fuzzy_pso/
├── experiment/
│   ├── runner.py
│   ├── seeding.py
│   ├── budget.py
│   └── provenance.py
├── persistence/
│   ├── database.py
│   └── migrations/
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
3. Añadir esquema de configuración validado.
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

## 9. Decisiones que requieren aprobación

Antes de comenzar la Fase B se debe decidir:

1. Si `FUZZY/ARTICULO_MDPI/` se retira por completo de v2 o se conserva un
   README que apunte a la rama histórica.
2. Qué scripts de `analysis_modules*` y `FUZZY/ARTICULO_MDPI/code` se consideran
   reutilizables.
3. Si SCP y USCP seguirán formando parte del núcleo v2.
4. Si las metaheurísticas distintas de PSO/PSO_FCS se mantienen como soportadas.
5. Qué resultados mínimos se conservarán como fixture de pruebas.

Hasta resolver estas decisiones, no debe ejecutarse una limpieza destructiva.
