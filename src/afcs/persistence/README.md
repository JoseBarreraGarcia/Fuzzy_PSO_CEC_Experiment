# Persistence

Base SQLite versionada, repositorios, migraciones, sellado, exportaciones y
procedencia. No calcula métricas ni decide configuración científica.

Estado: implementación migrada:

- `database.py`: conexiones de escritura/solo lectura, validación de historial
  compatible y aplicación explícita de migraciones;
- `repository.py`: ciclo transaccional de campañas, réplicas, trazas y métricas;
- `integrity.py`: auditoría read-only de estructura, estados, intentos,
  presupuestos, resultados y trazas;
- `migrations/`: esquema SQLite versionado incluido en el paquete.

La migración 004 separa réplicas lógicas de intentos operativos mediante
`run_attempts`. La migración 005 incorpora cancelaciones justificadas y
excepciones auditables para el sellado de campañas incompletas. La CLI ofrece
recuperación explícita, cancelación, sellado y auditoría integral; ninguna de
estas operaciones reconstruye resultados.

La migración 006 separa etiqueta local de tratamiento y clave interna sin
reescribir referencias anteriores, y añade versión explícita del formato de
huella inicial. El repositorio rechaza conflictos en óptimo, dirección o huella
de una instancia compartida. Los contratos y límites están en
[SQLite v2](../../../documentation/architecture/SQLITE_V2_SCHEMA.md).

La migración 007 separa resultado confirmado y finalización operativa, con
estados/errores propios, y registra la fase de fallos de réplica e intento.
`run_contracts.py` comparte invariantes de solución, best-so-far y tiempos
post-commit entre repositorio, auditoría y exportación. Un cierre fallido
conserva el resultado pero no permite cerrar/sellar ni exportar como válido;
el sello exige auditoría integral bajo bloqueo de escritura. No se rellenan
campos históricos ni se repiten réplicas para ocultar fallos de finalización.

Los puentes `BD/persistence_v2.py` y `BD/repository_v2.py` se retiraron: los
consumidores v2 importan directamente `afcs.persistence`. Las migraciones
autoritativas se distribuyen en este paquete, no en `BD/`.

`BD/sqlite.py` se retiró después de sus consumidores numerados y del
dispatcher de benchmarks. Su versión modificada se conserva como snapshot
verificado en Review, sin sobrescribir el original. Su esquema fijo,
catálogos y cola están superados por los contratos v2: no se migraron otra
vez ni se archivaron como capacidad futura.

También se retiraron `Util/check_db.py`, `check_coverage.py`,
`check_integrity.py`, `check_progress.py` y `9_db_scanner.py`, cuyos originales
coinciden con Review. Consultaban SQLite directamente, no la clase BD.
Sus supuestos de 31 réplicas, 33 algoritmos, intervalos de inercia fijos y
estados históricos no son contratos generales. El scanner deducía dimensiones
desde etiquetas y tomaba parámetros de una sola fila, con valores por defecto
y una réplica: su salida no reconstruye una campaña reproducible.
La auditoría y el ciclo operativo v2 usan los módulos anteriores, no esos
scripts ni un adaptador del esquema antiguo.

Las bases locales históricas se preservaron en la carpeta `BD` de la copia
Review, verificando SHA-256 y metadatos antes de retirarlas de este worktree.
La operación quedó registrada allí en `v2_cleanup_bd_20261109.json`.
Los scripts antiguos ya no disponen aquí de esos resultados; no ejecutarlos
para inspeccionar el respaldo, pues sus conexiones pueden crear bases vacías
o modificar el journal. La API v2 recibe rutas explícitas y no importa ni
migra automáticamente el esquema histórico.
