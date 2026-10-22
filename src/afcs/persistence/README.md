# Persistence

Base SQLite versionada, repositorios, migraciones, sellado, exportaciones y
procedencia. No calcula métricas ni decide configuración científica.

Estado: implementación migrada:

- `database.py`: conexión, descubrimiento y aplicación de migraciones;
- `repository.py`: ciclo transaccional de campañas, réplicas, trazas y métricas;
- `migrations/`: esquema SQLite versionado incluido en el paquete.

`BD/persistence_v2.py` y `BD/repository_v2.py` son puentes temporales sin
implementación independiente. La base histórica `BD/sqlite.py` permanece
separada y no se migra ni modifica automáticamente.
