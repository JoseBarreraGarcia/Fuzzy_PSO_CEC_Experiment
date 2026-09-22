# OLA 2026 — Estructura de Presentación

**Paper:** *On the Impact of Linguistic Granularity and Fuzzy Semantic Design in Particle Swarm Optimization*
**Autores:** J. Barrera-García, B. Crawford, E. Monfroy, F. Cisternas-Caneo, R. Soto, G. Giachetti
**Fuente única:** `manuscript_OLA2026.tex`
**Duración objetivo:** 15 min charla + 5 min Q&A
**Total de láminas:** 15

---

## Mapa Paper → Láminas

| Sección del paper | Láminas |
|---|---|
| Title / Abstract | 1, 2 |
| Introduction | 3 |
| Related Work | 4 |
| Fuzzy-Controlled PSO Framework | 5–8 |
| Experimental Setup | 9–10 |
| Results and Discussion | 11–13 |
| Conclusions and Future Work | 14 |
| Acknowledgements / Q&A | 15 |

---

## Lámina 1 — Portada

- Título: *On the Impact of Linguistic Granularity and Fuzzy Semantic Design in Particle Swarm Optimization*
- Autores con afiliaciones (PUCV; U. Alcalá; U. Angers, LERIA; UNAB)
- OLA 2026

---

## Lámina 2 — Abstract en una vista

Cuatro bullets directos del abstract:

- El desempeño de PSO controlado por fuzzy depende de decisiones de diseño tratadas como secundarias
- La granularidad lingüística y el diseño de funciones de pertenencia rara vez se analizan explícitamente
- Estudio experimental: esquemas de **3 y 5 etiquetas** bajo lógica de control idéntica (entradas: progreso de iteración + diversidad)
- Hallazgo: el control fuzzy mejora robustez en paisajes multimodales complejos; **no aporta** en problemas unimodales o regulares

---

## Lámina 3 — Introducción / Motivación

- PSO depende del balance exploración–explotación, regulado por la inercia $w$ [Kennedy 1995; Shi 1998]
- Fuzzy control adapta $w$ con descripciones cualitativas del estado de búsqueda [Shi 2001]
- **Problema:** las variantes fuzzy-PSO usan particiones lingüísticas y MFs fijadas *a priori*, sin análisis del diseño semántico
- **Pregunta de investigación:** ¿en qué medida granularidades y configuraciones fuzzy distintas, con la misma lógica, afectan el desempeño en paisajes diferentes?

> Aporte explícito del paper: **no propone un nuevo algoritmo**; aísla y evalúa el efecto del diseño semántico fuzzy.

---

## Lámina 4 — Trabajo Relacionado

Cuatro bloques (un bullet cada uno):

1. **Fuzzy adaptation en PSO:** Shi & Eberhart (2001) – semilla; extensiones de Nobile (2018) FST-PSO, Xia (2022) MIMO fuzzy, Komarudin (2021) fuzzy signatures
2. **Diseño de MFs:** Olivas (2014) – distintas formas producen diferencias estadísticamente significativas con la misma base de reglas; Fierro (2013), Nikolic (2020)
3. **Granularidad lingüística y granular computing:** Huang (2022), Zhang (2022), Zhao (2021) – la resolución semántica no es una transformación neutra
4. **Posicionamiento del paper:** la granularidad rara vez es factor experimental explícito en PSO → este trabajo llena ese hueco

---

## Lámina 5 — PSO Baseline

Ecuaciones (compactas, ec. 1 y 2 del paper):

$$v_i(t+1) = w \cdot v_i(t) + c_1 r_1 (p_i - x_i(t)) + c_2 r_2 (g - x_i(t))$$
$$x_i(t+1) = x_i(t) + v_i(t+1)$$

- Baseline: inercia decreciente lineal **0.9 → 0.1** [Abualigah 2021]
- Resto de parámetros idénticos en todas las variantes (control experimental)

---

## Lámina 6 — Sistema Fuzzy para Adaptar $w$

**Figura central:** `figures/fcs_architecture.JPG`

- Mamdani FIS, **una evaluación por iteración**, a nivel del *swarm*
- Dos entradas normalizadas:
  - Progreso: $t_{\text{progress}} = t / T_{\max}$ (ec. 3)
  - Diversidad: $D(t) = \frac{1}{d}\sum_{k=1}^{d} \frac{\max_i x_{i,k}(t) - \min_i x_{i,k}(t)}{U_k - L_k}$ (ec. 4)
- Salida: $w_t \in [w_{\min}, w_{\max}]$, defuzzificación por **centroide** (ec. 5)

---

## Lámina 7 — Esquemas Lingüísticos Evaluados

**Figura:** `figures/06_input_diversity_comparison_membership_functions.png` + `06_input_progress_comparison_membership_functions.png`

- Dos granularidades: **3 etiquetas** y **5 etiquetas**
- Para cada granularidad, dos configuraciones: **Set A** y **Set B**
- A y B difieren **solo** en forma, solapamiento y posición de las MFs
- Variables lingüísticas, universos de discurso y estructura de reglas → **idénticos**
- MFs **estáticas** durante toda la optimización

> Diseño aísla resolución semántica de la lógica de control.

---

## Lámina 8 — Salida y Base de Reglas

- **Izquierda:** `figures/06_output_w_comparison_membership_functions.png` (MFs de salida para A y B)
- **Derecha:** `figures/04_fuzzy_rules_heatmap_3labels.png` y `04_fuzzy_rules_heatmap_5labels.png`

Mensaje: aumentar la granularidad **refina la superficie de control** preservando la estrategia cualitativa subyacente.

---

## Lámina 9 — Benchmarks (Tabla del paper)

| Función | Tipo | Dim | Óptimo |
|---|---|---|---|
| F1 (Sphere) | Unimodal | 100 | 0.0 |
| F11 (Griewank) | Multimodal regular | 100 | 0.0 |
| F21 (Shekel, $m=5$) | Multimodal rugoso | 4 | −10.1532 |
| F23 (Shekel, $m=10$) | Multimodal rugoso | 4 | −10.5363 |

Implementadas con **Opfunu** [Van Thieu 2024].

---

## Lámina 10 — Protocolo Experimental

| Parámetro | Valor |
|---|---|
| Población | 50 partículas |
| Iteraciones | 500 |
| Runs independientes | 31 |
| Semillas | 42, 43, …, 72 (compartidas entre algoritmos) |
| Hardware | Intel i7 2.8 GHz, 16 GB RAM |
| Implementación | Python 3.11.9, ejecución secuencial CPU |

**Variantes:** PSO baseline + PSO-FCS-{A3, B3, A5, B5}

**Métrica de gap:** $\text{Gap}(\%) = \dfrac{|f_{\text{best}} - f_{\text{opt}}|}{|f_{\text{opt}}|} \times 100$ (ec. 6)

---

## Lámina 11 — Resultados: Tabla Resumen

Tabla del paper (`tab:performance_summary`), resaltando mejor variante por función.

Cifras a leer en voz alta:

| Función | Mejor variante | Mean fitness | Std | Mean Gap |
|---|---|---|---|---|
| F1 | **PSO** | 23.07 | 11.47 | 23.1% |
| F11 | **PSO** | 1.21 | 0.10 | 1.2% |
| F21 | **PSO-FCS-A5** | −7.749 | 1.275 | 23.7% |
| F23 | **PSO-FCS-A3** | −8.203 | 1.419 | 22.1% |

> Las variantes FCS en F1 y F11 producen gaps catastróficos (74,000%+ y 675%): **decirlo abiertamente**.

---

## Lámina 12 — Insight Principal: Es Problem-Dependent

Dos columnas:

| Paisaje suave / regular (F1, F11) | Multimodal rugoso (F21, F23) |
|---|---|
| PSO baseline domina | PSO-FCS domina |
| Adaptación fuzzy interfiere con dinámica eficiente | Adaptación fuzzy mejora media y robustez |
| FCS aumenta el gap drásticamente | FCS reduce std notablemente |
| Tiempo de FCS algo mayor (~12 s vs ~10 s) | Overhead modesto, justificado por la mejora |

Cita textual del paper: *"fuzzy-controlled inertia adaptation is strongly problem-dependent"*.

---

## Lámina 13 — Efecto de Granularidad y Diseño de MFs

- En F1 y F11: **ninguna** configuración (granularidad ni Set A/B) recupera el desempeño de PSO baseline
- En F21 y F23: **5 etiquetas** tienden a leve mejora en gap medio y a veces menor variabilidad
- **Set A vs Set B:** sin ventaja sistemática en ninguna función
- Conclusión del paper: el diseño semántico es un efecto **medible pero secundario**; el factor dominante es **si existe un mecanismo adaptativo** apropiado

---

## Lámina 14 — Conclusiones

Tres conclusiones literales del paper:

1. PSO baseline supera consistentemente a las variantes fuzzy en problemas unimodales o estructuralmente regulares
2. En problemas multimodales complejos, PSO-FCS mejora el desempeño promedio y la robustez (menor gap medio, menor variabilidad)
3. La granularidad lingüística y el diseño de MFs tienen un efecto **medible pero secundario**: ninguna configuración domina universalmente

**Trabajo futuro:**

- Métricas adicionales del proceso de búsqueda
- Mecanismos dinámicos para **seleccionar/adaptar** la configuración fuzzy *online*
- Intersección con Machine Learning para meta-control adaptativo [Karimi 2022]

---

## Lámina 15 — Agradecimientos y Q&A

- ANID Doctorado Nacional **21230203** (F. Cisternas-Caneo)
- ANID Doctorado Nacional **21242516** (J. Barrera-García)
- Contacto: jose.barrera@pucv.cl
- "Preguntas"

---

## Checklist de Verificación de *Claims* (estricto al .tex)

- [ ] Funciones evaluadas: **únicamente** F1, F11, F21, F23
- [ ] Variantes fuzzy: **únicamente** A3, B3, A5, B5 (no C, no D)
- [ ] Iteraciones: **500** | Población: **50** | Runs: **31**
- [ ] Semilla inicial: **42**, incrementada en 1 por run
- [ ] Inercia baseline: **0.9 → 0.1** lineal decreciente
- [ ] Defuzzificación: **centroide**
- [ ] FIS evaluado **una vez por iteración** a nivel swarm
- [ ] Conclusión central: **problem-dependent**, no dominancia universal de FCS
- [ ] Granularidad: efecto **medible pero secundario**
- [ ] Set A vs Set B: sin ventaja sistemática
- [ ] Cifras de la tabla resumen coinciden con `tab:performance_summary`

---

## Sugerencias Visuales

- Una idea por lámina. Si hay dos, dividir.
- Mostrar **literalmente** la tabla del paper en la lámina 11 (no parafrasear cifras).
- En la lámina 12, evitar el sesgo de presentar solo el caso favorable: mencionar explícitamente que FCS *empeora* en F1/F11.
- Backup slides opcionales: (a) reglas 5-label en detalle, (b) histogramas de los 31 runs por función, (c) curvas de convergencia.
