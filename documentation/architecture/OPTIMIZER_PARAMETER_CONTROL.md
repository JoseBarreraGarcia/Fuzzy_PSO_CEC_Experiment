# Metaheurísticas y control opcional de parámetros

**Estado:** decisión arquitectónica aprobada; implementación incremental.  
**Fecha:** 22 de octubre de 2026.

## Decisión de transición aprobada

El 22 de octubre de 2026 se autorizó extraer el PSO conservando inicialmente
su matemática histórica bajo la identidad explícita **legacy_ldiw**:

- wMax = 0.9 y wMin = 0.1;
- c1 = c2 = 2;
- calendario lineal histórico por iteración;
- Vmax = 0.1 × límite superior escalar;
- clipping de posición realizado posteriormente por el solver;
- parada histórica por maxIter, registrando el NFE observado.

Esta política existe para regresión y trazabilidad. No es una recomendación
metodológica para campañas nuevas. Cualquier cambio de coeficientes, velocidad,
fronteras o presupuesto se introducirá como configuración/política distinta y
en un cambio separado.

La autorización no incluye corregir GA ni implementar el nuevo protocolo de
semillas.

## 1. Propósito

AFCS debe servir simultáneamente para:

1. ejecutar metaheurísticas sin control adaptativo;
2. comparar políticas de ajuste dentro de una misma metaheurística;
3. aplicar control difuso inicialmente a PSO y después a GA u otros métodos;
4. comparar variantes adaptativas completas sin presentarlas como ablaciones.

El controlador es una capacidad opcional del experimento, no una dependencia
obligatoria de toda metaheurística.

## 2. Separación de responsabilidades

~~~text
ExperimentRunner
├── OptimizationProblem
├── Optimizer
├── ParameterPolicy (opcional)
├── MetricCollector
├── EvaluationBudget
└── ExperimentRepository
~~~

- **Optimizer** implementa la búsqueda y no conoce SQLite.
- **ParameterPolicy** propone cambios usando sólo estado observable.
- **MetricCollector** calcula y registra las métricas seleccionadas.
- **ExperimentRunner** coordina causalidad, presupuesto y persistencia.
- **NoAdaptation** representa explícitamente un tratamiento sin ajuste dinámico.

La configuración inicial y la adaptación durante la ejecución son conceptos
distintos y deben persistirse por separado.

## 3. Modos experimentales

| Modo | Ejemplo | Adaptación durante la corrida |
|---|---|---|
| algoritmo nativo | GA o una MH legacy | sólo la intrínseca del método |
| parámetro fijo | PSO-FIW | ninguna |
| calendario abierto | PSO-LDIW/NDIW | depende de progreso, no de desempeño |
| adaptación por estado | PSO-AIW-SR/AIW-D | usa retroalimentación observable |
| control difuso | PSO-FCS, futuro GA-FCS | FIS propone uno o más parámetros |
| variante completa | APSO, HPSO-TVAC | adaptación inseparable de otros operadores |

Una política de parámetros no convierte automáticamente una variante completa
en una ablación comparable.

## 4. Contratos previstos

### Optimizer

Debe declarar identidad y versión, configuración inicial validada, parámetros
configurables y adaptables, estado observable, consumo exacto de evaluaciones,
resultado y condición terminal. Debe poder ejecutarse sin política externa.

### ParameterPolicy

Recibe una vista de sólo lectura del estado disponible en el instante actual y
devuelve un **ParameterUpdate** explícito. No actualiza directamente partículas,
individuos, la base de datos ni el presupuesto.

Cada política declara:

- metaheurísticas y parámetros compatibles;
- variables observadas necesarias;
- momento de aplicación;
- límites y validación de salida;
- identidad, versión y configuración;
- razón o diagnóstico de cada actualización cuando corresponda.

### SearchState

Contiene un núcleo común: iteración o generación, evaluaciones consumidas y
restantes, progreso, mejor objetivo observado, mejora y estancamiento
disponibles y tiempo transcurrido.

Puede extenderse con vistas específicas, como posiciones, velocidades y tasa
de éxito en PSO, o población y éxito de mutación en GA. Una política sólo puede
solicitar campos declarados y ya observados; no puede utilizar información
futura.

### ParameterUpdate

Debe registrar valores propuestos, política y versión, instante de aplicación,
valores anteriores y efectivos, validación/clipping/rechazo y diagnóstico
opcional.

## 5. Familia PSO para comparaciones controladas

PSO-FIW, PSO-LDIW, PSO-NDIW, PSO-AIW-SR, PSO-AIW-D y PSO-FCS deben compartir
el mismo núcleo PSO. La diferencia autorizada dentro de esta familia es la
política de inercia:

~~~python
w = inertia_policy.compute(state)
~~~

La futura especialización **InertiaPolicy** se construirá sobre
**ParameterPolicy**; no será el contrato general de AFCS.

Para una comparación controlada deben conservarse, salvo decisión metodológica
explícita:

- inicialización y condiciones aleatorias comparables;
- topología;
- c1 y c2;
- actualización de velocidad, posición, pbest y gbest;
- tamaño de enjambre;
- límites de velocidad y tratamiento de fronteras;
- presupuesto de evaluaciones y criterios de parada.

APSO y HPSO-TVAC se registrarán como variantes completas o comparadores externos
porque modifican más elementos que w.

## 6. Extensión a GA y otras metaheurísticas

El contrato general no contiene nombres hardcodeados como w o mutation_rate.
Cada optimizador publica un catálogo de parámetros adaptables. Por ejemplo:

- PSO: w, y eventualmente c1 o c2;
- GA: tasa de mutación o cruce;
- DE: F o CR;
- otras MH: sólo parámetros cuya semántica y aplicación estén definidas.

Las metaheurísticas legacy pueden integrarse primero mediante un adaptador sin
control. Incorporar adaptación será un cambio posterior y probado, no un
requisito para conservarlas o utilizarlas.

## 7. Comparabilidad experimental

El runner debe imponer condiciones comunes mediante NFE, problema, réplica,
instrumentación, persistencia y manejo de fallos. No debe asumir que una
iteración de PSO equivale a una generación de GA.

Se registrarán separadamente los tiempos del evaluador, optimizador, métricas,
política/controlador y total. Esto permite ejecutar una MH sin control sin
cobrarle un coste inexistente y medir el coste añadido por la adaptación.

## 8. Secuencia de implementación

1. [Completado] Auditar PSO, PSO-FCS, GA, runner y consumidores actuales.
2. [Completado] Congelar mediante pruebas el comportamiento relevante de PSO.
3. Definir Optimizer, SearchState, ParameterPolicy y ParameterUpdate.
4. Extraer el núcleo PSO sin cambiar fórmulas ni orden de operaciones.
5. Implementar NoAdaptation, inercia fija y política legacy equivalente.
6. Conectar el runner y persistencia v2.
7. Migrar PSO-FCS como política difusa.
8. Incorporar las otras políticas de w tras aprobar sus fórmulas.
9. Adaptar GA y después inventariar las demás MH legacy.
10. Implementar comparadores completos en módulos separados.

Cada paso requiere regresiones, documentación y un commit independiente.

La auditoría inicial del paso 1 se encuentra en
[LEGACY_OPTIMIZER_AUDIT.md](LEGACY_OPTIMIZER_AUDIT.md).

## 9. Decisiones todavía abiertas

Este documento no aprueba:

- fórmulas concretas de NDIW, AIW-SR, APSO o HPSO-TVAC;
- métricas definitivas de estado para cada controlador;
- límites o políticas de clipping de parámetros;
- política de fronteras o velocidad de PSO;
- protocolo de semillas y subflujos;
- presupuesto de las campañas;
- qué MH legacy se considerarán soportadas.

Estas decisiones deben verificarse, proponerse y aprobarse antes de codificarse.

## 10. Antecedentes de trabajo

- FUZZY/ARTICULO_OVERLAP/variantes_pso_a_considerar
- FUZZY/ARTICULO_OVERLAP/pso_w_analisis.md
- FUZZY/ARTICULO_OVERLAP/Roadmap_Paper_2_Ruspini_Overlap_PSO_FCS_ACTUALIZADO.md
- Tesis/CONTEXTO_TESIS_DOCTORAL_CODEX.md
