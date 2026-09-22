# Hipótesis, métricas y plan de análisis — Paper MDPI

> **Propósito.** Definir antes de generar resultados qué hipótesis se prueban, con qué métricas se cuantifican y con qué tests estadísticos se contrastan. Este documento es la base de la sección *Results* y *Discussion* del manuscrito y la guía operativa para Fase 5.

> **Pregunta de investigación principal** (ver `03_decisiones_metodologicas.md::D0`): *¿existe una configuración estática del FCS Mamdani (granularidad + reglas) que domine globalmente sobre el Classical Benchmark Suite F1–F23, o el desempeño óptimo depende del tipo de problema?* La respuesta a esta pregunta (sintetizada en **H5**) condiciona la viabilidad de la línea de adaptación semántica de la tesis doctoral.

> **Vocabulario.** Se habla de **"configuración del FCS Mamdani"** ó **"parametrización del FIS"** — una configuración = `(n, R)` con `n ∈ {3,5,7,9}` y `R ∈ {R1,…,R8}`. Los términos *fuzzy scheme* y *AFCS* están reservados para *Discussion / Future Work*.

**Última actualización:** 2026-06-27
**Estado:** propuesta inicial. **A revisar/aprobar por el autor antes de Fase 2.**

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

**Test estadístico.**
- **ANOVA de dos vías** (n × R) o, si no se cumplen supuestos, **Scheirer–Ray–Hare** (no paramétrico).
- **Variance partition:** estimar fracción de varianza explicada por n, R y la interacción n×R.
- **Plot:** desviación estándar de `mean_best` entre R1–R8 vs n (esperado: pendiente negativa).

**Criterio de rechazo.**
- H3 se sostiene si:
  - El efecto principal de R es significativo (p < 0.05), y
  - `std(mean_best | R) | n=9 < std(mean_best | R) | n=3` (pendiente negativa en el plot).
- H3 se rechaza si la interacción n×R no es significativa o la pendiente es positiva.

---

### H4 — PSO_FCS supera a PSO clásico en la mayoría de funciones

**Claim.** Existe al menos una configuración `(n*, R*)` que supera estadísticamente a PSO clásico en **≥ 50% de las funciones × dimensiones** del Classical Benchmark Suite F1–F23.

**Variables.**
- Comparación pareada: PSO_FCS(n*, R*) vs PSO en cada (f, d).
- Respuesta: `fitness_best` distribuido sobre 31 runs.

**Test estadístico.**
- **Wilcoxon signed-rank** pareado (PSO_FCS vs PSO) por cada (f, d), con corrección de Bonferroni para múltiples comparaciones.
- Tabla **wins / ties / losses** y `success_rate` por configuración.

**Criterio de rechazo.**
- H4 se sostiene si `wins_vs_PSO(n*, R*) ≥ 0.5 × |F| × |D|` con p_global < 0.05.
- H4 se rechaza si ninguna configuración llega a la mitad del benchmark.

---

### H5 — No existe una configuración estática del FCS óptima global  **[HIPÓTESIS CLAVE DEL PAPER]**

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

**Criterio de rechazo.**
- H5 se sostiene si `(n*, R*)_global ≠ (n*, R*)_S1` o `≠ (n*, R*)_S2`, y `τ(S1, S2) < 0.7`.
- H5 se rechaza si una sola configuración domina en ambos subgrupos.

**Implicación para la tesis** (CRUCIAL).
- **Si H5 se sostiene:** la heterogeneidad de óptimos del FCS estático evidencia que un FCS con configuración fija es insuficiente para abordar la variabilidad del benchmark. Este resultado **motiva empíricamente** la línea de investigación posterior de la tesis: diseño de mecanismos que adapten la semántica del FCS al tipo de problema (en la tesis: definición formal de fuzzy schemes + selector dinámico).
- **Si H5 se rechaza:** una sola configuración estática del FCS dominaría globalmente, lo que **debilitaría** la motivación de la tesis y exigiría replantear su propuesta central. (Resultado posible pero improbable según trabajos previos OLA/CLEI/WEA.)

*En la conclusión del paper, esta implicación se redacta como motivación de trabajo futuro sin nombrar AFCS explícitamente — esto se mantiene bajo perfil hasta tener AFCS implementado.*

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
| Scheirer–Ray–Hare | ANOVA 2 factores no paramétrica | Diseño factorial | — |
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
