# Plan de finalización de la plataforma v2

**Rama:** `Solver_CEC_Fuzzy_PSO_v2`

**Estado de referencia (9 de noviembre de 2026):** núcleo continuo con PSO/PSO-FCS,
GA real-coded, ejecución secuencial/paralela y análisis canónico implementados;
limpieza histórica y auditoría interna R1/R2 cerradas para el alcance revisado;
R3 verificado localmente en Windows/Python 3.14.4; R4 tiene controles locales
verdes en Windows/Python 3.11.9 y 3.14.4, con 312 pruebas e instalaciones no
editables de núcleo/extras. CI, matriz de soporte y autorización de distribución siguen pendientes;
esto no certifica lanzamiento.

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
- ejecución `preview → plan → run`, secuencial o por procesos;
- recuperación y cancelación explícitas con intentos auditables;
- GA real-coded con presupuesto, semillas y trazas bajo contratos comunes;
- SQLite v2 transaccional con campañas, réplicas, métricas y trazas;
- registro seleccionable y versionado de métricas;
- FIS triangular/gaussiano, overlap compartido/independiente e inferencia
  densa/dispersa;
- análisis canónico desde SQLite con exportaciones reconciliadas, descriptivos,
  pruebas estadísticas, convergencia, tablas y figuras;
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
2. [En pausa por decisión metodológica] Migrar SCP y USCP mediante el contrato
   común de problema, restricciones y reparación.
3. [En pausa por decisión metodológica] Incorporar un fixture mínimo de
   Knapsack y dejar preparada su familia.
4. [En pausa por decisión metodológica] Clasificar e integrar binarización,
   funciones de transferencia y reparación. El inventario heredado se conserva
   sin convertirlo todavía en dependencia del núcleo v2.
5. Evaluar como próxima ampliación problemas de ingeniería o benchmarks de
   variables continuas, manteniendo el mismo contrato y sin binarización.
6. [Completado] Separar `ProblemFactory` del adaptador PSO y confirmar que el
   runner no contiene casos especiales por familia.

**Decisión vigente (2026-10-26):** antes de incorporar dominios binarios se
priorizará decidir y, si corresponde, validar una familia adicional de
problemas continuos. SCP, USCP y KP no se eliminan del alcance futuro de la
tesis, pero su migración no condiciona el cierre inicial de la plataforma v2
hasta nuevo aviso. Reactivarlos requerirá una decisión metodológica explícita.

### Bloque C — contratos generales de optimizadores

1. [Completado] Congelar PSO v2 como primera implementación de referencia bajo
   la identidad `2.0.0a0-legacy-compatible`.
2. [Completado] Migrar GA real-coded para problemas continuos, con ejecución
   inicial sin adaptación y punto de extensión para control de probabilidades.
   La implementación binaria heredada permanece en pausa junto con la fase
   discreta.
3. Inventariar las demás metaheurísticas como soportadas, experimentales o
   heredadas, sin eliminarlas silenciosamente.
4. [Completado] Definir observaciones y recolectores comunes, poblacionales y
   específicos de PSO/controlador para que las métricas generales no dependan
   de PSO.
5. [PSO y GA completados] Añadir pruebas de presupuesto, dirección, semillas y
   replay para cada optimizador soportado; repetir el requisito al incorporar
   nuevos optimizadores.

### Bloque D — análisis reutilizable

1. [Completado] Definir una exportación tabular canónica de réplicas y trazas
   desde SQLite, conservando configuración, identidad, estado y procedencia
   por métrica.
2. [Completado] Descriptivos por instancia, rangos agregados, Wilcoxon pareado,
   Holm por campaña, rank-biserial, estimador Hodges-Lehmann, Friedman ómnibus,
   Kendall's W, post hoc Nemenyi condicionado al ómnibus y convergencia a
   conteos exactos de evaluaciones. Las pruebas cubren ausencia de trazas,
   checkpoints repetidos, puntos sin objetivo y procedencia. La aproximación
   chi-cuadrado de Friedman queda marcada como no recomendada para muestras
   que no cumplen la guía de SciPy.
3. [Completado] Etiquetar la procedencia de las métricas usadas en análisis:
   los resúmenes por instancia y convergencia cuentan valores observados,
   reconstruidos y esperados. La API de resumen de filas arbitrarias cuenta la
   procedencia ausente como no disponible; el informe canónico desde SQLite
   falla explícitamente si falta procedencia válida o el valor métrico no
   coincide con el objetivo almacenado. SQLite sigue siendo la fuente primaria.
4. [Completado] Parametrizar entradas y salidas y retirar rutas/nombres
   específicos del artículo de las implementaciones autoritativas. Las API
   aceptan campaign ID, rutas de CSV/informe, directorio de salida y alpha;
   los nombres internos de los artefactos son convenciones de formato, no
   referencias a campañas o artículos. Se verificó que el paquete de análisis
   no contiene rutas históricas.
5. [Completado] Reconciliar los CSV de réplicas/trazas con una proyección
   temporal de SQLite antes de permitir que se carguen como entrada analítica.
   El informe JSON canónico (esquema v3) se genera desde las filas verificadas
   y puede reconciliarse regenerándolo desde SQLite. Ocho tablas CSV y tres
   figuras PNG deterministas, incluida la convergencia, se generan y
   reconcilian contra el informe y manifiestos de hashes. La API
   `run_campaign_analysis` automatiza exportación, informe, tablas, figuras y
   reconciliación final.

### Bloque E — limpieza y fuente única de verdad

La retirada física del stack histórico ya se completó para las carpetas
revisadas. **Tesis queda fuera de la limpieza y de la auditoría de cierre**:
no inspeccionar ni modificar su contenido como parte de este trabajo.
La siguiente tarea no es seguir eliminando carpetas, sino auditar el contenido
activo de `src` según la etapa R1 de la sección 4.

1. [Completado] Revisar las rutas marcadas como históricas en el manifiesto y
   comprobar sus 24 rutas/patrones contra el árbol del commit MDPI congelado
   `f8649134362f9a7b5e04f2f2bf032eb4b5938172`; el README ya documenta cómo
   recuperar ese estado.
2. [Completado] Retirar los árboles históricos y sus consumidores tras verificar
   el respaldo. Los 819 archivos versionados del árbol MDPI coinciden por blob
   con Review; los 52 archivos ignorados (2.726.670.103 bytes) coinciden por
   tamaño y SHA-256. Las tres configuraciones MDPI también están en Review y
   sólo eran consumidas por scripts retirados con ese árbol. Se trasladaron
   además a Review los 44 archivos locales de `Resultados/` (15.692.018 bytes)
   tras verificar cada copia; el directorio quedó fuera del worktree v2.
3. [Alcance acordado] PSO/PSO-FCS y GA real-coded son optimizadores activos.
   Las 37 MH experimentales y el GA binario se conservan como fuentes pasivas
   en ARCHIVE. SCP/USCP también se trasladaron allí: dos fuentes pasivas y
   140 instancias verificadas contra Review, fuera del contrato operativo.
   La discretización es una fuente pasiva en `ARCHIVE/binarization/`,
   no código importable. `Metaheuristics/` y `Problem/` ya se retiraron.
   Procedencia/licencia de instancias y referencias USCP requieren verificación
   antes de una futura integración o redistribución pública.
4. [Completado: retirada física] Se retiraron los puentes de persistencia/métricas en `BD/` y
   `Util/` que sólo reexportaban APIs de `afcs` y no tenían consumidores dentro
   del repositorio. `2_main.py`, todo `Solver/` y `Diversity/` ya se retiraron;
   el wrapper lineal PSO ya se retiró trasladando sus regresiones al núcleo
   v2. El GA binario queda como fuente pasiva separada en ARCHIVE. El wrapper PSO-FCS, los
   tres controladores de `FUZZY/`, su JSON y el registro heredado ya se
   retiraron coordinadamente; las regresiones útiles prueban las APIs v2.
   El dispatcher de benchmarks ya se retiró trasladando sus regresiones a
   las APIs v2. Los comandos de creación/reinicio/población y los analizadores
   BEN/SCP también se retiraron, sin consumidores Python directos restantes
   de `BD/sqlite.py`; el módulo ya se retiró tras preservar su snapshot actual.
   Las cuatro bases históricas locales de `BD/`
   (9.751.830.528 bytes) ya se preservaron y verificaron por SHA-256/metadatos
   en Review, con recibo, y se retiraron de v2. `BD/sqlite.py` no se migrará
   de nuevo ni se archivará por compatibilidad. Los cuatro diagnósticos
   SQLite de `Util` y el scanner también se revisaron y retiraron: originales
   idénticos en Review, sin adaptar sus supuestos al esquema v2.
   Las cinco utilidades restantes y los JSON `experiments.json`/`directories.json`
   también se retiraron tras comprobar ausencia de consumidores y respaldos.
   `Util/` queda cerrado, sin otro paquete genérico de compatibilidad; los
   ejemplos activos de campañas y su esquema permanecen intactos.
5. [Pendiente: auditoría interna] Los lectores y scripts de análisis antiguos
   ya se retiraron. Falta justificar las capacidades incorporadas a `src`,
   distinguir decisiones metodológicas heredadas de adaptadores transitorios
   y resolver superficies sin consumidores operativos. Las pruebas existentes
   demuestran comportamiento, no justifican por sí solas conservar una API.
   Entre los candidatos a revisión están resúmenes iterativos rescatados,
   metadatos de métricas históricas y entradas alternativas RNG. No se declaran
   defectos ni se autoriza su retirada sólo por llevar la etiqueta legacy.

### Bloque F — calidad y distribución

Pendiente. Se ejecutará mediante las etapas R3 a R7 de la sección siguiente,
con evidencia separada de instalación, calidad, validación integral,
documentación y distribución. No hay workflows de CI actualmente; la licencia
general del proyecto y la distribución de material de terceros requieren
decisión explícita. La licencia incluida de CEC2017 no sustituye esa decisión.

## 4. Hoja de ruta acordada para el lanzamiento

Este es el orden de cierre, no una autorización para implementar todos los
bloques en una sola tanda. Cada etapa registra evidencia, pendientes y decisión
de cierre antes de pasar a la siguiente. No se asigna un porcentaje de avance
ni una fecha de lanzamiento hasta conocer los hallazgos de R1.

| Etapa | Estado | Depende de | Entregable / puerta de cierre |
|---|---|---|---|
| R1. Auditoría interna de `src` | Cerrada con decisiones trazadas en R2 | Ninguna | 31 hallazgos/candidatos investigados; resolución registrada sin confundir bugs y decisiones científicas |
| R2. Correcciones justificadas | Completada; grupos A-G cerrados | R1 y decisiones aprobadas | 31 entradas resueltas mediante correcciones o contratos explícitos; 310 pruebas aprobadas; no certifica lanzamiento |
| R3. Instalación limpia y artefactos | Completada localmente (Windows/Python 3.14.4) | R2 | Wheel y sdist inspeccionados; núcleo y extras no editables fuera del workspace; 310 pruebas desde el sdist |
| R4. Calidad y CI | Implementada y validada localmente; CI remota pendiente | R3 | Ruff/Pyright verdes en Windows 3.11/3.14; matriz candidata Windows/Ubuntu 3.11–3.14; cierre exige workflows reales verdes |
| R5. Validación integral de candidata | Pendiente | R4 | Flujo completo sobre paquete instalado, con replay, recuperación y análisis reconciliado |
| R6. Documentación de lanzamiento | Pendiente | R5 | Guías y ejemplos coherentes con capacidades realmente validadas |
| R7. Distribución y autorización | Pendiente | R6 y decisiones legales/de versión | Licencias, contenido distribuible, changelog, versión y compatibilidad resueltos; candidata aprobada |

Las decisiones de licencia, público/canal de distribución y matriz de soporte
pueden solicitarse antes para detectar bloqueos, pero no se presuponen ni se
posponen sus consecuencias hasta publicar.

### R1 — Auditar antes de cambiar

Revisar el paquete activo por responsabilidades: contratos/problemas y RNG;
optimizadores y control difuso; métricas/trazas; configuración, ejecución y
persistencia; análisis y API pública. Seguir sus relaciones reales, no limitarse
a buscar nombres `legacy`.

Por cada capacidad o superficie discutible registrar:

- archivo/símbolo y contrato que pretende satisfacer;
- consumidores operativos, exportaciones públicas y pruebas, diferenciados;
- origen: necesidad v2, decisión matemática heredada, compatibilidad temporal
  o capacidad futura sin integración operativa;
- evidencia del comportamiento y riesgos metodológicos/operativos;
- propuesta: conservar, simplificar, retirar o archivar con utilidad concreta;
- efecto sobre API, configuración, identidad, RNG, NFE y esquema;
- decisión pendiente y validación necesaria.

Primeros candidatos conocidos, todavía sin veredicto:

- reglas PSO conservadas, en especial `Vmax` a partir de `ub[0]`, calendario
  `legacy_ldiw` e identidad de implementación;
- entrada alternativa `rng=` frente a subflujos reproducibles de campañas;
- `summarize_convergence_curve` y `aggregate_iteration_values`, sus usos reales
  y diferencia respecto al análisis canónico por evaluaciones;
- metadatos `legacy_gap_percent` y `legacy_rdp_percent`;
- contratos futuros vacíos y README que aún describen estados anteriores.

**Cierre R1:** informe persistente con alcance, evidencia y tabla de decisiones,
incluidas incertidumbres. No basta con pasar pruebas ni con no encontrar imports
históricos. El informe no modifica fórmulas ni elimina APIs por su nombre.

### R2 — Resolver hallazgos sin otra reescritura

Separar errores comprobados, deuda de compatibilidad y elecciones científicas.
Aplicar cambios coherentes por responsabilidad y mantener una sola autoridad.
Retirar una superficie exige revisar consumidores, documentación, tests y
posibles datos/configuraciones persistidos, no sólo imports internos.

Los cambios que redefinan fórmulas, inicialización, fronteras, RNG, presupuesto,
identidad científica o significado estadístico no son limpieza mecánica.
Aplicar el mandato siguiente para distinguir correcciones técnicas de
decisiones científicas; no convertir silenciosamente PSO en otra variante.

#### Mandato general aprobado para R2

El usuario autoriza continuar los grupos restantes sin aprobación ítem por
ítem para correcciones técnicas justificadas. Prioridad: prevenir defectos que
invaliden, sesguen o hagan irreproducibles las campañas y su reporte posterior.

1. Elegir la solución más sólida en integridad experimental, claridad,
   escalabilidad y mantenimiento, conforme a buenas prácticas pertinentes.
   No preservar errores por compatibilidad histórica ni añadir abstracciones
   sin necesidad.
2. Mantener coherencia entre configuración declarada, ejecución, persistencia
   y reporte. Rechazar inconsistencias explícitamente: sin sustituciones
   silenciosas, datos inventados ni fallos presentados como éxito.
3. Registrar por decisión: problema y evidencia, alternativas relevantes,
   solución elegida, justificación técnica/metodológica, impacto de
   compatibilidad o versión y pruebas que la verifican.
4. Proteger identidad de problemas/tratamientos, semillas, presupuestos,
   versiones, métricas y procedencia. Una práctica habitual debe ser además
   adecuada al diseño experimental; no sustituye su justificación.
5. Corregir y verificar antes del lanzamiento y las campañas: ningún bloqueante
   conocido de integridad experimental puede trasladarse a las campañas.
   Añadir regresiones y validar el flujo hasta análisis/informe. R2 corrige
   hallazgos; R3-R7 completan las verificaciones de publicación. Una suite verde
   aislada no declara v2 lista. Toda limitación restante debe quedar explícita
   y evaluada antes de esa declaración; no se promete ausencia absoluta de bugs.
6. Consultar sólo ante decisiones científicas reales con alternativas
   defendibles que cambien fórmulas o significado experimental, retirada de
   capacidades activas, o pérdida/transformación irreversible de datos.
   Resolver y documentar autónomamente las demás correcciones justificadas.

Este mandato no autoriza campañas científicas, commits ni push. Tesis sigue
excluida. La decisión de lanzar y el protocolo de cada campaña conservan sus
puertas de aprobación; no se sustituyen por autonomía de implementación.

**Avance aprobado y verificado — grupo A:** resueltos R1-08/10/12/14/24/26.
Semillas y última réplica limitadas al entero SQLite no negativo; snapshots
anidados protegidos y JSON estricto; PSO/GA de un solo intento incluso tras
fallo; rechazo FIS no finito anterior al clamp; migrador sin propiedad sobre
transacciones ajenas. El usuario aprobó estos contratos explícitamente.
La autorización posterior para los demás grupos se rige por el mandato
anterior; no implica aprobación de cambios científicos o campañas.
Se añadieron nueve pruebas persistentes de regresión en
[test_input_contracts.py](../tests/test_input_contracts.py). La suite completa
aprobó **223 pruebas**; el alcance de publicación R3-R7 sigue pendiente.
Detalle y límites en la
[actualización R2-A del informe](architecture/V2_SRC_AUDIT_R1.md#8-actualización-r2--grupo-a-aprobado-y-corregido).

**Avance bajo mandato general — grupo B:** resueltos R1-11/23/27.
Historial de migraciones validado antes de DDL o cambio a WAL; rechazo de
esquemas futuros/incoherentes y bases no vacías sin historial. Repositorio,
auditoría y exportación exigen esquema actual; un prefijo antiguo válido se
migra sólo en una operación explícita. `audit` abre un archivo existente en
modo de sólo lectura, sin bootstrap/migración ni dependencia del catálogo
instalado, y conserva visibilidad de evidencia confirmada en WAL.
CEC comprueba SHA-256 de los mismos bytes que deserializa, una vez al cargar.
Se añadieron catorce pruebas en
[test_schema_compatibility.py](../tests/test_schema_compatibility.py);
suite completa: **237 pruebas aprobadas**. Decisiones, alternativas y límites
en la [actualización R2-B](architecture/V2_SRC_AUDIT_R1.md#10-actualización-r2--grupo-b-corregido).
No se inventan checksums históricos ni se certifican fórmulas o instalación
limpia con estas verificaciones.

**Avance bajo mandato general — grupo C:** resueltos R1-13/16/17.
La migración 006 separa etiqueta local de tratamiento y clave interna sin
reescribir claves ni referencias anteriores. Dos campañas con las mismas
etiquetas coexisten; CSV conserva etiqueta y clave. Conflictos de óptimo,
dirección o huella en una instancia compartida fallan explícitamente sin
modificarla. PSO y GA comparten formato de hash inicial versionado, conservando
RNG y operaciones científicas. Las huellas históricas no se recalculan ni se
les atribuye formato; las instancias mantienen ID y parámetros en exportación.
El agrupamiento estadístico R1-28 sigue pendiente de F: verificar transporte
de identidad en C no lo resuelve.
Nueve pruebas nuevas en
[test_persisted_identity.py](../tests/test_persisted_identity.py);
suite completa: **246 pruebas aprobadas**, incluida equivalencia
secuencial/paralela por etiqueta local y resultados científicos.
Decisiones, compatibilidad y límites:
[actualización R2-C](architecture/V2_SRC_AUDIT_R1.md#11-actualización-r2--grupo-c-corregido).
El siguiente grupo pendiente tras C era D.

**Avance bajo mandato general — grupo D:** resueltos R1-03/25/31.
GAP/RDP históricos conservan metadatos pero no son seleccionables como cálculo;
`all` sólo incorpora métricas disponibles. Inicio y escrituras exigen que la
versión y definición completa coincidan con el contrato persistido; una
actualización incompatible bloquea la reanudación sin relabel ni downgrade.
Un control compartido de evidencia sirve a cierre, auditoría, exportación y
sellado: rechaza versiones ajenas y observaciones `required` ausentes, según
scope, estado y aplicabilidad. PSO y GA emiten explícitamente objetivo final
observado, también sin trazas; no se fabrica en persistencia.
Catorce pruebas nuevas en
[test_metric_contracts.py](../tests/test_metric_contracts.py); selección
conectada de 92 pruebas y suite completa de **260 pruebas aprobadas**.
No se modificaron fórmulas, versiones de definiciones ni esquema SQLite.
Los fallos post-commit y la completitud de tiempos condicionales siguen en E,
no quedan certificados por el cierre de D. Decisiones y límites:
[actualización R2-D](architecture/V2_SRC_AUDIT_R1.md#12-actualización-r2--grupo-d-corregido).
El siguiente grupo pendiente tras D era E.

**Avance bajo mandato general — grupo E:** resueltos R1-18/19/20/21/22/29.
La migración 007 separa resultado científico confirmado y finalización
operativa: un fallo post-commit queda registrado sin borrar el resultado ni
repetir el optimizador; tiempos seleccionados pendientes/ausentes bloquean
cierre, auditoría, exportación y sello. Los errores de preparación quedan en
réplica/intento con fase explícita en secuencial y en trabajadores.
Runner y repositorio rechazan soluciones de dimensión incorrecta; las trazas
best-so-far deben respetar dirección y coincidir exactamente con resultado/NFE
final. Las exportaciones y sus informes heredan el mismo gate.
El sello exige auditoría integral bajo bloqueo de escritura y no admite
dispensar corrupción mediante waiver. No hay escrituras post-commit tras sello
ni sustitución de objetivo por la API de tiempos. Una cancelación planificada
puede conservar cero intentos; ejecuciones sin ledger son inválidas.
Veintiuna pruebas nuevas en
[test_execution_integrity.py](../tests/test_execution_integrity.py);
suite completa: **281 pruebas aprobadas**. Sin cambios científicos ni RNG.
Compatibilidad histórica explícita: campos nuevos NULL, sin tiempos ni intentos
inventados; no existe reparación automática de finalización fallida.
Decisiones, evidencia y límites:
[actualización R2-E](architecture/V2_SRC_AUDIT_R1.md#13-actualización-r2--grupo-e-corregido).
El siguiente grupo pendiente es F: identidad de agrupamiento y superficies
analíticas. G y las puertas de lanzamiento R3-R7 permanecen abiertos.

**Avance bajo mandato general — grupo F:** resuelto R1-28; propagación de
R1-29 a todo el bundle analítico verificada. La identidad completa de instancia
(ID local, definición y huella semántica versionada) se conserva en descriptivos,
pareado/Wilcoxon, cobertura y convergencia, bloques Friedman/Nemenyi y rangos.
Los rangos enumeran las instancias disponibles y efectivamente clasificadas.
Las figuras separan variantes por identidad, no sólo por etiquetas.
Entradas sin ID/parámetros explícitos o con metadatos contradictorios fallan;
no se inventan IDs ni se deduplican bases por huellas coincidentes.
Informe/manifiestos de tablas y figuras pasan al esquema 4; regenerar desde
SQLite, sin reinterpretar artefactos antiguos. No cambia el esquema SQLite ni
la configuración científica, fórmulas o protocolo de multiplicidad.
Dieciséis pruebas nuevas en
[test_analysis_identity.py](../tests/test_analysis_identity.py);
suite completa: **297 pruebas aprobadas**.
Decisiones, compatibilidad y evidencia:
[actualización R2-F](architecture/V2_SRC_AUDIT_R1.md#14-actualización-r2--grupo-f-corregido).
El siguiente grupo pendiente es G; R3-R7 y el lanzamiento siguen abiertos.

**Avance — grupo G y cierre R2:** resueltos 01/02/04/05/06/07/09/15/30.
Tras discutir expresamente las alternativas metodológicas, el usuario aprobó
velocidad PSO por amplitud de dimensión (`domain_width_v1`, optimizador
`2.0.0a1-domain-width`), calendario `linear_endpoints_v1` con extremos efectivos
(T=1 usa máximo), y diversidad `hussain_diversity_v2` sin redondeo interno
(FCS versión 2). Se conservan identidades históricas sin cambiar fórmulas ni
actualizar defaults omitidos. La nueva plantilla técnica declara los tres
contratos y mismo Vmax/NFE entre comparadores.
PSO/GA rechazan evaluaciones infactibles o con violación no nula, sin inventar
penalización/reparación. Helpers posicional/genérico e inyección RNG in-memory
se conservan como API explícita con límites, no como soporte forzado a legacy.
Pareado sigue como API baseline/candidato, no inferencia automática del informe.
README y guías conectadas actualizados sin prometer instalación limpia o CI.
Trece pruebas nuevas en
[test_release_contracts.py](../tests/test_release_contracts.py);
suite completa: **310 pruebas aprobadas**, incluido replay científico
secuencial/paralelo de las nuevas variantes y rechazo persistido de restricciones.
Decisiones/compatibilidad:
[actualización R2-G](architecture/V2_SRC_AUDIT_R1.md#15-actualización-r2--grupo-g-y-cierre-r2).
Al cerrar G, la siguiente puerta era **R3, artefactos e instalación limpia**;
su ejecución y cierre se registran a continuación.
Sin campañas científicas, commits ni push; Tesis permanece excluida.

**Cierre R2:** pruebas focalizadas y regresión completa aprobadas; sin hallazgos
bloqueantes abiertos. Los diferidos tienen motivo, impacto y condición de
reapertura documentados. No ocultar fallos mediante defaults o exclusiones.

### R3 — Probar lo que realmente se distribuirá

Construir wheel y sdist con herramientas de empaquetado. Inspeccionar que
incluyen los módulos, dataset/licencia CEC2017, métricas y migraciones necesarios,
y que no arrastran bases, resultados, entornos, Tesis o material de archivo no
aprobado. No asumir que la selección del wheel garantiza el contenido del sdist.

Instalar los artefactos sin modo editable en un entorno temporal nuevo y ejecutar
desde fuera del repositorio, sin `PYTHONPATH` ni imports accidentales del workspace.
Verificar núcleo NumPy y extras `analysis`/`opfunu`, CLI y errores explícitos al
solicitar capacidades opcionales no instaladas.

**Cierre R3:** comandos, entorno, versiones y hashes de artefactos registrados;
instalación y comprobaciones correctas, sin usar bases ni resultados históricos.
No recrear ni actualizar `.venv` para demostrar una instalación limpia.

#### Cierre ejecutado de R3 (9 de noviembre de 2026)

**Decisión:** R3 cerrado para la comprobación local descrita aquí, no para una
matriz de soporte ni para publicación. No se ejecutaron campañas científicas,
no se usaron bases/resultados históricos y no se modificó Tesis. `.venv` se
utilizó sólo como intérprete para crear entornos separados; no se instalaron
ni actualizaron dependencias en ella.

**Defectos reproducidos y correcciones:**

1. El primer sdist incluía las pruebas Python, pero omitía sus CSV de fixtures
   y la configuración que leen. `MANIFEST.in` incorpora explícitamente código,
   pruebas/fixtures y configuración. No incorpora documentación completa,
   Tesis, ARCHIVE, Review, resultados, bases ni entornos. La selección de paquetes
   queda limitada a `afcs` y sus subpaquetes regulares; el wheel usa únicamente
   los recursos de ejecución declarados, no todo el manifiesto del sdist.
2. `afcs[opfunu]` instalado limpiamente no podía importar OPFUNU 1.0.1:
   `ModuleNotFoundError: pkg_resources`. El entorno editable ocultaba el fallo
   porque ya tenía setuptools. El extra declara ahora `setuptools>=68,<82`;
   [setuptools 82 retiró pkg_resources](https://setuptools.pypa.io/en/latest/history.html#v82-0-0).
   No se limita por ello el backend de construcción ni se añade setuptools al
   núcleo. Se conserva visible el warning de obsolescencia de OPFUNU: esta es
   compatibilidad explícita, no una eliminación de su deuda externa.

**Artefactos locales verificados** (no publicados; versión provisional
`2.0.0a0`, sin decidir versión/canal de R7):

| Archivo | Bytes | SHA-256 |
|---|---:|---|
| `afcs-2.0.0a0-py3-none-any.whl` | 2666177 | `f9c2daf41408ac6662ae784bc9d280938110a3f8ca5a11eb156fc6ebce0bf1ce` |
| `afcs-2.0.0a0.tar.gz` | 2710781 | `9a62c83c7969a285ed5859d17890755273c2baaa7979a88914700773559dd027` |

El build PEP 517 aislado generó primero el sdist y después el wheel **desde ese
sdist**. El wheel contiene 71 entradas, de las cuales 66 son archivos de
ejecución del paquete: 56 módulos Python, siete migraciones SQL, catálogo de
métricas, dataset CEC2017 y su licencia. El sdist contiene 134 archivos.
`distribution_contents.py` verifica inventarios exactos, contenido idéntico
al origen, dependencias/entry point y SHA del dataset; por tanto, un archivo
inesperado o la omisión de un fixture hacen fallar la comprobación.
Los hashes identifican estos snapshots; no se afirma construcción bit a bit
reproducible ni se autoriza redistribuirlos por contener una licencia CEC.

**Entorno medido:** Windows 10 build 19045, `win-amd64`, CPython 3.14.4
MSC v.1944. Frontend `build 1.6.1`, `pip 26.0.1`,
`packaging 26.3`, `pyproject_hooks 1.3.3`, `colorama 0.4.6`;
el campo `Generator` del wheel registra setuptools 84.2.1.
El límite de setuptools del extra OPFUNU no aplica al build aislado.

- Instalación núcleo desde wheel: únicamente `afcs 2.0.0a0`, NumPy 2.5.4 y pip.
- Instalación desde sdist con ambos extras: además, OPFUNU 1.0.1,
  setuptools 81.0.0, SciPy 1.18.1, Matplotlib 3.11.2, Pillow 13.0.0,
  requests 2.34.2, contourpy 1.4.0, cycler 0.12.1, fonttools 4.68.0,
  kiwisolver 1.5.1, packaging 26.3, pyparsing 3.3.3,
  python-dateutil 4.0.0, tzdata 2026.6, charset-normalizer 3.5.2,
  idna 3.20, urllib3 2.8.0 y certifi 2026.10.23.
- `pip check` correcto en ambos entornos; instalación no editable y sin acceso
  a los paquetes de `.venv` ni a system-site-packages.

**Comprobaciones ejecutadas:**

- Fuera del checkout, con `PYTHONPATH` eliminado y Python `-I`, se importaron
  los 56 módulos de AFCS y se comprobó que todos proceden del `site-packages`
  del entorno nuevo, no del árbol fuente.
- CEC2017 y CLASSICAL evalúan correctamente con sólo NumPy. Solicitar OPFUNU,
  inferencia SciPy o figuras Matplotlib sin extras produce los errores explícitos
  previstos. Con extras se evaluó también OPFUNU CEC2014 F1 D10.
- CLI instalada: ayuda, preview sin base, plan, run, audit y seal; migraciones
  001–007 y registro de métricas cargados desde el paquete instalado.
- Cada smoke crea y elimina una base temporal: seis corridas técnicas,
  CLASSICAL F1/F2 D2, una réplica, tres políticas PSO, población 4, dos iteraciones
  y **72 NFE en total**. Son fixtures de instalación, sin conclusión inferencial
  ni parámetros de artículo. Con extras se verificó además el pipeline de
  informe/tablas/figuras con reconciliación; sin extras, exportación CSV.
- La suite completa ejecutada desde el sdist extraído aprobó **310 pruebas**.
  Esa suite usa el código fuente del sdist; no se presenta como prueba de imports
  instalados. Los smokes aislados anteriores cubren esa puerta por separado.
- Los dos verificadores nuevos pasan sintaxis y diagnósticos del editor.

**Reproducción en PowerShell** (usar un `$r3` nuevo fuera del checkout; no
recrear `.venv`). Cada comando debe terminar correctamente antes del siguiente:

```powershell
$repo = (Get-Location).Path
$r3 = Join-Path $env:TEMP ('afcs-r3-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $r3 | Out-Null
& "$repo\.venv\Scripts\python.exe" -m venv "$r3\builder"
& "$r3\builder\Scripts\python.exe" -m pip install build
& "$r3\builder\Scripts\python.exe" -m build --outdir "$r3\validated" $repo
& "$r3\builder\Scripts\python.exe" -I "$repo\tests\distribution_contents.py" `
  --source $repo --wheel "$r3\validated\afcs-2.0.0a0-py3-none-any.whl" `
  --sdist "$r3\validated\afcs-2.0.0a0.tar.gz"
& "$repo\.venv\Scripts\python.exe" -m venv "$r3\verified-core"
& "$repo\.venv\Scripts\python.exe" -m venv "$r3\verified-extras"
& "$r3\verified-core\Scripts\python.exe" -m pip install `
  "$r3\validated\afcs-2.0.0a0-py3-none-any.whl"
& "$r3\verified-extras\Scripts\python.exe" -m pip install `
  "$r3\validated\afcs-2.0.0a0.tar.gz[analysis,opfunu]"
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
Set-Location $r3
& "$r3\verified-core\Scripts\python.exe" -I "$repo\tests\distribution_smoke.py" `
  --config "$repo\config\campaigns\classical_pso_recommended_v2.example.json"
& "$r3\verified-extras\Scripts\python.exe" -I "$repo\tests\distribution_smoke.py" `
  --extras --config "$repo\config\campaigns\classical_pso_recommended_v2.example.json"
& "$r3\verified-core\Scripts\python.exe" -m pip check
& "$r3\verified-extras\Scripts\python.exe" -m pip check
& "$r3\builder\Scripts\python.exe" -I -c `
  "import tarfile; tarfile.open(r'$r3\validated\afcs-2.0.0a0.tar.gz').extractall(r'$r3\source', filter='data')"
Set-Location "$r3\source\afcs-2.0.0a0"
& "$r3\verified-extras\Scripts\python.exe" -m unittest discover -s tests -q
Set-Location $repo
```

Los artefactos y evidencia operativa de esta ejecución quedaron en el
directorio de sesión `files\r3-distribution\validated` y sus logs/smokes
adyacentes, fuera del repositorio. Los verificadores y este registro quedan
en el worktree; no hubo commit, push ni publicación.
La siguiente puerta es **R4: herramientas de calidad, matriz de soporte y CI**.

### R4 — Automatizar calidad y soporte

Acordar herramientas de formato, lint y tipos; versionar su configuración y
resolver los errores relevantes sin silenciamientos globales ni reformateos
ajenos al alcance. Definir qué versiones de Python y sistemas se prueban:
`requires-python >=3.11` no equivale a certificar todos los runtimes futuros.

CI debe cubrir instalación limpia, pruebas unitarias, comprobaciones estáticas
y smoke acotado, incluyendo extras y procesos paralelos donde se declaren
soportados. No añadir una plataforma al soporte sólo porque el workflow exista.

**Cierre R4:** workflows ejecutados y verdes en la matriz acordada; no confundir
YAML válido o ejecución local con CI verificada. Si no puede ejecutarse CI,
registrar el bloqueo y mantener la etapa abierta.

#### Implementación de R4 (9 de noviembre de 2026)

**Decisiones aprobadas:** Ruff para lint/formato, Pyright en modo `standard`,
unittest como runner existente; matriz candidata Python 3.11, 3.12, 3.13 y
3.14 en Windows y Ubuntu. Se concretan runners `windows-2022` y
`ubuntu-24.04`, CPython x64 y último patch disponible de cada minor. No se
amplía la certificación a macOS, PyPy, 32 bits ni Python 3.15. El
`requires-python >=3.11` sigue siendo metadato de instalación, no una prueba
de compatibilidad universal. El soporte real debe respaldarse con la matriz
ejecutada y no sólo con su definición.

**Herramientas y alcance:**

- `pyproject.toml` declara el extra `dev`: build 1.6.1, Ruff 0.17.4 y
  Pyright 1.1.414. No cambia las dependencias del núcleo ni las fórmulas
  científicas, identidades de optimizadores, configuración o esquema SQLite.
- Ruff cubre los módulos activos y pruebas: `E4`, `E7`, `E9`, `F` e `I`;
  formato de 88 columnas, sintaxis objetivo 3.11. No se habilita E501 como
  requisito adicional incompatible con el formateador.
- Pyright cubre los 56 módulos de producción, en `standard`, con objetivo
  Python 3.11 y el intérprete explícito del entorno con extras. No se excluyen
  CEC2017 ni los módulos de persistencia/análisis. Las pruebas tienen
  lint/formato y ejecución, no certificación estática de tipos.
- No se añadieron `type: ignore`, `noqa` ni silenciamientos globales. Se
  retiraron imports/variables sin uso, imports estrella de funciones CEC y
  cinco ajustes de `sys.path` en pruebas. Estas últimas requieren instalar
  AFCS; ya no sustituyen silenciosamente el paquete instalado por `src`.
- El formateo inicial queda restringido a `src/afcs` y `tests` (71 archivos
  reformateados en la primera pasada); no se reformatearon Tesis, ARCHIVE ni
  material externo. La normalización de imports se hizo con fixes seguros
  de Ruff, no con reescrituras de fórmulas.

**Línea base y correcciones relevantes:** Ruff encontró inicialmente 121
avisos; 73 archivos necesitaban formato. Pyright detectó 59 errores con las
dependencias de Python 3.14. Se corrigieron con comprobaciones explícitas de
ausencia, tipos de valores normalizados, lectura de campos persistidos
obligatorios y estrechamiento de tipos en límites de NumPy/SciPy/Matplotlib;
no se sustituyeron por defaults silenciosos. La configuración de overlap y
las mismas instancias RNG mantienen su flujo y valores.

El protocolo de políticas expone `compatible_parameters` como capacidad de
lectura, compatible con políticas inmutables; no se convierte esa capacidad
en campo/argumento de las dataclasses. `PSOTraceCollector.observe` conserva
ahora la interfaz neutral de su clase base (población y telemetría PSO
opcionales), sin fabricar métricas ausentes. Dos regresiones nuevas cubren
estos contratos. Pylance verificó siete llamadas de `observe` y dos del
validador de probabilidades; todas compatibles. La suite contiene
**312 pruebas** tras esas adiciones.

**CI preparada:** `.github/workflows/quality.yml` se activa en push, PR o
manualmente, con permisos `contents: read`, límites de tiempo y sin pasos de
publicación. Un job estático ejecuta Ruff y Pyright; ocho celdas construyen y
verifican distribuciones. `tests/distribution_ci.py`:

1. Construye sdist y wheel desde ese sdist con aislamiento PEP 517.
2. Ejecuta el contrato de contenido exacto, recursos, dependencias y dataset.
3. Crea entornos nuevos fuera del checkout, sin `PYTHONPATH`/`PYTHONHOME`.
4. Instala wheel con núcleo y sdist con extras, sin modo editable ni heredar
   paquetes de desarrollo. Python 3.11 puede preinstalar setuptools al crear
   un venv; sólo se permite ese bootstrap adicional, no SciPy/Matplotlib/OPFUNU
   en la comprobación de núcleo.
5. Ejecuta los smokes de instalación con uno y dos trabajadores en cada entorno:
   cuatro fixtures de seis corridas/72 NFE por celda. Comprueba ausencias
   opcionales, procedencia de imports, CLI, auditoría, sello y reconciliación
   analítica con extras.
6. Ejecuta `pip check` y las 312 pruebas desde el sdist extraído con el paquete
   instalado. Retirar los ajustes de `sys.path` evita que la suite importe
   accidentalmente el código fuente del sdist en lugar de la instalación.
7. Elimina entornos/bases temporales y conserva los artefactos locales. No usa
   ni modifica bases/resultados históricos.

El workflow pasó actionlint 1.7.12. Se descargó su binario oficial para Windows
después de comprobar que faltaba, y se verificó SHA-256
`6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9`.
Esto valida estructura/expresiones del workflow, **no ejecuta GitHub Actions**.

**Resultados locales medidos** (Windows 10 build 19045, x64, no confundir con
el runner Windows Server 2022):

| Comprobación | CPython 3.11.9 | CPython 3.14.4 |
|---|---|---|
| Ruff lint y formato | Correctos | Correctos |
| Pyright standard | 0 errores, 0 warnings | 0 errores, 0 warnings |
| Instalación wheel/núcleo y sdist/extras | Correctas | Correctas |
| Smokes aislados, 1 y 2 trabajadores en ambos entornos | 4 aprobados | 4 aprobados |
| `pip check` en ambos entornos | Correcto | Correcto |
| Suite del sdist con paquete instalado | 312 pruebas OK | 312 pruebas OK |

Con 3.11 se resolvieron NumPy 2.4.6 y SciPy 1.17.1; con 3.14, NumPy 2.5.4 y
SciPy 1.18.1. Ambos usaron Matplotlib 3.11.2, OPFUNU 1.0.1 y setuptools 81.0.0.
El smoke registra intérprete, ubicación de imports y versiones completas en
su salida. Se mantuvo visible el warning externo de `pkg_resources`; no se
ocultó para obtener una salida aparentemente limpia. La diferencia de tipos
expuesta por Matplotlib en 3.11 se resolvió conservando únicamente los rangos
no nulos que ya seleccionaba la figura, sin cambiar sus datos.

La ejecución final sobre 3.14 conserva estos snapshots en el directorio de
sesión `files\r4-quality\final-distribution\artifacts`; no reemplazan los
artefactos históricos de R3 ni constituyen una versión publicada:

| Archivo | Bytes | SHA-256 |
|---|---:|---|
| `afcs-2.0.0a0-py3-none-any.whl` | 2668093 | `6ba8ffafe1c3c54fed63f0006a7cdff45a7a3e761f1156491b2b8c914ec0a7ad` |
| `afcs-2.0.0a0.tar.gz` | 2715149 | `ab58e65e79c208ed34a341b0882b295bbd149e6696116a723c5b02d868d6c58a` |

El verificador confirmó 66 recursos de ejecución idénticos al origen,
71 entradas del wheel y 135 archivos del sdist. También se compararon los
66 recursos del wheel probado con 3.11 contra el código de producción final:
sin diferencias. Logs y versiones del entorno quedan junto a los artefactos;
los entornos y archivos intermedios se retiraron tras validar.

**Comandos reproducibles:** desde un entorno separado con
`pip install -e ".[dev,analysis,opfunu]"`, en la raíz:

```powershell
python -m ruff check src\afcs tests
python -m ruff format --check src\afcs tests
python -m pyright --pythonpath (python -c "import sys; print(sys.executable)")
python tests\distribution_ci.py --output (Join-Path $env:TEMP "afcs-r4-local")
```

No ejecutar el último comando con un directorio compartido o con artefactos de
otra versión. La validación no autoriza sobrescribir campañas científicas.
El uso de `.venv` se limitó a lecturas y a crear un entorno separado: sus
dependencias no se actualizaron.

**Estado de cierre:** R4 permanece abierto hasta ejecutar y aprobar la matriz
real de GitHub Actions. Este worktree aún no se ha convertido en commit ni
publicado; el workflow local no puede validar por sí mismo los cambios no
enviados. No se hace commit, push ni ejecución remota sin autorización. Tampoco
se presenta una ejecución Windows local como evidencia de Ubuntu o de Python
3.12/3.13. R5 sigue pendiente.

### R5 — Validar una candidata de extremo a extremo

Usar fixtures/campañas técnicas pequeñas con límites explícitos, no campañas
de artículos. Sobre el paquete instalado verificar:

1. Preview sin escritura y planificación con identidades/semillas completas.
2. PSO, PSO-FCS y GA con presupuestos y métricas previstos.
3. Replay secuencial/paralelo de resultados científicos; los tiempos no tienen
   obligación de coincidencia.
4. Fallos e interrupciones con intentos preservados y recuperación justificada;
   cancelación, sellado y auditoría sin reparación silenciosa.
5. Exportación, informe, tablas y figuras cuando corresponda, con reconciliación
   contra SQLite y detección de artefactos alterados.

**Cierre R5:** resultados esperados medidos, no sólo salida cero del comando;
sin inconsistencias de auditoría o reconciliación ni consumo del stack histórico.

### R6 — Cerrar la documentación de uso y extensión

Revisar README, índice, guías de paquete, ejemplos y mensajes CLI. Documentar
instalación por extras, soporte real, flujo completo, recuperación, limitaciones,
contribución y cómo extender problemas/optimizadores sin duplicar autoridades.
Distinguir API operativa, archivo futuro y propuestas científicas.

**Cierre R6:** comandos comprobados contra la candidata, enlaces válidos y
afirmaciones de soporte respaldadas por R3–R5. No se revisa el contenido de Tesis.

### R7 — Preparar y autorizar la distribución

Decidir licencia general con el usuario; revisar atribuciones y condiciones de
terceros, especialmente código/datos CEC2017 y datasets archivados.
Determinar contenido autorizado para cada canal: repositorio, wheel y sdist.
Excluir datos de un paquete no resuelve su posible publicación en el repositorio.
No elegir una licencia ni afirmar derechos sobre terceros automáticamente.

Definir versión candidata y changelog, API pública y política de compatibilidad
de configuración, esquema SQLite, métricas e identidades científicas. Indicar
si una versión previa se admite, migra explícitamente o rechaza; no prometer
compatibilidad retrospectiva sin pruebas.

**Cierre R7:** checklist de salida completo, artefactos finales identificados,
limitaciones conocidas publicables y aprobación explícita de la candidata.
Crear commits, tags, releases, push o publicar paquetes requiere autorización;
documentar este plan no concede esos permisos.

### Registro de avance

Usar este documento como hoja de ruta y el
[manifiesto](V2_CLEANUP_MANIFEST.md) para decisiones de retirada/conservación.
El [informe R1](architecture/V2_SRC_AUDIT_R1.md) registra el inventario inicial,
siete tandas con treinta y un hallazgos/candidatos y las decisiones todavía
pendientes. Incluye referencias Pylance, reproducciones en memoria y seis
selecciones de pruebas aprobadas (52, 33, 58, 68, 59 y 50, con solapamiento; no se suman
como tests únicos ni son una nueva suite completa).
La segunda tanda revisa contratos, adaptadores y RNG, incluido un fallo
reproducido de semillas aceptadas por preview pero no persistibles en SQLite.
La tercera revisa GA, Mamdani y métricas; reproduce entradas FIS no finitas
aceptadas, hashes iniciales con formatos distintos y acumulación de estado
al reutilizar optimizadores. Incluye 960 comparaciones acotadas dense/sparse
aprobadas; no son certificación exhaustiva.
La cuarta revisa planificación/ejecución y persistencia. Reproduce límites de
identidad, fallos sin evidencia completa, resultado mal dimensionado aceptado,
auditoría de intentos incompleta y escrituras posteriores al sellado. Las pruebas
de recuperación, cancelación, rollback y paralelismo siguen aprobando; no
sustituyen una puerta de integridad antes del sellado.
La quinta contrasta compatibilidad de migraciones, propiedad transaccional,
versiones de métricas, JSON y apertura read-only. Reproduce valores con versión
distinta de la seleccionada, JSON anidado no finito y migración implícita de
bases por el comando `audit`.
La sexta revisa estadística, informe/tablas/figuras y diagnóstico FIS. Reproduce
mezcla de identidades de instancia y convergencia contradictoria que supera
reconciliación; distingue API Wilcoxon/Holm probada de su ausencia en el informe
automático. Al finalizar esa tanda todavía faltaba la consolidación.
La séptima completa la evidencia de snapshots/ausencia obligatoria y consolida
el dictamen: 21 correcciones técnicas/documentales, 7 elecciones de API/alcance
y 3 decisiones matemáticas, no 31 bugs equivalentes. Regresión completa:
**214 pruebas aprobadas**. El informe define bloqueantes propuestos, recomendaciones,
grupos R2 con prerrequisitos y puerta de cierre. No hace falta otra auditoría
general para empezar a decidir; quedan pendientes las aprobaciones.
R1 queda pendiente de cierre decisorio; no se han aplicado correcciones ni
aprobado decisiones metodológicas por el hecho de documentarlas.

En cada etapa registrar fecha, alcance, evidencia, decisiones aprobadas,
pendientes y criterio de cierre. Ante un fallo, corregir y repetir la validación
afectada; si cambia el artefacto candidato, repetir las puertas que dependan
de ese cambio. Mantener regresiones de A–D durante todo el cierre.

El microbenchmark dense/sparse puede conservarse como prueba técnica de costo,
pero no desplaza este orden ni autoriza experimentación de artículos.

## 5. Puerta de salida de plataforma

La plataforma podrá considerarse finiquitada cuando:

- se instale desde cero y su CI esté verde;
- pueda ejecutar en forma secuencial y paralela con replay reproducible;
- recupere interrupciones mediante una política explícita y auditada;
- soporte de forma auditable las familias matemáticas continuas aprobadas y
  cualquier familia continua adicional que se seleccione durante el cierre;
- soporte PSO y GA bajo contratos comunes;
- permita optimizadores con y sin control externo de parámetros;
- persista configuraciones, semillas, resultados y métricas sin reconstrucción
  silenciosa;
- produzca análisis reutilizables desde SQLite sobre fixtures;
- no dependa operativamente del árbol del artículo MDPI;
- no mantenga dos implementaciones autoritativas de una misma capacidad;
- cuente con documentación de usuario y desarrollador coherente con el código.
- tenga cerradas las etapas R1–R7, sin bloqueantes ni afirmaciones de soporte
  no verificadas, y con contenido/licencias de distribución aprobados.

Solo después de esta puerta se congelarán protocolos y se ejecutarán campañas
científicas destinadas a publicaciones.

La puerta anterior no exige actualmente SCP, USCP, KP ni binarización. Esas
capacidades quedan como una fase posterior y no deben introducirse de forma
implícita durante el trabajo con problemas continuos.
