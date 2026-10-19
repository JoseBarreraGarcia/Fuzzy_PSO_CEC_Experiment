# Contexto científico y especificación de implementación para Codex

**Proyecto:** An Adaptive Fuzzy Control System for Metaheuristic Configuration through Dynamic Selection of Fuzzy Schemes  
**Idioma de trabajo:** español (nombres de funciones, variables y código en inglés)  
**Propósito:** documento de conocimiento para un agente que implementa, prueba y evalúa el sistema en Python.  
**Estado:** especificación de investigación, NO declaración de que todos los mecanismos estén implementados o validados.  
**Fuentes primarias:** `thesis_project_proposal.tex`, `thesis_project_methodology.tex`, `thesis_project_theoretical_framework.tex`, `thesis_project_introduccion.tex` y `thesis_project_referencias.bib`. Documentos de revisión complementarios sobre adaptación semántica y particiones difusas.  

## 0. Reglas obligatorias para el agente de programación

1. **Fidelidad:** distinguir siempre entre (A) lo establecido en los documentos doctorales, (B) diseños de implementación sugeridos y (C) decisiones abiertas. No atribuir al proyecto una fórmula o umbral no documentado.
2. **No reemplazar el objeto científico:** el tratamiento experimental principal es la **selección online de esquemas difusos completos o perfiles semánticos predefinidos**, no exclusivamente el ajuste numérico de funciones de pertenencia, ni el entrenamiento de una red neurodifusa.
3. **Control de confusores:** conservar PSO/GA, instancia, presupuesto de evaluaciones, semilla/estado inicial y reglas de inferencia cuando se compare únicamente la estrategia de selección semántica.
4. **Modularidad:** optimizadores, métricas, esquemas, inferencia Mamdani, selectores, problemas y evaluación estadística deben ser módulos independientes e intercambiables.
5. **Reproducibilidad:** guardar configuración completa, versiones, semilla, coste en evaluaciones, estado del selector, trayectorias y resultados por ejecución.
6. **Nada de resultados inventados:** no afirmar mejoras, significación o superioridad antes de ejecutar las comparaciones.
7. **Sin fuga experimental:** políticas Q-learning e hiperheurísticas con entrenamiento no pueden aprender del conjunto final de test y reportarse luego sobre esas mismas instancias como evaluación independiente.
8. **Cambios científicos:** antes de codificar una decisión ambigua, documentar su alternativa y su repercusión en `docs/decisions.md`; si es irreversible o afecta comparabilidad, solicitar validación del investigador.
9. **Implementación incremental:** comenzar con PSO continuo y FIS Mamdani estático reproducible; después añadir biblioteca de esquemas, selectores y GA; al final, extensiones discretas y aplicaciones.
10. **Revisión de fuentes:** la nomenclatura, rango operativo, normalización, reglas y fórmulas de publicaciones previas deben verificarse en su versión definitiva antes de declararlas réplicas exactas.

## 1. Pregunta, hipótesis y contribución

**Pregunta central:** ¿La selección dinámica de esquemas difusos durante la ejecución de una metaheurística mejora su optimización frente a controladores difusos estáticos y ajustes de parámetros fijos?

**Preguntas complementarias:** ¿Qué estrategia de selección (reglas estáticas, estocástica, Q-learning, hiperheurística) funciona mejor? ¿Qué efecto tiene la optimización/aprendizaje del sistema sobre el control online de parámetros?

**Hipótesis documental:** integrar un sistema de control difuso adaptativo que seleccione dinámicamente entre esquemas predefinidos, guiado por métricas de búsqueda, mejorará significativamente efectividad, eficiencia, robustez y equilibrio exploración-explotación respecto de configuraciones fijas.

**Contribución conceptual:** separar dos niveles:

- **Nivel inferior (parameter-level adaptation):** FIS Mamdani produce online un parámetro del optimizador, inicialmente inercia `w` en PSO y tasa de mutación `mu` en GA.
- **Nivel superior (semantic-level adaptation):** un selector decide cuál esquema difuso `S_t` debe utilizar el FIS según métricas observadas. El esquema determina las funciones de pertenencia, tipos, formas, cantidad, soporte, cobertura y solapamiento. El FIS sigue un ciclo Mamdani.

La distinción científica fundamental es comparar **adaptación semántica** contra **adaptación de parámetros bajo semántica fija**; el sistema no debe confundirse con un PSO que simplemente varía `w`.

## 2. Modelo matemático conceptual

Sea `X_t` la población, `f` la función objetivo y `m_t = MetricExtractor(X_t, fitness_history, t, T)` el vector de indicadores calculado en la iteración `t`.

- Biblioteca finita de esquemas: `S = {S_1, ..., S_K}`.
- Selector superior: `k_t = Selector(m_t, history, k_(t-1), selector_state)`.
- Semántica activa: `S_t = S[k_t]`.
- Inferencia inferior: `u_t = Mamdani(m_t, S_t, RuleBase, output_config)`.
- Parámetro operativo: `theta_t = MapOutput(u_t, parameter_bounds)`.
- Transición de búsqueda: `X_(t+1) = MetaheuristicStep(X_t, theta_t, rng)`.

**Secuencia causal requerida:** calcular estado observable -> decidir esquema -> fuzzificar con el esquema elegido -> inferir/agregar/desfuzzificar -> transformar salida -> actualizar población -> evaluar -> registrar nuevo estado. Nunca usar información futura para decidir `S_t`.

**Cuestión pendiente importante:** los textos también plantean esquemas de granularidad variable (p. ej., 3 frente a 5 etiquetas), pero indican que la base de reglas puede permanecer fija. Cambiar cardinalidad altera las referencias lingüísticas: definir explícitamente un mapeo de etiquetas, una base de reglas compatible por esquema o restringir inicialmente el experimento de reglas fijas a esquemas con igual número de etiquetas. No ejecutar silenciosamente un `3x3` sobre un esquema `5x5`.

## 3. PSO: implementación de referencia

Para partícula `i`, dimensión `j`, iteración `t`:

```text
v[i,j,t+1] = w[t]*v[i,j,t]
             + c1*r1[i,j,t]*(pbest[i,j,t] - x[i,j,t])
             + c2*r2[i,j,t]*(gbest[j,t] - x[i,j,t])
x[i,j,t+1] = x[i,j,t] + v[i,j,t+1]
```

Donde `r1,r2 ~ U(0,1)` y `pbest`, `gbest` reflejan las mejores posiciones observadas hasta `t` (para minimización). Definir explícitamente topología (global/local), actualización síncrona, inicialización, tratamiento de límites de posición, velocidad máxima y uso de vectores aleatorios por partícula/dimensión.

**Tratamiento inicial:** controlar `w_t` con el FIS. Mantener `c1,c2,vmax` constantes y configurables para aislar el efecto semántico. Extensión posterior posible a parámetros adicionales; no implementarla como si formara parte del contraste inicial confirmado.

**Punto de partida experimental previo (contexto de trabajos PSO-FCS, no especificación universal de tesis):** `population_size=20`, `iterations=500`, `runs=31`, `w` lineal de `0.9` a `0.1` como comparador, experimentos CEC2017 incluyendo F1/F21/F22/F23 y una configuración de dimensión 100. Estos valores requieren verificación contra el artículo/experimento final específico. En particular, **500 iteraciones × 20 individuos no debe confundirse automáticamente con el presupuesto CEC estándar**. Preferir comparación por número real de evaluaciones `nfe`.

**Mapeo del controlador (diseño parametrizable):** si el FIS produce `u_t in [0,1]`, `w_t = w_min + u_t*(w_max-w_min)`. No asumir límites definitivos de `w` a partir del ejemplo de la comparación sin validarlos.

## 4. GA: interfaz prevista

La propuesta integra GA como segunda metaheurística. El FIS adapta online una tasa de mutación `mu_t`. Mantener fijos selección, cruce, elitismo, codificación y operadores durante la comparación de selectores. La propuesta **no cierra** operadores exactos, representación, tasas, población, mecanismos de reparación ni presupuesto; implementarlos mediante configuración y ADR/documentación. Evitar atribuir una opción de GA concreta a la propuesta.

## 5. Indicadores online del proceso (inputs del control)

Los documentos primarios enumeran cinco indicadores: **diversidad**, **velocidad de convergencia**, **tasa de mejora**, **estancamiento** e **índice de iteración**. No significa que los cinco deban entrar simultáneamente al primer FIS: la elección de entradas es un factor experimental. El punto de partida PSO-FCS previo usa *diversity* e *iteration ratio*.

### 5.1 Progreso temporal

Definición recomendada si `t` son pasos completados y `T` total de pasos: `iteration_ratio_t = t/T` para `t=0,...,T`; garantizar `T>0`, intervalo `[0,1]`, y coherencia entre instante de medición y aplicación del control. **Es propuesta operativa compatible con la formulación documental**, no una referencia a número de ecuación de un paper no incluido.

### 5.2 Diversidad poblacional

La diversidad es una métrica central y debe concordar exactamente con la versión del método de Hussain que se adopte en el artículo base. **No asumir que existe una única normalización canónica.** Definición candidata basada en distancia euclidiana media a la media de la población:

```text
centroid[t,j] = mean_i(x[i,j,t])
D_raw[t] = (1/N) * sum_i sqrt(sum_j (x[i,j,t]-centroid[t,j])^2)
```

Para dimensiones de escalas distintas, registrar además una variante en coordenadas normalizadas `z_ij=(x_ij-lb_j)/(ub_j-lb_j)`; si se necesita `[0,1]`, escoger y documentar una normalización consistente con los límites y con el artículo original. **La expresión anterior es una especificación candidata**, no una transcripción certificada de Hussain. Distinguir `D_raw`, `D_normalized` y métricas de porcentaje de exploración.

Tests: población idéntica -> `D=0`; invariancia por permutación; finitud; comportamiento ante escala de coordenadas; límites de normalización; N=1; ausencia de NaN.

### 5.3 Mejora del fitness

Para minimización, con `b_t = best_so_far_fitness[t]`, candidato:

```text
absolute_improvement[t] = max(0, b[t-1]-b[t])
relative_improvement[t] = max(0,b[t-1]-b[t]) / max(abs(b[t-1]), epsilon)
```

Decidir si usar mejora por iteración o por ventana y cómo tratar óptimos negativos/cercanos a cero. Evitar normalización interproblemas dependiente de resultados del futuro.

### 5.4 Estancamiento

`stagnation_count[t] = 0` si la mejora supera `improvement_tol` y `stagnation_count[t-1]+1` en caso contrario. Variante relativa: `stagnation_ratio = min(count/window, 1)`. Definir la tolerancia y ventana antes de evaluar; registrar ambas. La mejora relevante debe establecerse respecto al mejor global histórico, no al mejor de una única iteración, salvo experimento distinto explícito.

### 5.5 Velocidad de convergencia

La propuesta la menciona sin fijar una única fórmula. Candidatos: pendiente en ventana del mejor fitness, reducción de distancia a un óptimo conocido **solo para evaluación offline** o velocidad relativa de mejora del mejor global. **No utilizar el óptimo de benchmark como entrada del selector** si la arquitectura se pretende agnóstica al problema; reservar ese dato para métricas externas.

### 5.6 Balance exploración-explotación

Separar **diversidad (input)** de **índice de exploración/explotación (salida diagnóstica)**. Una formulación habitual basada en diversidad normalizada por el máximo observado es `exploration[t]=100*D[t]/max_{s<=t}D[s]` y `exploitation[t]=100-exploration[t]`, pero debe verificarse la definición exacta utilizada en Crawford et al. y su orientación/denominador. El máximo **online acumulado** no es intercambiable con el máximo calculado tras finalizar toda la ejecución; el último puede utilizarse solo para análisis retrospectivo, y debe etiquetarse como tal. No asumir que porcentaje de explotación mide directamente el éxito de la búsqueda.

### 5.7 Contrato de métricas

Cada métrica expondrá `name`, `value`, `unit`, `range`, `normalization`, `depends_on`, `sampling_phase` y `validity_flags`. Diferenciar métricas para selector superior, FIS inferior y evaluación posterior. Monitorizar coste de su cálculo.

## 6. FIS Mamdani Tipo-1

**Fundamento documental:** inferencia Mamdani con esquemas de pertenencia alternativos, reglas interpretables y defuzzificación para establecer parámetros. Las fuentes contemplan funciones triangulares, trapezoidales y gaussianas, cardinalidad, forma, cobertura y solapamiento variables.

**Valores por defecto sugeridos, NO fijados en la propuesta:** AND=`min`, implicación=`min`, agregación=`max`, defuzzificación=`centroid` por integración numérica o analítica consistente. Exponer todos en configuración. Definir universos exactos de entrada/salida, discretización, resolución e interpolación de bordes. Mantener la misma malla de integración en todos los métodos al comparar semánticas.

Para función agregada `mu_out(y)`:

```text
u = integral(y*mu_out(y) dy) / integral(mu_out(y) dy)
```

Cuando el denominador es cero, **no devolver NaN ni un valor oculto**: establecer política documentada (parámetro previo, centro neutro u otra), registrar incidente y probarla. Comprobar dominios y saturación. `u` puede ser salida normalizada o física según esquema; estandarizar interfaz.

**Validez/interpretabilidad de esquemas:** cobertura `max_k mu_k(x)>0` sobre la rejilla; normalidad `max_x mu_k(x)≈1` cuando sea un requisito; orden semántico de centros; no duplicidad; límites y solapamiento controlados. La partición Ruspini `sum_k mu_k(x)=1` es una propiedad **opcional más fuerte**, no una obligación de todas las particiones ni de funciones gaussianas arbitrarias. Reportar grado de cumplimiento según el diseño seleccionado.

**Contrato:** `FuzzyScheme(id, input_partitions, output_partition?, semantic_labels, rule_mapping, metadata)`. Especificar si el esquema modifica únicamente antecedentes o también consecuentes; la propuesta enfatiza entradas pero el marco teórico contempla variabilidad semántica mayor. **No variar ambos lados sin identificar el factor**, pues pierde interpretabilidad causal.

### 6.1 Biblioteca experimental mínima propuesta

- `S_tri_3`: tres etiquetas, membresías triangulares, cobertura completa.
- `S_trap_3`: tres etiquetas, trapezoidales con diferente anchura de transición.
- `S_gauss_3`: tres etiquetas gaussianas con parámetros validados.
- `S_tri_5`: cinco etiquetas y reglas compatibles, como brazo separado de granularidad.

Los valores numéricos de centros, anchuras y solapamientos **son parámetros experimentales aún por definir**, no generar configuraciones arbitrarias y declararlas definitivas. Versionar cada esquema con archivo YAML/JSON y hash.

## 7. Selector semántico de nivel superior

Interfaz común:

```python
select_scheme(metrics, previous_scheme_id, selector_state, rng) -> SelectionDecision
update(feedback, selector_state) -> selector_state
```

`SelectionDecision` debe incluir `scheme_id`, `reason`, `policy_version`, `score/probability` si aplica, y si hubo cambio.

**Comparadores experimentales definidos en la propuesta:**

1. **Esquema fijo** (control): `k_t=k_0`; permite atribuir el efecto al switching.
2. **Reglas deterministas / static rule-based switching:** usar umbrales de estancamiento, diversidad o progreso; umbrales explícitos, estabilidad temporal, prioridad de reglas, sensibilidad. Distinguir de `fixed_scheme`.
3. **Selección estocástica:** distribución de probabilidades sobre esquemas, que puede basarse en desempeño histórico; definir exploración, actualización, recompensa, manejo de semillas y comparador aleatorio uniforme.
4. **Q-learning:** estados discretizados de las métricas, acciones=esquemas, recompensa asociada a mejora/coste, tabla Q, `alpha`, `gamma`, política `epsilon-greedy`, calendario y política de entrenamiento/test. La propuesta no fija estos hiperparámetros.
5. **Hiperheurística:** esquemas como opciones de bajo nivel; elegir mecanismo de selección y criterio de aceptación/recompensa, diferenciándolo de Q-learning para evitar comparadores prácticamente idénticos.

**Diseño sugerido de switching robusto:** opcionalmente `minimum_dwell_time` y `hysteresis`, explícitos y con ablación, para evitar oscilaciones. Registrar número de cambios, duración de permanencia, histograma de ocupación por esquema, matriz de transiciones, entropía de uso y coste computacional del selector. Estas son **métricas internas complementarias sugeridas**.

**Recompensa sugerida para métodos aprendidos:** mejora del mejor global por evaluación objetiva consumida, normalizada de modo estable y sin introducir conocimiento del test. La definición final, horizonte de crédito, penalización por cambio y protocolo de aprendizaje siguen **abiertos**.

## 8. Métricas de evaluación externas y fórmulas operativas

La propuesta exige **efectividad, eficiencia, robustez y balance exploración-explotación**. Se listan las métricas documentadas junto a expresiones implementables que deben aprobarse en el protocolo.

| Dimensión | Métrica | Cálculo / criterio | Estado |
|---|---|---|---|
| Efectividad | Mejor fitness final | `min f(x)` alcanzado hasta el presupuesto para minimización | Confirmada |
| Efectividad | Error al óptimo | `abs(best_fitness - f_opt)`; error relativo `abs(best-f_opt)/max(abs(f_opt),eps)` si apropiado | Confirmada; fórmula concreta propuesta |
| Efectividad | Tasa de éxito | `successful_runs / total_runs`, éxito si error <= tolerancia preregistrada | Confirmada; umbral pendiente |
| Eficiencia | NFE hasta target | Primer conteo acumulado de evaluaciones que alcanza `f_target` | Confirmada; target pendiente |
| Eficiencia | Tiempo computacional | Tiempo de pared por corrida, además de tiempo del controlador y evaluador | Confirmada; desglose sugerido |
| Robustez | Desviación estándar final | Desviación muestral con `ddof=1` de `best_final` entre corridas | Confirmada |
| Robustez | IQR final | Percentil 75 - percentil 25 entre corridas | Confirmada |
| Balance | Exploration/exploitation ratio | Según definición verificada de la referencia Crawford et al. | Confirmada; fórmula por confirmar |
| Diagnóstico | Curva de convergencia | `best_so_far` vs NFE, no solo vs iteración | Confirmada |
| Diagnóstico | Dinámica semántica | switches, permanencia, transiciones, distribución de esquemas | Sugerida |
| Diagnóstico | Overhead | `(runtime_adaptive-runtime_control)/runtime_control` con cautela por variabilidad | Sugerida |

**Reglas de métrica:**

- Priorizar `best-so-far`, no último fitness sin especificación. En CEC con bias, usar exactamente la definición de `f_opt` de la versión benchmark.
- Cada ejecución produce **una observación independiente por combinación** en el resumen estadístico; las 500 iteraciones dentro de la misma ejecución no son 500 réplicas independientes.
- Para funciones minimizadas, menor fitness/error/tiempo/NFE es mejor; mayor tasa de éxito es mejor. Para `exploration ratio` no hay dirección universal de optimalidad.
- Cuando no se alcanza target: guardar `reached=false`, `nfe_to_target=null`, `nfe_censored=budget`; no imputar tiempo/NFE exitoso ni suprimir fracasos.
- Si el óptimo es 0 o negativo, definir el error relativo o sustituir por error absoluto para evitar comparaciones engañosas.
- NFE debe incluir inicialización, evaluaciones de población, reevaluaciones y reparaciones que llamen al objetivo. Métricas que solo inspeccionan población no añaden NFE.
- Contabilizar independientemente número de evaluaciones, iteraciones y duración; detener por presupuesto homogéneo según comparación.

## 9. Protocolo experimental

### 9.1 Ámbitos previstos en la propuesta

- **Optimización continua:** funciones IEEE CEC; identificar versión, dimensión, límites, sesgo, rotación, archivos auxiliares y condiciones oficiales de benchmark.
- **Optimización combinatoria:** Set Covering Problem y Knapsack Problem.
- **Selección de características:** datos sintéticos y escenarios de clasificación biomédica/educativa.

**Advertencia:** SCP, KP y feature selection binaria necesitan representación y operadores/binarización distintos del PSO continuo. No mezclar rendimiento de binarización y del selector semántico en una sola atribución causal. Antes de esas extensiones, validar la hipótesis en continuo y después realizar ablaciones en discreto.

### 9.2 Diseño de comparadores (matriz sugerida)

Para cada instancia/dimensión/presupuesto/semilla, comparar:

- PSO/GA con parámetro fijo.
- PSO/GA con programación determinista de parámetro (p. ej., inercia lineal).
- PSO/GA + FIS fijo, mismo sistema de inferencia y mismo esquema.
- PSO/GA + FIS + selector determinista.
- PSO/GA + FIS + selector estocástico.
- PSO/GA + FIS + Q-learning.
- PSO/GA + FIS + hiperheurística.

**Ablaciones recomendadas:** tipo MF manteniendo cardinalidad; granularidad manteniendo formas comparables; presencia/ausencia de switching; entradas del selector; penalización por cambio; congelación de base de reglas; ajuste del FIS vs aprendizaje de selector. No afirmar efecto de semantic switching si las reglas, el presupuesto, la semilla u operadores cambian simultáneamente sin control.

### 9.3 Repeticiones, emparejamiento y semillas

El documento formal exige múltiples semillas controladas y propone Friedman y Wilcoxon. Los trabajos experimentales previos emplearon **31 corridas**: usar 31 como configuración inicial razonable, registrando claramente su procedencia, no como imposición general de todos los estudios doctorales.

Para emparejar, reutilizar semilla raíz/estado inicial comparable (misma población inicial y mismos streams base si el algoritmo lo permite), pero **la misma semilla no garantiza trayectorias aleatorias idénticas** cuando las ramas del algoritmo consumen distinta aleatoriedad. Mantener generadores separados para inicialización, operador, selector y ruido del problema; preservar independencia entre réplicas.

### 9.4 Estadística

- Wilcoxon signed-rank para comparaciones pareadas cuando la definición del par es defendible y se conservan diferencias por ejecución/instancia; tratar ceros y empates explícitamente.
- Friedman para ranking de múltiples métodos sobre bloques de problemas/instancias comparables. Los bloques son **problemas independientes**, no cada iteración ni corridas intercambiables agrupadas sin estructura.
- Reportar comparaciones post hoc ajustadas por multiplicidad (p. ej., Holm), tamaños de efecto y estadísticos descriptivos. No llamar `p<0.05` un tamaño de efecto.
- Ofrecer IC bootstrap adecuados a la unidad de replicación, gráficos de convergencia con bandas y análisis por dimensión/familia de problemas.
- Separar tuning/entrenamiento, validación y pruebas finales. Predefinir control de múltiples hipótesis y criterio primario antes de evaluar.

### 9.5 Logs reproducibles

Guardar por corrida:

```text
run_id, experiment_id, problem_id, problem_version, dimension,
algorithm_id, selector_id, scheme_library_version, rule_base_version,
seed_init, seed_operator, seed_selector, config_hash,
iteration, nfe, best_so_far, population_best, population_mean,
diversity_raw, diversity_normalized, iteration_ratio, improvement,
stagnation_count, convergence_speed, exploration, exploitation,
active_scheme_id, switch_event, controller_output, parameter_value,
selector_reward, selector_state_version, controller_elapsed_s,
optimizer_elapsed_s, elapsed_s, termination_reason
```

No serializar arreglos gigantes por iteración salvo modo diagnóstico. Mantener también `summary.csv` (una fila por corrida), `trajectories.parquet`, `config.yaml`, `environment.json` y `events.jsonl`. Esquema exacto de formatos propuesto, no prescrito por la tesis.

## 10. Arquitectura de código propuesta

```text
project/
  pyproject.toml
  README.md
  configs/
    problems/  algorithms/  fuzzy_schemes/  selectors/  experiments/
  src/afcs/
    core/           # Problem, Optimizer, RunContext, RNGStreams, config
    problems/       # CEC, standard continuous, SCP, KP, feature selection
    optimizers/     # PSO, GA, baseline variants
    metrics/        # progress, diversity, stagnation, exploration
    fuzzy/          # membership, partitions, schemes, rules, mamdani
    selectors/      # fixed, rules, stochastic, q_learning, hyperheuristic
    controllers/    # adaptive facade, output mapping, parameter injection
    experiments/    # orchestrator, plans, runner, resumable execution
    evaluation/     # summary metrics, statistics, visualization
    io/             # artifacts, schema validation, provenance
  tests/
    unit/ integration/ regression/ statistical/ reproducibility/
  docs/
    decisions.md
    scientific_specifications.md
    benchmark_provenance.md
  scripts/
    run_experiment.py
    summarize_results.py
```

**Interfaces mínimas (contratos, no código ejecutable):**

```python
Problem.evaluate(position) -> float
Problem.bounds -> (lower, upper)
Optimizer.initialize(problem, rng) -> OptimizerState
Optimizer.step(state, parameter_updates, rng) -> OptimizerState
MetricExtractor.compute(state, history, iteration, budget) -> Metrics
SchemeLibrary.get(scheme_id) -> FuzzyScheme
Selector.select(metrics, selector_state, rng) -> SelectionDecision
MamdaniController.infer(metrics, scheme, rule_base) -> ControlOutput
ParameterMapper.map(control_output, algorithm_config) -> ParameterUpdates
ExperimentRunner.run(config) -> RunResult
Evaluator.summarize(run_results) -> ExperimentReport
```

Preferir `numpy`, `scipy`, `pandas`/`pyarrow`, `pydantic` o `dataclasses`, `pytest`, `matplotlib`, `scikit-posthocs` según necesidad. Usar la librería CEC oficial o implementación validada contra valores de referencia, con versión/licencia registrada. Evitar depender de una biblioteca externa FIS sin pruebas de correspondencia Mamdani.

## 11. Pruebas que Codex debe construir antes de escalar

1. **PSO:** función esfera en dimensión baja con semillas fijas; prueba de `pbest`, `gbest`, límites, signo de minimización y NFE exacto.
2. **Métricas:** diversidad cero en población colapsada, valor esperado en configuraciones simétricas, mejora no negativa del best-so-far, estancamiento monotónico entre mejoras y ratio temporal con extremos correctos.
3. **Pertenencia:** dominios, grados `[0,1]`, continuidad cuando proceda, interpretación ordenada de términos, cobertura y requisitos Ruspini solo cuando aplique.
4. **Mamdani:** reglas simples con salida conocida, activación múltiple, discretización consistente, ausencia de reglas activas y saturación del mapeo de salida.
5. **Switching:** distinto esquema debe alterar memberships y potencialmente salidas, con misma entrada y reglas compatibles; selector fijo debe reproducir FIS estático bit a bit cuando posible.
6. **Reproducibilidad:** misma configuración/semillas -> mismos resultados numéricos dentro de la tolerancia definida; cambio de seed -> no exigir identidad.
7. **Presupuesto:** comparar NFE idéntico en todas las variantes, detectar terminación por presupuesto y corridas con target no alcanzado.
8. **RL:** persistencia de Q-table, congelación de política en test, recompensa sin datos futuros y reinicio entre réplicas cuando corresponde.
9. **Estadística:** datos sintéticos con ranking/pareamiento conocidos; manejo de NaN/censura sin retirar selectivamente casos desfavorables.
10. **Regresión científica:** `golden tests` con resultados confirmados del PSO-FCS previo cuando se disponga del código y valores originales.

## 12. Hoja de ruta de implementación

**Fase 0. Auditoría de fuente:** extraer reglas FIS, funciones de pertenencia y definición exacta de Hussain/exploración de manuscritos consolidados. Crear `docs/decisions.md` con decisiones abiertas y matriz de trazabilidad.

**Fase 1. Núcleo experimental:** benchmark esfera + PSO estándar + PSO inercia fija/lineal + métricas de rendimiento y NFE + reproducibilidad con seeds y logs.

**Fase 2. FIS estático:** replicar Mamdani de 2 entradas, controlar `w` y probar concordancia con los resultados previos disponibles.

**Fase 3. Semántica modular:** biblioteca versionada de esquemas válidos; comparaciones de mismo número de etiquetas y reglas invariantes; después granularidad variable con mapeos de reglas explícitos.

**Fase 4. Selección:** fixed, rule-based, stochastic; log de transiciones y ablaciones.

**Fase 5. Aprendizaje:** Q-learning e hiperheurística, separación entrenamiento/test y comparaciones con presupuesto equitativo.

**Fase 6. Extensión:** GA; CEC completo en dimensiones definidas; problemas combinatorios/feature selection; análisis estadístico e informes.

## 13. Decisiones abiertas y riesgos metodológicos

| Tema | Estado real | Resolución necesaria |
|---|---|---|
| Fórmula exacta Hussain | No transcrita en los archivos de propuesta revisados | Confirmar paper/código y normalización |
| Fórmula exacta exploración-explotación Crawford | Citada, sin ecuación operativa en la propuesta | Recuperar ecuación original |
| Entradas definitivas del FIS | Se ejemplifican diversidad e iteración; propuesta añade otras | Definir modelos primario y ablaciones |
| Reglas Mamdani completas | No formalizadas numéricamente en la metodología resumida | Versionar base de reglas, operadores y salidas |
| Relación esquemas 3 vs 5 etiquetas | Potencial incompatibilidad con reglas fijas | Mapeo o bases de reglas por granularidad |
| Número de esquemas / parámetros MF | No cerrado | Diseñar perfiles semánticos preregistrados |
| Política de fallback sin activación | No cerrada | Definir y testear |
| Umbrales selección determinista | No cerrados | Ajustar en validación, no test |
| Estados/recompensas Q-learning | No cerrados | Diseñar MDP, crédito temporal y protocolo train/test |
| Hiperheurística concreta | No cerrada | Definir mecanismo y diferenciación de Q-learning |
| Presupuesto oficial CEC/instancias | Versión y diseño de tesis abiertos | Elegir conjunto, dimensiones y NFE |
| Operadores/representación GA | No cerrados | Definir antes de implementar |
| SCP/KP binarios y binarización | Fuente adicional de variación | Experimento separado y ablación |
| Número de repeticiones universal | Propuesta dice múltiples; trabajos previos 31 | Prerregistrar N según fase |
| Estadística y comparaciones múltiples | Friedman/Wilcoxon previstos | Definir bloques, ajustes e hipótesis primarias |

## 14. Criterios de aceptación para tareas de Codex

Toda contribución de código debe responder: **qué objetivo científico implementa**, qué fuente o decisión interna la sustenta, qué métricas calcula, qué pruebas automatizadas demuestra, qué semillas/presupuesto usa y cómo reproduce el resultado. No considerar una fase completa hasta disponer de (i) implementación, (ii) tests, (iii) corrida pequeña reproducible, (iv) reporte de resultados, (v) registro de decisiones.

**Próximo paso aconsejado al agente:** inspeccionar el repositorio existente antes de escribir nuevos módulos, construir un mapa código ↔ especificación, identificar las ecuaciones/reglas que ya están programadas y proponer el menor conjunto de cambios para obtener PSO + FIS estático + métrica de diversidad + NFE validados.

## 15. Bibliografía/recursos internos prioritarios

- `thesis_project_proposal.tex`: diseño dual, arquitectura, estrategias y evaluación.
- `thesis_project_methodology.tex`: preguntas, hipótesis y objetivos.
- `thesis_project_theoretical_framework.tex`: sustento conceptual, semántica modular y lógica difusa.
- `thesis_project_introduccion.tex`: problema y justificación.
- `thesis_project_referencias.bib`: citas bibliográficas; verificar correspondencia y DOI antes de reutilizar.
- `Búsquedas para fortalecer el CAPÍTULO MATEMÁTICO.docx`: propiedades de particiones (cobertura, normalidad, distinguibilidad, orden).
- `Modular Fuzzy Semantics, Full Fuzzy Partition Switching, and Meta-Level Controllers Existence and Frameworks.docx`; `Semantic-Level Adaptation in Fuzzy Systems.docx`; `semantic level adaptation.docx`; `GAP.docx`: exploración bibliográfica auxiliar. **No interpretar afirmaciones de ausencia absoluta de trabajos previos como demostraciones de novedad; requieren revisión sistemática contrastada y actualización.**

**Prioridad de autoridad:** manuscrito doctoral explícito > implementaciones/publicaciones experimentales confirmadas para reproducirlas > decisiones aprobadas por el investigador > propuestas técnicas de este archivo > documentos de síntesis bibliográfica.
