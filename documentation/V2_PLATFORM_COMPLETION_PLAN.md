# Plan de finalización de la plataforma v2

**Rama:** `Solver_CEC_Fuzzy_PSO_v2`

**Estado de referencia:** integración secuencial CEC2017–PSO–FCS validada

**Prioridad:** terminar una plataforma reutilizable antes de diseñar campañas
científicas para artículos.

## 1. Separación de alcances

La plataforma v2 proporciona mecanismos generales: problemas, optimizadores,
control opcional de parámetros, métricas, semillas, campañas, persistencia y
análisis. Una campaña científica es un consumidor posterior de esos mecanismos.

Por tanto, no son requisitos para cerrar la plataforma:

- elegir el presupuesto definitivo del Paper 2;
- ejecutar el factorial completo de overlap;
- seleccionar funciones o comparadores confirmatorios;
- ejecutar el microbenchmark publicable dense/sparse;
- fijar las familias de hipótesis estadísticas de un artículo concreto.

Sí es requisito que la plataforma permita expresar, validar, ejecutar y analizar
esas decisiones cuando sean aprobadas, sin valores ocultos ni cambios de código.

## 2. Estado funcional alcanzado

- paquete instalable `afcs` y contratos fundamentales;
- adaptador CEC2017 validado, con F2 excluida explícitamente;
- PSO v2 con inercia fija, `legacy_ldiw` y `fuzzy_inertia_mamdani`;
- semillas pareadas y subflujos NumPy versionados;
- configuración de campañas validada y previsualización de costo;
- ejecución secuencial `preview → plan → run`;
- SQLite v2 transaccional con campañas, réplicas, métricas y trazas;
- registro seleccionable y versionado de métricas;
- FIS triangular/gaussiano, overlap compartido/independiente e inferencia
  densa/dispersa;
- validación técnica CEC2017–PSO–FCS de 42 corridas sin fallos;
- batería automatizada que cubre las tres familias matemáticas y el núcleo
  experimental.

## 3. Trabajo necesario para declarar v2 terminada

### Bloque A — endurecimiento del núcleo experimental

1. [Completado] Recuperación explícita de réplicas abandonadas en `running`,
   conservando intentos auditables y sin sobrescribir resultados.
2. [Completado] Ejecución por procesos reproducible e independiente del orden,
   con conexiones SQLite y estado RNG aislados por trabajador.
3. [Completado] `NaN`, `inf`, excepciones y presupuesto exacto se rechazan y
   dejan evidencia estructurada. La cancelación es explícita, exige motivo,
   descarta observaciones parciales y no provoca reintentos automáticos.
4. [Completado] Tiempos monotónicos separados para evaluación del problema,
   ejecución inclusiva del optimizador, métricas, controlador, persistencia y
   pared total, seleccionables mediante el perfil `timing`.
5. [Completado] Inspección read-only de integridad relacional, intentos, NFE,
   resultados y trazas de campañas.

### Bloque B — contratos generales de problemas

1. [Completado] Benchmarks matemáticos consolidados bajo `afcs.problems`:
   `CLASSICAL` F1-F23, `CEC2017` autocontenido y suites CEC de `OPFUNU_CEC`,
   con familia, año, función, dimensión, implementación y versión auditables.
2. Migrar SCP y USCP mediante el contrato común de problema, restricciones y
   reparación.
3. Incorporar un fixture mínimo de Knapsack y dejar preparada su familia.
4. Clasificar binarización, funciones de transferencia y reparación por módulo.
5. Asegurar que el runner no contiene casos especiales por familia.

### Bloque C — contratos generales de optimizadores

1. Congelar PSO v2 como primera implementación de referencia.
2. Migrar GA con ejecución sin adaptación y con punto de extensión para control
   futuro de parámetros.
3. Inventariar las demás metaheurísticas como soportadas, experimentales o
   heredadas, sin eliminarlas silenciosamente.
4. Definir observaciones comunes y específicas por optimizador para que las
   métricas no dependan de PSO.
5. Añadir pruebas de presupuesto, dirección, semillas y replay para cada
   optimizador soportado.

### Bloque D — análisis reutilizable

1. Definir la vista o exportación tabular canónica desde SQLite.
2. Migrar agregaciones, análisis pareados, Holm, tamaños de efecto, convergencia
   y generación de tablas/figuras sobre fixtures pequeños.
3. Etiquetar cualquier métrica reconstruida y mantener SQLite como fuente
   primaria de datos experimentales.
4. Parametrizar entradas y salidas; retirar rutas y nombres específicos del
   artículo de las implementaciones autoritativas.
5. Probar reconciliación entre tablas, figuras y datos fuente.

### Bloque E — limpieza y fuente única de verdad

1. Actualizar el manifiesto por ruta y comprobar cada elemento histórico contra
   el commit MDPI congelado.
2. Retirar de v2 resultados, manuscritos, binarios y duplicados recuperables.
3. Conservar únicamente conocimiento, fixtures y código reutilizable.
4. Eliminar puentes heredados solo después de migrar todos sus consumidores.
5. Confirmar que ningún módulo operativo importa rutas históricas.

### Bloque F — calidad y distribución

1. Añadir formateo, lint y comprobación de tipos con configuración versionada.
2. Configurar CI para instalación limpia, pruebas unitarias y smoke tests.
3. Completar guías de instalación, uso, contribución y extensión.
4. Definir versionado, changelog y política de compatibilidad de esquemas.
5. Verificar una instalación desde cero sin datos ni dependencias del artículo.

## 4. Orden recomendado

1. Congelar en un commit la integración PSO–FCS ya validada.
2. Ejecutar Bloque A: endurecimiento del runner y campañas.
3. Ejecutar Bloques B y C: generalización a problemas y optimizadores.
4. Ejecutar Bloque D: análisis reutilizable desde SQLite.
5. Ejecutar Bloque E: limpieza final una vez disponibles los reemplazos.
6. Ejecutar Bloque F y publicar una versión candidata `2.0.0-rc1`.

El microbenchmark dense/sparse puede conservarse como prueba técnica de costo,
pero no desplaza este orden ni autoriza experimentación de artículos.

## 5. Puerta de salida de plataforma

La plataforma podrá considerarse finiquitada cuando:

- se instale desde cero y su CI esté verde;
- pueda ejecutar en forma secuencial y paralela con replay reproducible;
- recupere interrupciones mediante una política explícita y auditada;
- soporte al menos CEC/BEN, SCP, USCP y un fixture KP;
- soporte PSO y GA bajo contratos comunes;
- permita optimizadores con y sin control externo de parámetros;
- persista configuraciones, semillas, resultados y métricas sin reconstrucción
  silenciosa;
- produzca análisis reutilizables desde SQLite sobre fixtures;
- no dependa operativamente del árbol del artículo MDPI;
- no mantenga dos implementaciones autoritativas de una misma capacidad;
- cuente con documentación de usuario y desarrollador coherente con el código.

Solo después de esta puerta se congelarán protocolos y se ejecutarán campañas
científicas destinadas a publicaciones.
