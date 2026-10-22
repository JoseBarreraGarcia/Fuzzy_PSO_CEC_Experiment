# Propuesta de implementación del sistema de semillas reproducibles

**Estado:** contrato aprobado e implementado en la arquitectura v2.

**Fecha:** 19 de octubre de 2026.

**Implementación v2:** 22 de octubre de 2026.
**Alcance:** generación, persistencia y aplicación de semillas para campañas
experimentales. Esta propuesta no modifica las funciones CEC 2017.

La implementación vigente utiliza `runs.random_seed` como semilla maestra de
la réplica, conserva `replica_index` y registra en la campaña `base_seed`,
`seed_protocol` y `rng_engine`. Los nombres físicos difieren de la propuesta
inicial, pero mantienen su semántica. El runner y los optimizadores legacy aún
no se han migrado; la garantía aplica al flujo modular `src/afcs/`.

## 1. Problema actual

El ejecutor calcula la semilla mediante:

```python
exp_seed = base_seed + exp_id
```

`exp_id` es la clave primaria de la tabla `experimentos`. Por ello, la semilla
depende del orden en que se insertaron los tratamientos en la base de datos.
Dos configuraciones que representan la misma réplica no reciben la misma
aleatoriedad y recrear la base con otro orden puede cambiar todos los
resultados.

Esto impide garantizar un diseño de *Common Random Numbers* (CRN), en el cual
los tratamientos comparados dentro de la misma instancia y réplica deben partir
de condiciones aleatorias equivalentes.

## 2. Contrato propuesto

Para `R = 31` réplicas se define:

```text
replica_index = 0, 1, ..., 30
master_seed   = base_seed + replica_index
base_seed     = 42
master_seed   = 42, 43, ..., 72
```

La semilla debe depender exclusivamente de la réplica. No debe depender de:

- `id_experimento`;
- orden de inserción en SQLite;
- cantidad de workers;
- orden de ejecución;
- nombre de la metaheurística;
- configuración del controlador difuso.

Para una misma combinación `(instancia, dimensión, replica_index)`, PSO y todos
los tratamientos PSO_FCS deben compartir `master_seed`.

## 3. Diseño recomendado

### 3.1 Persistencia explícita

Añadir a `experimentos`:

```sql
replica_index INTEGER NOT NULL,
master_seed   INTEGER NOT NULL
```

No se recomienda guardar estos datos dentro de `paramMH`: son metadatos del
diseño experimental, deben poder consultarse y validarse mediante SQL y no
deben confundirse con parámetros del algoritmo.

Restricciones recomendadas:

```sql
CHECK (replica_index >= 0),
CHECK (master_seed >= 0)
```

También se recomienda un índice para auditoría y análisis:

```sql
CREATE INDEX idx_experimentos_replica
ON experimentos (fk_id_instancia, replica_index, master_seed);
```

### 3.2 Generación al poblar la base

`BD.insertarExperimentos` debe recibir `base_seed` y crear cada registro con su
índice de réplica:

```python
for replica_index in range(corridas):
    master_seed = base_seed + replica_index
    insertar(..., replica_index, master_seed, ...)
```

`1_0_poblarDB.py` debe leer `seed` desde el JSON y pasarlo al método de
inserción. De este modo la asignación queda congelada antes de ejecutar y puede
inspeccionarse sin iniciar ningún solver.

### 3.3 Aplicación en el worker

`2_main.py` debe leer `master_seed` del registro obtenido. Debe eliminarse:

```python
exp_seed = base_seed + exp_id
```

Como compatibilidad temporal, una base antigua sin las columnas nuevas debe
fallar con un mensaje claro. No se recomienda conservar silenciosamente la
derivación por `exp_id`, porque produciría campañas con dos contratos de
reproducibilidad diferentes.

### 3.4 Generadores separados

La opción mínima consiste en ejecutar:

```python
np.random.seed(master_seed)
random.seed(master_seed)
```

Sin embargo, la opción recomendada es migrar progresivamente a generadores
explícitos basados en `numpy.random.SeedSequence`:

```python
root = np.random.SeedSequence(master_seed)
init_ss, dynamics_ss = root.spawn(2)
init_rng = np.random.default_rng(init_ss)
dynamics_rng = np.random.default_rng(dynamics_ss)
```

- `init_rng`: creación de la población y velocidades iniciales.
- `dynamics_rng`: números aleatorios consumidos durante las iteraciones.

Separar estos flujos evita que un cambio en la inicialización desplace toda la
secuencia usada por la dinámica. Para preservar CRN, las rutas comparadas deben
consumir los números comunes en el mismo orden. Si PSO_FCS necesita aleatoriedad
adicional exclusiva, debe recibir un tercer subflujo y no consumir valores del
flujo común de PSO.

## 4. Configuración propuesta

Mantener las claves actuales por compatibilidad semántica:

```json
"use_seed": true,
"seed": 42
```

Y documentarlas así:

- `use_seed`: activa el contrato reproducible.
- `seed`: primera semilla maestra, no una semilla única para toda la campaña.
- `num_experimentos`: número de réplicas; la réplica `r` usa `seed + r`.

Opcionalmente se puede introducir una sección más explícita en una versión
posterior:

```json
"randomness": {
    "enabled": true,
    "base_seed": 42,
    "policy": "paired_by_replica",
    "engine": "numpy_seedsequence"
}
```

No conviene mantener simultáneamente ambas sintaxis de forma indefinida. Si se
adopta `randomness`, debe existir una fase de deprecación y una validación que
rechace configuraciones contradictorias.

## 5. Archivos que se modificarían

| Archivo | Cambio previsto |
|---|---|
| `BD/sqlite.py` | Añadir columnas, índice y argumentos de réplica/semilla en la inserción. |
| `1_0_poblarDB.py` | Enumerar réplicas y pasar `base_seed` al acceso a datos. |
| `2_main.py` | Leer la semilla persistida; dejar de derivarla desde `exp_id`. |
| `Solver/population/population_BEN.py` | Aceptar `init_rng` cuando se migre a generadores explícitos. |
| `Solver/solverBEN.py` | Crear/recibir subflujos y propagarlos a población y metaheurística. |
| `Metaheuristics/*` | Sustituir accesos globales a `np.random`/`random` por el generador recibido. |
| `config/experiments*.json` | Documentar o adoptar el nuevo contrato de configuración. |
| `tests/test_experiment_seeding.py` | Incorporar pruebas unitarias, SQL y de reproducción. |
| `README.md` o documentación experimental | Explicar semillas, emparejamiento y limitaciones CRN. |

La primera fase puede limitarse a `BD/sqlite.py`, `1_0_poblarDB.py`,
`2_main.py` y las pruebas. La migración completa a objetos `Generator` debe
realizarse en una segunda fase, porque afecta a las metaheurísticas.

## 6. Migración de la base de datos

Las campañas antiguas no contienen `replica_index` ni `master_seed`; no es
seguro inferirlos desde `id_experimento` salvo que se demuestre y documente el
orden exacto de inserción.

Propuesta:

1. No modificar resultados históricos en sitio.
2. Crear una base nueva para la campaña corregida.
3. Marcar los resultados históricos como pertenecientes al contrato
   `legacy_exp_id_seed` si se conservan para análisis.
4. Registrar en cada exportación la política de semillas utilizada.
5. Impedir que resultados `legacy_exp_id_seed` y `paired_by_replica` se mezclen
   como si pertenecieran al mismo bloque CRN.

Si se requiere mantener la misma base, debe crearse un script de migración con
copia de seguridad, transacción y verificación posterior. Esa migración no debe
formar parte implícita de `construirTablas()`.

## 7. Pruebas necesarias

### 7.1 Asignación

- Con `base_seed=42` y 31 réplicas se obtienen exactamente 42-72.
- Dos tratamientos de la misma instancia y réplica tienen la misma
  `master_seed`.
- Réplicas distintas tienen semillas distintas.
- Cambiar el orden de `mhs` o `mh_params` no cambia las semillas asignadas.
- Cambiar `parallel_workers` no cambia las semillas.

### 7.2 Base de datos

- `replica_index` y `master_seed` se almacenan y recuperan sin depender del ID.
- Las restricciones rechazan réplicas o semillas negativas.
- Una consulta detecta duplicados o huecos de réplicas por tratamiento.
- Faltan cero combinaciones esperadas antes de iniciar la campaña.

### 7.3 Reproducción

- Repetir un experimento produce población inicial, trayectoria y resultado
  idénticos.
- Ejecutar secuencialmente y con varios workers produce los mismos resultados.
- Ejecutar los registros en orden inverso no cambia los resultados.
- PSO y PSO_FCS de una misma réplica tienen población y velocidades iniciales
  idénticas, comprobadas mediante hash.

### 7.4 Subflujos

- Consumir números del subflujo exclusivo de PSO_FCS no altera `init_rng` ni el
  flujo común de dinámica.
- Ningún módulo usa `np.random` o `random` global después de completar la
  migración a `Generator`.

## 8. Evidencia que debe guardarse

Por ejecución:

- `replica_index`;
- `master_seed`;
- política y motor RNG;
- versión de NumPy y Python;
- hash de la población inicial;
- hash de las velocidades iniciales;
- hash o versión del código;
- identificador de instancia, dimensión y tratamiento.

No es necesario guardar el estado completo del generador si el código y el
orden de consumo están congelados, aunque puede ser útil para depuración.

## 9. Secuencia de implementación

### Fase A: contrato persistido

1. Añadir esquema y modelo de datos.
2. Poblar `replica_index` y `master_seed`.
3. Leer `master_seed` en el worker.
4. Añadir pruebas de asignación, orden y paralelismo.
5. Crear una base nueva y ejecutar un piloto pequeño.

### Fase B: generadores explícitos

1. Inventariar todos los usos de `np.random` y `random`.
2. Introducir `SeedSequence` y subflujos.
3. Propagar los RNG por solver, población y metaheurísticas.
4. Verificar consumo estable y condiciones iniciales idénticas.
5. Eliminar gradualmente el estado aleatorio global.

### Fase C: auditoría y congelación

1. Ejecutar las pruebas en modo secuencial y paralelo.
2. Comparar hashes y resultados.
3. Registrar versiones y hashes.
4. Congelar configuración, código y base de datos vacía.
5. Autorizar la campaña completa únicamente después del piloto.

## 10. Criterios de aceptación

La implementación se considerará terminada cuando:

- las 31 réplicas estén identificadas explícitamente;
- cada réplica use una semilla 42-72;
- tratamientos emparejados compartan semilla y condiciones iniciales;
- IDs, orden de inserción, workers y orden de ejecución no afecten el resultado;
- las bases antiguas no se interpreten silenciosamente con el contrato nuevo;
- las pruebas unitarias y de integración pasen;
- la política quede registrada en resultados y documentación.

## 11. Decisiones resueltas para v2

1. El contrato es general para campañas v2, no exclusivo de CEC2017.
2. Se usan subflujos comunes separados para inicialización y dinámica; el
   controlador dispone de un tercer subflujo independiente.
3. La implementación v2 usa directamente `numpy.random.Generator` construido
   mediante `SeedSequence`; no recurre al estado global.
4. Los hashes SHA-256 de población y velocidades iniciales se almacenan en
   SQLite para cada réplica completada.
5. Con 31 réplicas y `base_seed=42` se persisten exactamente las semillas
   42–72, compartidas por todas las configuraciones del mismo índice.

Continúan pendientes la migración de los solvers heredados, las pruebas reales
de paralelismo y el piloto científico antes de una campaña exhaustiva.
