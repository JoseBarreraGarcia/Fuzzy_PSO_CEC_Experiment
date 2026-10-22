# Auditoría de optimizadores y runner heredados

**Estado:** auditoría inicial completada; no autoriza todavía la migración.  
**Fecha:** 22 de octubre de 2026.

## 1. Alcance

Se revisaron:

- Metaheuristics/Codes/PSO.py;
- Metaheuristics/Codes/PSO_FCS.py;
- Metaheuristics/Codes/GA.py;
- Metaheuristics/imports.py;
- Solver/solverBEN.py;
- Solver/solverSCP.py;
- Solver/population/population_BEN.py;
- Solver/population/population_SCP.py;
- 1_0_poblarDB.py y 2_main.py;
- configuraciones experimentales activas.

Esta auditoría describe el comportamiento presente. No declara correctas sus
decisiones metodológicas ni propone reutilizar defectos conocidos.

## 2. Flujo heredado

~~~text
JSON
  → poblar base histórica
  → recuperar experimento por ID
  → reconstruir parámetros desde texto
  → seleccionar solver BEN o SCP/USCP
  → inicializar población y estado especial por nombre de MH
  → despachar función mediante MH_ARG_MAP
  → evaluar, calcular métricas y escribir CSV temporal
  → convertir CSV a binario y persistir en SQLite histórica
~~~

El runner, el solver, el optimizador, las métricas, los archivos temporales y la
persistencia no están separados.

## 3. PSO clásico observado

La implementación usa:

- inercia lineal w = 0.9 - iter × (0.8 / maxIter);
- c1 = c2 = 2;
- Vmax = 0.1 × ub0;
- r1 y r2 matriciales mediante el RNG global de NumPy;
- topología global-best;
- velocidad inicial cero;
- clipping de velocidad antes de actualizar la posición;
- clipping de posición en el solver, antes de evaluar;
- minimización estricta para pbest y gbest.

La población inicial y cada iteración completa consumen una evaluación por
partícula en BEN. Por ello, en la ruta normal, NFE = población ×
(maxIter + 1). El bucle termina por iteraciones, no al alcanzar un presupuesto
NFE.

### Riesgos

- Los parámetros están hardcodeados.
- Vmax depende sólo del primer límite superior y presupone límites compatibles.
- Usa np.random global y no recibe un generador explícito.
- La función no valida formas, finitud, límites ni maxIter.
- La política de inercia está incrustada en la ecuación de movimiento.

## 4. PSO-FCS observado

PSO-FCS conserva la ecuación, c1, c2, clipping de velocidad y actualización de
posición del PSO clásico. Sustituye la política lineal de w por:

1. diversidad de la población antes del movimiento;
2. normalización contra el máximo histórico observado;
3. progreso iter / maxIter;
4. inferencia difusa para obtener w.

El controlador recibe diversidad normalizada y progreso. La función devuelve
también el nuevo máximo histórico de diversidad.

### Riesgos

- Depende directamente de Diversity y de una clase FIS concreta.
- Usa el mismo RNG global de NumPy.
- El máximo de diversidad forma parte de una posición de retorno sobrecargada
  que otros algoritmos usan para posibles mejoras.
- Puede crear localmente otro controlador si w_set no coincide; ese objeto no
  se devuelve al caller, por lo que su historial podría quedar desconectado.
- BEN permite configurar wMin/wMax; la ruta SCP/USCP usa valores por defecto del
  factory salvo cambios externos.
- La diversidad se calcula dentro de PSO-FCS y nuevamente en el solver.

## 5. Acoplamientos del runner

- La identidad del algoritmo se interpreta mediante cadenas como PSO_FCS:A.
- MH_ARG_MAP actúa como contenedor de inyección no tipado.
- Hay ramas especiales por algoritmo tanto en solver como en population.
- solverBEN abre archivos, consulta SQLite, evalúa, calcula métricas, imprime,
  controla iteraciones y persiste.
- El parámetro extra sólo se expande de manera específica para algunas MH.
- Las excepciones generales del runner están comentadas.
- La semilla heredada depende del ID de experimento. Su sustitución permanece
  fuera de este bloque, según la propuesta de semillas.

## 6. Hallazgos de instrumentación

- solverBEN registra correctamente el NFE de la población inicial y de las
  evaluaciones ordinarias.
- El criterio de ejecución continúa siendo maxIter.
- La columna Divj_max posterior a la iteración cero escribe divj_max0 en lugar
  del valor actual divj_max. Este defecto ya estaba identificado y no se corrige
  dentro de la separación del optimizador.
- solverSCP no posee todavía el mismo contador NFE explícito que BEN.
- Los tiempos mezclan coste del optimizador, métricas, controlador y otras
  tareas de la iteración.

## 7. Estado de GA

GA está registrado y puede pasar por la ruta especial SCP/USCP, pero no debe
considerarse todavía una implementación v2 soportada.

Hallazgos:

- selección de los dos mejores según ranking;
- crossover implementado como punto determinado por el parámetro cross, no como
  una probabilidad de aplicar cruce;
- mutación binaria mediante el módulo random global;
- parámetros recibidos en una cadena cros/mut;
- una población impar produce un descendiente menos;
- selectionSort modifica el vector fitness recibido en el lugar, con riesgo de
  romper la correspondencia entre fitness e individuos en selecciones
  posteriores;
- la ruta BEN no incorpora cross y muta a su contexto general, aunque
  MH_ARG_MAP los exige.

Las fórmulas y correcciones de GA deben aprobarse antes de su adaptación.

## 8. Otras metaheurísticas

El dispatcher registra numerosas MH con firmas y retornos heterogéneos. Algunas
evalúan internamente la función objetivo y otras dependen de la evaluación del
solver. Por ello no es seguro envolverlas todas con un único adaptador ciego.

Cada MH deberá clasificarse como:

- candidata a adaptador sin cambios;
- requiere separar evaluaciones internas;
- requiere corrección antes de migrar;
- experimental sin validación suficiente.

No se eliminará ninguna sólo por quedar fuera de la primera integración.

## 9. Invariantes que deben congelarse antes de extraer PSO

- fórmula y orden de operaciones de velocidad;
- matrices r1 y r2 por partícula y dimensión;
- clipping de velocidad y posición;
- inicialización de velocidad, pbest y gbest;
- criterio estricto de mejora;
- momento de observación de diversidad y progreso;
- número de evaluaciones;
- resultado con una secuencia aleatoria controlada.

Las pruebas de caracterización pueden fijar estos puntos sin fijar el mecanismo
heredado de semillas.

## 10. Estrategia de extracción

1. Crear pruebas deterministas de una transición PSO y PSO-FCS.
2. Definir contratos generales sin nombres hardcodeados de parámetros.
3. Extraer la ecuación común a un núcleo PSO.
4. Representar LDIW heredado y FCS como políticas separadas.
5. Mantener un adaptador para los solvers históricos.
6. Introducir un runner en memoria antes de conectarlo a SQLite v2.
7. Corregir defectos de trazas y migrar métricas en commits separados.
8. Auditar GA antes de usarlo como segunda implementación del contrato.

## 11. Decisiones que requieren aprobación

- conservar o cambiar los valores legacy c1 = c2 = 2;
- definición correcta de Vmax para límites no uniformes/asimétricos;
- política de límites de posición;
- compatibilidad numérica exigida tras usar Generator explícito;
- corrección y definición metodológica de GA;
- presupuesto NFE definitivo y relación con maxIter.

## 12. Resolución de transición

Se aprobó una estrategia de compatibilidad primero:

1. conservar c1 = c2 = 2, LDIW 0.9 → 0.1, Vmax y clipping actuales dentro de
   una configuración identificada como legacy_ldiw;
2. demostrar equivalencia antes de proponer mejoras;
3. no presentar legacy_ldiw como baseline recomendado automáticamente;
4. crear políticas nuevas para cualquier cambio metodológico;
5. mantener GA fuera de esta extracción.

Permanecen abiertas las decisiones sobre configuraciones recomendadas para
nuevas campañas.

