# H3: Solicitud de revisión estadística independiente

## Propósito

Solicitamos una revisión metodológica de la interacción entre granularidad del FCS ($n\in\{3,5,7,9\}$) y patrón de reglas ($R\in\{R1,\ldots,R8\}$). El análisis debe determinar qué estimando y unidad experimental son defendibles, y si existe una prueba de interacción con error tipo I calibrado para este diseño. No se presupone que la interacción exista o no exista.

## Diseño y estructura de dependencia

- El benchmark contiene 23 funciones y 62 instancias: F1--F13 tienen cuatro dimensiones cada una; F14--F23 tienen su dimensión fija.
- Se ejecutaron 32 configuraciones FCS y un baseline PSO en cada instancia, con 31 runs por configuración--instancia; el total es 63,426 runs, de los cuales 61,504 corresponden a FCS.
- Cada bloque `instancia x run_id` contiene las 32 configuraciones FCS. El mismo `run_id`/semilla (`seed = 42 x run_id`) se usa entre configuraciones, funciones y dimensiones.
- Las dimensiones están anidadas dentro de 23 funciones. Por ello, los 62 registros de instancia no son necesariamente independientes si la inferencia pretende generalizar más allá de este benchmark.
- H3 se había formulado como una reducción de la sensibilidad entre reglas al aumentar $n$. La dispersión descriptiva entre reglas no decrece monótonamente al pasar de $n=3$ a $n=9$.

## Análisis anteriores y resultados exploratorios

El análisis inicial de 61,504 filas trató los runs como independientes mediante Type-II ANOVA y Scheirer--Ray--Hare. Sus valores ($p=0.1003$ y $p=0.3430$ para la interacción) no se consideran inferencia válida para el diseño bloqueado y no deben reutilizarse como evidencia.

Se implementó un bootstrap pigeonhole cruzado por función y `run_id` sobre 1,922 bloques instancia--run, con 21 contrastes ortogonales de interacción y 100,000 réplicas:

- Dentro del bloque, usando el orden por gap final: $Q=357.64$, $p_{\mathrm{exploratory}}=1.10\times10^{-4}$; el tamaño de efecto reportado ($\eta_p^2=0.0107$) es descriptivo.
- Para el log-gap, el mismo procedimiento dio $Q=93.94$, $p_{\mathrm{exploratory}}=0.352$.
- Una calibración nula interna de 500 simulaciones por distribución (999 bootstraps por simulación) produjo tasas de rechazo bootstrap de 6.0% bajo errores normales (IC Wilson 95%: 4.2--8.4%) y 4.6% bajo errores $t_4$ estandarizados (3.1--6.8%). La aproximación Wald $F$ asociada rechazó 72.8--74.8% y fue descartada. Esta calibración usa distribuciones sintéticas seleccionadas y no demuestra calibración bajo el proceso experimental real.

También se agregaron perfiles por función (23 unidades), promediando las dimensiones de cada función. Un omnibus de contrastes repetidos con ajuste Greenhouse--Geisser dio $p=0.152$ en rangos y $p=0.535$ en log-gap. Una permutación de signos dio $p=0.086$ y $p=0.0029$, respectivamente; sin embargo, 18/21 contrastes de rangos y 15/21 de log-gap tienen asimetría absoluta mayor que 1, lo que cuestiona el supuesto de simetría de esa permutación. Estos resultados tampoco se proponen como confirmatorios.

La discrepancia entre escalas y procedimientos es la razón para solicitar esta revisión. En el manuscrito, H3 se trata actualmente como exploratorio y no se afirma que haya o no haya una interacción general.

## Preguntas para el revisor

1. ¿Cuál debe ser el estimando primario de H3: interacción en la magnitud del normalized gap/log-gap, cambios en el orden relativo de las configuraciones, u otro?
2. ¿Cuál es la unidad independiente apropiada para la inferencia: las 62 instancias, las 23 funciones, los runs emparejados, o una estructura jerárquica que modele estos niveles?
3. ¿Qué prueba/modelo respeta simultáneamente el diseño $4\times8$ de medidas repetidas, el emparejamiento por `run_id`, las dimensiones anidadas en función, los empates y la asimetría observada?
4. ¿Cómo recomienda calibrar el error tipo I con 23 funciones y 31 `run_id` clusters? ¿Qué simulaciones nulas reflejarían razonablemente la dependencia y heterogeneidad del experimento?
5. ¿Conviene retirar los p-values exploratorios del cuerpo del artículo y mantener solo resultados descriptivos, o se puede justificar un procedimiento inferencial alternativo con los datos existentes?
6. ¿Qué formulación de H3 y qué alcance de generalización serían defendibles para el benchmark fijo F1--F23?

## Artefactos reproducibles

- Datos run-level: `results/level1_raw/experiments_meta.parquet`.
- Reanálisis y simulación nula: `code/17_reanalyze_h3_blocked.py`.
- Resultados guardados: `results/tests/h3_blocked/summary.json`.
- Métodos actuales: `manuscript/sections/04_experimental_design.tex`.
- Results actuales: `manuscript/sections/05_results.tex`.


# Sobre H3
# TASK: Final methodological closure of H3

We need to finalize H3 in the manuscript *Sensitivity of Fuzzy-PSO Inertia Control to Linguistic Granularity and Rule-Base Structure*, currently prepared for submission to *Mathematics* (MDPI).

The priority is methodological validity, internal consistency, and a defensible interpretation of the existing evidence. Do not seek statistical significance or introduce additional statistical procedures merely to obtain a conclusive p-value.

## 1. Methodological decision

H3 must be retained as an exploratory research question:

**H3: Does increasing linguistic granularity consistently reduce performance differences among rule-base patterns?**

The objective is to characterize whether the performance differences among R1–R8 become smaller as the number of linguistic labels increases from 3 to 5, 7, and 9.

This question is narrower than testing every possible granularity-by-rule interaction.

The manuscript must not claim that a statistically significant interaction exists or that the interaction has been demonstrated to be absent.

## 2. Verify existing experimental evidence

Use the existing experimental results. Do not rerun PSO.

Relevant files:

- `results/level1_raw/experiments_meta.parquet`
- `code/17_reanalyze_h3_blocked.py`
- `results/tests/h3_blocked/summary.json`
- `manuscript/sections/04_experimental_design.tex`
- `manuscript/sections/05_results.tex`

Before modifying the manuscript:

1. Verify the descriptive dispersion values currently reported for n = 3, 5, 7, and 9.
2. Verify precisely how each dispersion measure was calculated.
3. Distinguish dispersion based on Friedman ranks from dispersion based on normalized fitness gaps.
4. Examine the descriptive pattern at the function level, treating the 23 benchmark functions as the primary grouping units.
5. Account for the fact that F1–F13 contain four dimensional instances while F14–F23 have fixed dimensions.
6. Do not treat the 62 instances or the 61,504 FCS runs as mutually independent observations when interpreting generalization beyond the evaluated benchmark.
7. Check whether the conclusion of non-monotonic dispersion remains valid when dimensions are first aggregated within functions.

Use existing data and scripts whenever possible. Only implement a minimal descriptive calculation if the required summaries are not already available.

Do not replace or overwrite the raw experimental data.

## 3. Statistical interpretation

The previous analyses produced conflicting inferential outcomes:

- Initial ANOVA and Scheirer–Ray–Hare procedures did not adequately represent the blocked experimental design.
- The crossed-cluster bootstrap yielded different results for within-block ranks and log-transformed normalized gap.
- The function-level analyses also depended on the inferential procedure.
- Some sign-permutation assumptions were questionable because of substantial asymmetry.
- The finite-cluster calibration does not establish reliable type I error control for the actual experimental dependence structure.

These limitations prevent a confirmatory conclusion about the general granularity-by-rule interaction.

Therefore:

- Do not reuse the initial ANOVA or Scheirer–Ray–Hare p-values.
- Do not present the exploratory bootstrap p-values as confirmatory evidence.
- Do not interpret non-significant results as evidence that the interaction is absent.
- Do not introduce new inferential tests unless a concrete error in the existing descriptive analysis requires investigation.
- Preserve the existing exploratory analyses and their discordant outcomes in the reproducibility records.
- If relevant, document them concisely in supplementary material, explaining why they are not used for confirmatory inference.

The main manuscript should focus on verified descriptive patterns and their scientific interpretation.

## 4. Required interpretation of H3

Evaluate whether increasing linguistic granularity consistently reduces the observed differences among rule-base patterns.

If confirmed by the data, the principal conclusion should be:

"The observed performance differences among rule-base patterns did not decrease consistently as linguistic granularity increased."

This statement must be explicitly restricted to the evaluated configurations, benchmark functions, and performance measures.

Do not generalize this observation to all Mamdani fuzzy controllers, PSO implementations, or optimization landscapes.

Importantly, distinguish between:

- The observed dispersion among rule patterns.
- Changes in their relative rankings.
- A formal statistical interaction between granularity and rule-base structure.

These concepts are related but not equivalent.

## 5. Update the manuscript consistently

Review and update all references to H3 in:

- Section 4: Experimental Design.
- Section 5: Results, especially the granularity analysis.
- Table 5: Research questions and observed outcomes.
- Section 6: Discussion and limitations.
- Section 7: Conclusions and Future Work.
- Abstract, if necessary.

Requirements:

1. Maintain a consistent definition of H3 throughout the manuscript.
2. Report the dispersion measure, aggregation procedure, and observed values accurately.
3. Explain that H3 is exploratory and descriptive.
4. Avoid unsupported statements about statistical interaction.
5. Avoid presenting the absence of a monotonic decrease as proof of equivalence or absence of interaction.
6. Remove redundant statistical explanations that do not contribute directly to the central research question.
7. Preserve all other experimental results and research questions.

Use concise academic English suitable for *Mathematics*. Avoid generic, repetitive, or unnecessarily elaborate language.

## 6. Scope restrictions

Do not:

- Rerun the optimization experiments.
- Change experimental configurations.
- Modify H1, H2, H4, or H5 beyond necessary consistency adjustments.
- Introduce new benchmark functions.
- Change the original experimental datasets.
- Add further statistical procedures solely to obtain significance.
- Modify unrelated sections.
- Invent missing results or methodological justifications.

If the available data contradict the proposed descriptive interpretation, report the discrepancy rather than forcing the expected conclusion.

## 7. Required deliverables

After completing the analysis and manuscript updates, provide:

**A. Verification summary**

The verified dispersion values, their definitions, aggregation levels, and the observed pattern across granularities.

**B. Methodological decision**

A concise explanation of why H3 is treated descriptively rather than confirmatorily.

**C. Manuscript changes**

List each modified file and summarize precisely what was changed.

**D. Consistency verification**

Confirm that H3 has the same meaning and inferential scope in the methodology, results, discussion, conclusions, abstract, and Table 5.

**E. Remaining limitations**

Identify only unresolved issues that materially affect H3's validity or interpretation.

## Final objective

Close H3 as a coherent, transparent, and methodologically defensible exploratory analysis suitable for a journal manuscript.

The goal is not to demonstrate or reject a general statistical interaction. The goal is to determine whether the existing experiments support a consistent reduction in rule-pattern performance differences as linguistic granularity increases, and to report that finding without exceeding the available evidence.

Una recomendación adicional: pídele al agente que te entregue primero el resumen de verificación de los valores de dispersión y, si no encuentra inconsistencias, que continúe con la edición del manuscrito. Así podrás cerrar H3 en una sola intervención y evitar otro ciclo de pruebas estadísticas sin una justificación científica clara.