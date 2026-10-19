# Hipótesis, métricas y plan de análisis — Paper MDPI

> **Propósito.** Mantener el plan de análisis y su historial de cambios: preguntas de investigación, métricas, procedimientos ejecutados y límites de interpretación. Este documento apoya la auditoría de *Methods*, *Results* y *Discussion*.

> **Pregunta de investigación principal** (ver `03_decisiones_metodologicas.md::D0`): *¿existe una configuración estática del FCS Mamdani (granularidad + reglas) que domine globalmente sobre el Classical Benchmark Suite F1–F23, o el desempeño óptimo depende del tipo de problema?* La respuesta a esta pregunta (sintetizada en **H5**) condiciona la viabilidad de la línea de adaptación semántica de la tesis doctoral.

> **Vocabulario.** Se habla de **"configuración del FCS Mamdani"** ó **"parametrización del FIS"** — una configuración = `(n, R)` con `n ∈ {3,5,7,9}` y `R ∈ {R1,…,R8}`. Los términos *fuzzy scheme* y *AFCS* están reservados para *Discussion / Future Work*.

**Última actualización:** 2026-10-13
**Estado:** análisis ejecutado (63 426 corridas); H3 reanalizado con bloques; p-values exploratorios y validación metodológica independiente pendiente.

> ⚠️ **Cambio de estatus de H1–H5 (decisión D14, 2026-09-24).** En el manuscrito, H1–H5 **no se presentan como hipótesis confirmatorias** sino como **preguntas de investigación estructuradas** que guían la interpretación factorial del experimento. Los criterios de sostener/rechazar que siguen son históricos y no se usan como reglas confirmatorias. En particular, el umbral del 50 % en H4 y el corte $\tau<0.7$ en H5 fueron retirados como criterios de decisión.
>
> *Rather than confirmatory hypotheses, H1--H5 are treated as structured research questions guiding the factorial interpretation of the experiment.*
>
> Además: reportar siempre tamaño de efecto junto al *p*-value y separar explícitamente significancia estadística de relevancia práctica.

> **Auditoría H3 (2026-10-13).** Los resultados antiguos de `code/03_run_factorial_anova.py` ($p_{\mathrm{ANOVA}}=0.1003$, $p_{\mathrm{SRH}}=0.3430$) trataron 61 504 filas como independientes y no se usan. El reanálisis `code/17_reanalyze_h3_blocked.py` preserva los 1 922 bloques `instancia × run_id`; sus p-values de bootstrap son exploratorios. La calibración nula reproducible (500 simulaciones por distribución, 999 bootstraps por simulación) obtuvo tasas de rechazo de 6.0% normal (IC Wilson 4.2--8.4%) y 4.6% t4 (3.1--6.8%); la aproximación Wald F rechazó 72.8--74.8% bajo el nulo y se descarta. H3 se interpreta descriptivamente hasta revisión estadística independiente (ver `01_task_list.md::7.11`).

---

## 1. Variables y notación común

### Factores controlados (del diseño experimental)

| Factor | Niveles | Notación |
|---|---|---|
| Granularidad de la partición | n ∈ {3, 5, 7, 9} | n |
| Patrón de reglas | R ∈ {R1, R2, R3, R4, R5, R6, R7, R8} | R |
| Algoritmo base | {PSO clásico, PSO_FCS(n, R)} | A |
| Función objetivo | F1, …, F23 (Classical Benchmark Suite, Abualigah et al. 2021) | f |
| Dimensión | d ∈ {10, 30, 50, 100} (cuando aplica) | d |

Configuración de un experimento: tupla `(A, n, R, f, d, run_id)`. Para PSO clásico solo `(PSO, f, d, run_id)` (n y R no aplican).

### Métricas primarias (por run)

| Métrica | Definición |
|---|---|
| `fitness_best` | Mejor fitness alcanzado en la corrida (al final de las maxIter) |
| `nfe_to_target` | Número de evaluaciones de fitness para alcanzar `f_opt + ε` (NA si no llega) |
| `t_exec` | Tiempo de ejecución en segundos |

### Métricas secundarias (por iteración, agregadas)

| Métrica | Definición |
|---|---|
| `convergence_auc` | Área bajo la curva `log(fitness − f_opt)` vs iteración |
| `diversity_mean` | Diversidad media de la población a lo largo de la corrida |
| `diversity_decay_rate` | Pendiente del decaimiento de diversidad (regresión log-lineal) |
| `w_mean`, `w_std` | Media y desviación del peso de inercia a lo largo de la corrida |
| `w_trajectory_entropy` | Entropía de la distribución empírica de `w` (qué tanto explora el FIS el rango [wMin, wMax]) |

### Métricas derivadas (por configuración (n, R, f, d))

| Métrica | Definición |
|---|---|
| `mean_best`, `median_best`, `std_best`, `IQR_best` | Estadísticos de `fitness_best` sobre los 31 runs |
| `success_rate` | % de runs que alcanzan `f_opt + ε` |
| `rank_friedman` | Posición ordinal media sobre el conjunto de funciones (Friedman) |
| `wins_vs_PSO` | # de funciones donde la configuración supera a PSO clásico con p < 0.05 (Wilcoxon) |

---

## 2. Hipótesis de trabajo

### H1 — Granularidad y retornos decrecientes

**Claim.** Aumentar la granularidad `n` mejora la calidad de la solución hasta un punto de retornos decrecientes; después se estabiliza o degrada por exceso de fragmentación de reglas (n² consecuentes, más sensibilidad al ruido inferencial).

**Variables.**
- Factor: `n ∈ {3, 5, 7, 9}`.
- Controles: R fijo (analizar por R), f variado, d variado.
- Respuesta: `mean_best`, `rank_friedman`.

**Test estadístico.**
- **Friedman + post-hoc Nemenyi** sobre `rank_friedman(n)` cruzando todas las funciones × dimensiones.
- Diagrama de **Critical Difference (CD)** para mostrar grupos no significativamente distintos.

**Criterio de rechazo.**
- H1 se sostiene si existe al menos un `n* ∈ {3,5,7,9}` tal que:
  - `n*` está significativamente mejor que `n = 3` (p < 0.05 Nemenyi), y
  - No existe `n' > n*` que mejore significativamente a `n*` (retornos decrecientes).
- H1 se rechaza si la relación es estrictamente monótona (más n siempre mejor) o si no hay diferencias significativas en ningún sentido.

**Hipótesis nula complementaria:** `n` no afecta el desempeño (rankings indistinguibles entre n=3,5,7,9).

---

### H2 — Sensibilidad al patrón de reglas según la naturaleza del problema

**Claim.** El patrón de reglas óptimo depende de la **naturaleza** del problema:
- Funciones unimodales / convexas (F1–F4 del Classical Suite) tienden a favorecer **R1, R5, R6** (progress decreasing → más explotación al final).
- Funciones multimodales (F5–F10) tienden a favorecer **R3, R5, R7** (diversity following → cooperan con la dinámica natural del enjambre).
- Funciones compuestas / híbridas (F11–F23) son más sensibles a la combinación R5/R6/R7/R8 (efectos duales).

**Variables.**
- Factor: `R ∈ {R1, …, R8}`.
- Estratificación: clase del problema {unimodal, multimodal, híbrida, compuesta}.
- Respuesta: `mean_best`, `rank_friedman`.

**Test estadístico.**
- **Heatmap de win rates** (R × f) con tonalidad por `rank_friedman`.
- **Friedman + Nemenyi** por clase de problema (4 tests separados).

**Criterio de rechazo.**
- H2 se sostiene si las matrices de ranking por clase de problema son **estadísticamente distintas** (Kendall's τ entre rankings < 0.5 ó test de homogeneidad rechaza).
- H2 se rechaza si un único R domina en todas las clases.

---

### H3 — Interacción granularidad × reglas

**Claim.** A mayor granularidad `n`, la sensibilidad al patrón de reglas **disminuye** (la inferencia se vuelve más "suave" y absorbe diferencias entre Rk). Equivalentemente: la varianza del desempeño entre R1–R8 es decreciente en n.

**Variables.**
- Factores: `n × R` (4 × 8 = 32 configuraciones).
- Respuesta: `mean_best` agregado sobre f y d.

**Reanálisis bloqueado (2026-10-13).** `code/17_reanalyze_h3_blocked.py` forma 1 922 bloques completos `instancia × run_id` y calcula rangos medios de las 32 configuraciones dentro de cada bloque, asignando rangos promedio a empates. Para cada respuesta (rango y log-gap) calcula 21 contrastes ortogonales de interacción $n\times R$ y un bootstrap cruzado función/run_id de 100 000 réplicas (semilla 20261013). Los resultados ($p_{\mathrm{boot}}=1.10\times10^{-4}$ en rangos; $p_{\mathrm{boot}}=0.352$ en log-gap) son exploratorios, no confirmatorios. La calibración finita se registra en `results/tests/h3_blocked/summary.json`; no valida por sí sola el procedimiento para inferencia.

Descriptivamente, la dispersión de rangos entre reglas por granularidad es 5.80, 5.64, 5.94 y 6.20 para $n=3,5,7,9$ en los bloques run-level, mientras que la figura basada en rankings medianos por instancia muestra 6.78, 6.40, 6.69 y 7.52; ninguna secuencia disminuye monótonamente. La desviación estándar del `gap_median` entre reglas aumenta de 3.99 ($n=3$) a 4.64 ($n=9$). La expectativa direccional original de que la sensibilidad a las reglas disminuye con $n$ no queda respaldada descriptivamente; no se formula una conclusión inferencial hasta revisar el método con asesoría estadística.

**Lectura histórica, no confirmatoria.** La expectativa original era que la dispersión entre reglas disminuyera con $n$. La dispersión del `gap_median` entre reglas aumenta de 3.99 ($n=3$) a 4.64 ($n=9$); el reanálisis detecta cambios de orden relativo, pero no una reducción monótona de sensibilidad ni una interacción en la magnitud del gap.

---

### H4 — PSO_FCS supera a PSO clásico en la mayoría de funciones

**Claim.** Existe al menos una configuración `(n*, R*)` que supera estadísticamente a PSO clásico en **≥ 50% de las funciones × dimensiones** del Classical Benchmark Suite F1–F23.

**Variables.**
- Comparación pareada: PSO_FCS(n*, R*) vs PSO en cada (f, d).
- Respuesta: `fitness_best` distribuido sobre 31 runs.

**Test estadístico.**
- **Wilcoxon signed-rank** pareado (PSO_FCS vs PSO) por cada (f, d), con corrección de Bonferroni para múltiples comparaciones.
- Tabla **wins / ties / losses** y `success_rate` por configuración.

**Reporte adoptado (D14; 2026-10-13).** No se aplica un umbral mayoritario para sostener o rechazar H4. Se reportan victorias/empates/derrotas, comparaciones Wilcoxon con corrección Bonferroni y $A_{12}$, separando significancia y magnitud del efecto.

---

### H5 — Transferibilidad de la configuración estática del FCS  **[PREGUNTA DE INVESTIGACIÓN CENTRAL]**

**Claim.** No existe una sola configuración `(n*, R*)` del FCS Mamdani que sea óptima simultáneamente sobre toda la familia F1–F23 del Classical Benchmark Suite. Equivalentemente: el ranking de configuraciones varía significativamente entre subgrupos del benchmark.

Subgrupos:
- **S1**: F1–F13 (clásicas escalables, dim ∈ {10,30,50,100}).
- **S2**: F14–F23 (compuestas/híbridas, dimensiones fijas).
- Opcionalmente: refinar por modalidad (unimodal F1–F4, multimodal F5–F13, compuesta F21–F23).

**Variables.**
- `rank_friedman` global y por subgrupo.

**Test estadístico.**
- Comparar `argmin(rank_friedman)` global vs por subgrupo.
- **Kendall's τ** entre rankings S1 y S2 (medida de concordancia).
- Test de homogeneidad sobre los rankings (chi-cuadrado o test de Cochran si aplica).

**Reporte adoptado (D14; 2026-10-13).** La concordancia $\tau(S1,S2)$ y los mejores rangos por subconjunto se interpretan descriptivamente; no se aplica el corte $\tau<0.7$ como decisión. La evidencia por función individual también se reporta (D15).

**Implicación para la tesis** (CRUCIAL).
- **Si H5 se sostiene:** la heterogeneidad de óptimos del FCS estático evidencia que un FCS con configuración fija es insuficiente para abordar la variabilidad del benchmark. Este resultado **motiva empíricamente** la línea de investigación posterior de la tesis: diseño de mecanismos que adapten la semántica del FCS al tipo de problema (en la tesis: definición formal de fuzzy schemes + selector dinámico).
- **Si H5 se rechaza:** una sola configuración estática del FCS dominaría globalmente, lo que **debilitaría** la motivación de la tesis y exigiría replantear su propuesta central. (Resultado posible pero improbable según trabajos previos OLA/CLEI/WEA.)

*En la conclusión del paper, esta implicación se redacta como motivación de trabajo futuro sin nombrar AFCS explícitamente — esto se mantiene bajo perfil hasta tener AFCS implementado.*

---

## 2.6 Análisis por función individual  *(añadido 2026-09-24, decisión D15)*

Los cinco bloques anteriores son agregados (global o por clase de problema). Eso **no basta** para sostener la afirmación central del artículo. Se añade un tercer nivel de reporte, obligatorio en la sección de resultados.

**Tabla sintética** (una fila por función, en el cuerpo del artículo):

| Function | Problem type | Best configuration | Best `n` | Best `R` | PSO rank | Best FCS rank | Gain/loss vs PSO | Significant? |
|---|---|---|---|---|---|---|---|---|

**Figura complementaria:** heatmap `configuración × función` con el ranking por celda.

**Material suplementario:** matriz completa de las 33 configuraciones × 62 instancias.

**Preguntas que el lector debe poder responder con este nivel:**
- ¿en qué funciones gana claramente el Fuzzy-PSO?
- ¿en qué funciones el PSO clásico sigue siendo competitivo?
- ¿en qué funciones domina R1?
- ¿en qué funciones cambia el patrón de reglas ganador?
- ¿la ventaja global se distribuye entre muchas funciones o se concentra en unas pocas?

**Fuente de datos:** `results/level3_rankings/ranking_per_instance.csv` y `winners_per_instance.csv` (ya generados).

---

## 2.7 Estructura de la sección de resultados  *(añadido 2026-09-24, ampliado en la 2.ª revisión editorial)*

```text
5. Results

5.1 Global ranking of fuzzy-control configurations
    Friedman / Nemenyi / diagrama CD. Ranking de las 32 configuraciones + PSO.

5.2 Function-level performance                       <- nuevo, depende de 2.6
    Tabla PSO vs best FCS por función. Ranking por función. Heatmap función × configuración.

5.3 Problem-class dependence
    Ranking por clase. Kendall tau entre rankings de clases. Pareto / matriz de transferencia.

5.4 Effect of rule-base structure                    <- nuevo
    Tabla factorial semántica. Mirror-pair analysis. Tamaños de efecto por eje semántico.

5.5 Effect of linguistic granularity                 <- nuevo
    Comparación n = 3,5,7,9 por regla. Retornos decrecientes. Trade-off desempeño / estabilidad / interpretabilidad.

5.6 Robustness and computational overhead           <- nuevo
    Media vs desviación. Win/tie/loss. Overhead de tiempo de ejecución.

5.7 Dynamic behavior of the controller              <- nuevo
    Curvas de convergencia. Trayectorias de diversidad. Trayectorias de w(t).
```

La progresión va de lo agregado a lo desagregado, sigue con los dos factores del diseño (reglas y granularidad) y cierra con la dinámica del controlador, que es lo que explica *cómo* se produce la diferencia y no solo *quién* gana.

**Cadena explicativa que debe quedar visible en 5.4–5.7:**

```text
rule base → control surface → inertia trajectory → convergence behavior → final performance
```

Sin esa cadena, el artículo se lee como una comparación empírica más.

---

## 2.8 Análisis explícitos añadidos en la 2.ª revisión editorial

### Mirror-pair analysis (aislar ejes semánticos de las reglas)

**Verificado en código (D20).** Sobre `make_rule_matrix` y las superficies defuzzificadas, para $n \in \{3,5,7,9\}$ y las 28 combinaciones de R1–R8, solo cuatro pares cumplen la reflexión exacta $i_a + i_b = n-1$, y son los previstos. Además, en la superficie de control se cumple hasta precisión de máquina:

$$w_{R_a}(d,p) + w_{R_b}(d,p) = w_{\min} + w_{\max}$$

Test permanente: `FUZZY/4_verify_fis_properties.py::sección 7`.

**Tipo 1 — pares espejo (inversión semántica completa):**

| Par | Ejes invertidos |
|---|---|
| R1 vs R2 | progreso |
| R3 vs R4 | diversidad |
| R5 vs R8 | progreso **y** diversidad |
| R6 vs R7 | progreso **y** diversidad |

**Tipo 2 — pares de eje único (efecto marginal de un factor):**

| Par | Eje aislado | Contexto fijo |
|---|---|---|
| R5 vs R7 | dirección del progreso | diversidad = following |
| R6 vs R8 | dirección del progreso | diversidad = compensating |
| R5 vs R6 | reacción a la diversidad | progreso = decreasing |
| R7 vs R8 | reacción a la diversidad | progreso = increasing |

⚠️ **R5/R8 y R6/R7 invierten ambos ejes a la vez, de modo que NO aíslan un factor.** Atribuir su diferencia a un solo eje sería incorrecto. Las dos familias de comparación deben reportarse por separado.

Por cada par: funciones con diferencia significativa, ganador, tamaño de efecto e interpretación.

### Tabla factorial semántica de reglas

```text
                    Diversity-following | Diversity-neutral | Diversity-compensating
Progress decreasing        R5                   R1                    R6
Progress neutral           R3                   —                     R4
Progress increasing        R7                   R2                    R8
```

Contenido de cada celda: mean rank, normalized gap mediano, mejor granularidad, comportamiento típico de `w(t)`, clase de problema donde funciona mejor. Objetivo: que R1–R8 no se lean como etiquetas arbitrarias.

### Performance–robustness map

`x` = gap normalizado mediano; `y` = desviación / IQR / coeficiente de variación; color = patrón de reglas; marcador = granularidad; marcador destacado = PSO baseline; paneles por función representativa o clase. Permite distinguir configuraciones que mejoran media y robustez, solo media, solo robustez, o ninguna — información que un ranking oculta.

### Efecto de granularidad por regla

`Rule | Best n | Rank n=3 | Rank n=5 | Rank n=7 | Rank n=9 | Diminishing returns? | Interpretation`. Responde si aumentar `n` mejora una buena regla, empeora una mala, reduce las diferencias entre reglas, sobresegmenta, o mejora estabilidad sin mejorar fitness.

### Trayectorias de `w(t)`

`x` = iteración; `y` = `w` medio o mediano; líneas = R1–R8; paneles = n ∈ {3,5,7,9}. Debe explicar qué reglas inducen exploración temprana y explotación tardía, cuáles mantienen `w` demasiado alto, cuáles lo bajan demasiado pronto, si la granularidad suaviza la trayectoria, y si las mejores reglas reproducen o se apartan del schedule lineal del baseline.

### Cuidados de cálculo

- Con `f* = 0` no usar gap porcentual clásico (división por cero): usar fitness absoluto, gap normalizado alternativo o log-gap.
- Separar mejora estadística de mejora práctica; no declarar *win* sin significancia **y** efecto práctico.
- Los empates estadísticos se reportan como empates.

---

## 3. Diseño experimental (resumen ejecutivo)

| Parámetro | Valor |
|---|---|
| Funciones | F1–F23 (Classical Benchmark Suite, Abualigah et al. 2021) |
| Dimensiones | F1–F13: {10, 30, 50, 100}; F14–F23: fijas (4–20) |
| Configuraciones del FCS (PSO_FCS) | 4 (n) × 8 (R) = **32** |
| Baseline | PSO clásico (1 configuración) |
| Runs independientes | **31** por configuración × función × dimensión |
| Iteraciones por run | 1000 |
| Tamaño de población | 20 |
| Semilla maestra | 42 (semilla por run = `42 × run_id`) |

**Total experimentos full ≈ 63.500** (smoke ≈ 100).

Detalles en `02_setup_experimental.md`.

---

## 4. Tests estadísticos y supuestos

| Test | Cuándo se usa | Supuestos | Alternativa no paramétrica |
|---|---|---|---|
| Wilcoxon signed-rank | Pareado: PSO_FCS vs PSO por (f, d) | Distribución simétrica de diferencias | — (es la alternativa NP) |
| Friedman | Múltiples (≥3) configuraciones sobre múltiples problemas | Bloques pareados | — |
| Nemenyi post-hoc | Tras Friedman significativo | Mismas k muestras por bloque | — |
| Scheirer--Ray--Hare | Análisis de rangos de dos factores para diseños factoriales completamente aleatorizados | Observaciones independientes; diseño factorial balanceado para la descomposición usada | No es alternativa válida para los bloques repetidos de este estudio sin ajustar por ellos |
| Kendall's τ | Concordancia entre rankings | — | — |
| Bonferroni correction | Múltiples comparaciones simultáneas | Conservador | Holm |

**Corrección global por familia de tests:** Bonferroni con `α/m` donde `m` es el número total de tests dentro de cada hipótesis.

**Tamaño de efecto.** Reportar siempre:
- Diferencia mediana (`Δ_median`).
- `Vargha–Delaney A12` para comparaciones pareadas (interpretación: A12 > 0.71 = efecto grande, > 0.64 = mediano, > 0.56 = pequeño).

---

## 5. Visualizaciones obligatorias del paper

| Figura | Propósito | Sección |
|---|---|---|
| Particiones I1/O1 para n=3,5,7,9 | Mostrar el espacio de diseño | Methods |
| Heatmap reglas (R × granularidad) | Mostrar el espacio de patrones | Methods |
| Convergence curves por configuración | Visualizar dinámica | Results — H4 |
| Boxplots `fitness_best` por n (agregado) | H1 — granularidad | Results — H1 |
| CD diagram (Friedman+Nemenyi) por n | H1 — significancia | Results — H1 |
| Heatmap `rank(R, f)` por clase de problema | H2 — interacción problema×regla | Results — H2 |
| `std(R) vs n` plot | H3 — sensibilidad | Results — H3 |
| Tabla wins/ties/losses (mejor config vs PSO) | H4 — efectividad | Results — H4 |
| Comparación rankings S1 vs S2 | H5 — transferibilidad | Discussion — H5 |
| Trayectoria de `w` para 4 configuraciones representativas | Interpretabilidad FIS | Discussion |
| **Tabla por función individual** | Evidencia desagregada (D15) | Results — 5.3 |
| **Heatmap `configuración × función`** | Especialización por paisaje | Results — 5.3 |
| **Curvas de convergencia representativas** | Cómo se gana, no solo quién gana | Results — 5.5 / 5.6 |

### Curvas de convergencia — especificación  *(añadido 2026-09-24)*

El pipeline registra fitness, diversidad, progreso y `w` por iteración (`results/level1_raw/iterations.parquet`), información hoy infrautilizada.

- **Funciones representativas:** F1 o F2 (unimodal), F5 (Rosenbrock, valle estrecho), F9 o F10 (multimodal escalable), F14 o F15 (multimodal fija), F21–F23 (Shekel, deceptiva de baja dimensión).
- **Configuraciones por curva:** PSO clásico, mejor FCS global, mejor FCS para esa clase, y una configuración claramente inferior como contraste.
- **Formato:** mediana del mejor fitness, banda intercuartílica, escala logarítmica cuando corresponda, **misma escala entre configuraciones** para no inducir lecturas visuales engañosas.
- **Objetivo interpretativo:** convergencia temprana, estabilidad final, estancamiento, exploración tardía y sensibilidad a la multimodalidad.

### Reparto cuerpo / suplemento

**Diez elementos obligatorios en el cuerpo** (inventario cerrado en la 2.ª revisión editorial):

1. Tabla de diseño experimental (factores, niveles, ejecuciones, benchmark, dimensiones).
2. Tabla PSO vs best FCS por función (`Function | Dim | Class | Winner | Best FCS | Best n | Best R | Improvement % | Std. reduction % | p-value | Effect size | Overhead %`).
3. Heatmap función × configuración.
4. Ranking global + ranking por clase.
5. Tabla factorial semántica de reglas.
6. Mirror-pair analysis.
7. Efecto de granularidad por regla.
8. Trayectorias de `w(t)`.
9. Curvas de convergencia representativas.
10. Performance–robustness map.

| Cuerpo del artículo | Material suplementario |
|---|---|
| Una figura de particiones | Matrices completas de reglas para cada `n` |
| Una figura de rule bases | Rankings completos de las 32 configuraciones |
| Una figura de superficies de control | Resultados completos por función, instancia y dimensión |
| Los 10 elementos listados arriba | Todas las superficies de control |
| | Todas las curvas de convergencia |
| | Todas las trayectorias de diversidad y de `w(t)` |
| | Tests extendidos (Wilcoxon / Friedman / Nemenyi / Scheirer–Ray–Hare) |
| | CSV procesados, scripts, seeds y configuración experimental |

**Legibilidad del heatmap.** Si las 32 configuraciones lo vuelven ilegible, usar en el cuerpo una versión reducida (mejores configuraciones por regla, por granularidad, top-10 global, o R1–R8 con su mejor `n`) y dejar la matriz completa en el suplemento.

---

## 6. Reproducibilidad

| Elemento | Mecanismo |
|---|---|
| Semillas | `seed = 42 × run_id`, reportadas en CSV |
| Versión de software | `requirements.txt` congelado al inicio de Fase 2 |
| Configuración del FIS | `config/fuzzy_partitions.json` (JSON declarativo) |
| Configuración de experimentos | `config/experiments_mdpi_*.json` |
| Datos crudos | `Resultados/resumen/level1_raw/` (un CSV por run) |
| Datos agregados | `Resultados/resumen/level2_aggregated/` |
| Datos disgregados (rankings) | `Resultados/resumen/level3_disaggregated/` |
| Scripts de análisis | `analysis_modules_cec/` |
| Branch git del paper | `Solver_CEC_Fuzzy_PSO_ARTICULO_MDPI` (tag por release) |

---

## 7. Lo que este documento NO decide (pendiente)

1. **Tamaño exacto de la muestra de runs** (31 = estándar IEEE/CEC, podría ajustarse).
2. **Criterio operacional para `nfe_to_target`** (qué ε se usa).
3. **Reglas de exclusión** de runs anómalos (¿se eliminan outliers?, ¿qué definición?).
4. **Política de presentación de tiempos de ejecución** (¿agregado o por configuración?).

Decisiones a tomar al inicio de Fase 5 con resultados preliminares.

---

## Apéndice — Historial de cambios

| Fecha | Cambio |
|---|---|
| 2026-06-27 | Creación inicial: H1–H5, métricas y plan de análisis. |
| 2026-09-24 | Revisión editorial: H1–H5 pasan a preguntas de investigación (D14); nueva §2.6 análisis por función (D15); nueva §2.7 estructura de resultados; especificación de curvas de convergencia y reparto cuerpo/suplemento. |
| 2026-09-24 (2.ª) | Revisión editorial: se fijaron la estructura de resultados 5.1–5.7, los análisis explicativos y el inventario del cuerpo; las recomendaciones fuente se preservan en `archive/editorial_guidance_sources_20261015/`. |
