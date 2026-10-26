# Persistence

Base SQLite versionada, repositorios, migraciones, sellado, exportaciones y
procedencia. No calcula métricas ni decide configuración científica.

Estado: implementación migrada:

- `database.py`: conexión, descubrimiento y aplicación de migraciones;
- `repository.py`: ciclo transaccional de campañas, réplicas, trazas y métricas;
- `integrity.py`: auditoría read-only de estructura, estados, intentos,
  presupuestos, resultados y trazas;
- `migrations/`: esquema SQLite versionado incluido en el paquete.

La migración 004 separa réplicas lógicas de intentos operativos mediante
`run_attempts`. La migración 005 incorpora cancelaciones justificadas y
excepciones auditables para el sellado de campañas incompletas. La CLI ofrece
recuperación explícita, cancelación, sellado y auditoría integral; ninguna de
estas operaciones reconstruye resultados.

`BD/persistence_v2.py` y `BD/repository_v2.py` son puentes temporales sin
implementación independiente. La base histórica `BD/sqlite.py` permanece
separada y no se migra ni modifica automáticamente.
