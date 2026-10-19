# Task list — Artículo MDPI Mathematics

Checklist accionable. Cada tarea referencia la fase del plan (`00_paper_plan.md`).

## Estado vigente — 2026-10-15

El estudio y el manuscrito final están cerrados para esta etapa: dataset consolidado de 63 426 corridas, 33 configuraciones, 62 instancias y 31 réplicas por grupo; F14 usa pesos canónicos y todas las semillas verificadas son únicas. El artículo (`manuscript/main.pdf`, 62 páginas), el Supplementary Information (43 páginas) y `manuscript/Supplementary_Information_20261015.zip` compilan y se validaron. RQ3 es descriptiva; RQ4 usa Mann–Whitney independiente con Bonferroni y Tabla 11 usa una familia separada con Holm. Las notas fechadas antes del 2026-10-15 son historial de ejecución y no sustituyen los métodos/resultados finales resumidos en `04_hipotesis_metricas_analisis.md`.

## Fase 0 — Carpeta MDPI
- [x] Crear `FUZZY/ARTICULO_MDPI/00_paper_plan.md` (copia canónica del plan)
- [x] Crear `FUZZY/ARTICULO_MDPI/01_task_list.md` (este archivo)
- [x] Crear `FUZZY/ARTICULO_MDPI/02_setup_experimental.md`
- [x] Crear `FUZZY/ARTICULO_MDPI/03_decisiones_metodologicas.md` (log de decisiones D1–D12, citable).
- [x] Crear `FUZZY/ARTICULO_MDPI/04_hipotesis_metricas_analisis.md` (H1–H5, métricas, tests, plan de análisis).

## Fase 1 — Refactor FIS paramétrico
- [x] Crear `config/fuzzy_partitions.json` con esquema 100% paramétrico (sin tripletes hardcoded).
- [x] Crear `FUZZY/fuzzy_controller_auto.py`:
  - [x] `tri(x, a, b, c)` con soporte de hombros.
  - [x] `make_partition_uniform(n, overlap, shoulders)` — generador único para cualquier n.
  - [x] `make_rule_matrix(pattern, n_labels)` — modelo aditivo (identidad si un solo efecto activo; bandas-de-2 si ambos activos).
  - [x] Clase `FuzzyInertiaController_Auto(w_set, num_labels, input_set, rule_set, wMin, wMax)`.
- [x] Modificar `FUZZY/fuzzy_controller_w_3L.py::get_fuzzy_controller`: enruta SIEMPRE a `_Auto` (sistematización total). `_3L`/`_5L` quedan como referencia histórica.
- [x] Crear `FUZZY/4_verify_fis_properties.py`: valida propiedades matemáticas (centros equiespaciados, cobertura, Ruspini iff overlap=1, cardinalidad de reglas, w ∈ [wMin,wMax], determinismo).
- [x] Ejecutar verificación: `python FUZZY/4_verify_fis_properties.py` → **PASS todos los chequeos** (n∈{3,5,7,9} × R1..R8 × overlap∈{0,0.5,1.0} × shoulders∈{T,F}).
- [x] Generar visualización: `python FUZZY/5_visualize_partitions.py` → `FUZZY/plots/partition_{I1,O1}_overview.png`.

**Configuración elegida para la corrida inicial (esquema simétrico con hombros, estándar académico):**
- **I1 (input)**: `scheme=uniform_triangular`, `overlap=1.0` (Ruspini), `shoulders=true`.
  - Centros equiespaciados incluyendo bordes: `c_i = i/(n-1)`.
  - MF[0] hombro izquierdo (a=b=0); MF[n-1] hombro derecho (b=c=1).
  - **Cobertura Ruspini Σμ=1 en TODO [0,1]** → evidencia completa para cualquier valor de diversity/progress, incluidos los bordes.
- **O1 (output)**: idéntico a I1 (mismas fórmulas y `shoulders=true`).
  - Saturación exacta del centroide en wMin y wMax cuando solo MF[0] o MF[n-1] están activas.
- **Esquema simétrico input/output:** justificable en una línea ante revisores (Pedrycz & Gomide 2007, estándar Mamdani).
- **Etiquetas lingüísticas** definidas para n∈{3,5,7,9}:
  - n=7: `very_low, low, medium_low, medium, medium_high, high, very_high`
  - n=9: `very_very_low, very_low, low, medium_low, medium, medium_high, high, very_high, very_very_high`
- **Configurabilidad**: `overlap` y `shoulders` se mantienen parametrizables en el JSON (futuros estudios de sensibilidad).

## Fase 2 — Configuración experimental  *(✅ HECHO; validada)*
- [x] `config/experiments_mdpi_smoke.json` y `config/experiments_mdpi_full.json` existen y cargan como JSON válido.
- [x] El perfil full define 1000 iteraciones, población 20, 31 corridas, F1--F23, 32 variantes FCS y PSO.
- [x] `config/analysis_mdpi.json` existe; los análisis del artículo quedaron implementados en `FUZZY/ARTICULO_MDPI/code/00--16` y sus salidas están en `results/`.

## Fase 3 — Smoke test aislado  *(SUPERSEDIDO)*
- [x] No se registra una corrida aislada de 100 experimentos como fase independiente. El batch full validó la ejecución, almacenamiento y análisis de punta a punta; no se repite un smoke destructivo sobre la BD actual.

## Fase 4 — Batch completo MDPI  *(✅ HECHO; verificado)*
- [x] `experiments_meta.csv` contiene 63 426 corridas, 62 instancias y 33 configuraciones.
- [x] `BD/resultados.db` registra 63 426 experimentos en estado `terminado`.

## Fase 5 — Análisis MDPI  *(✅ CERRADA; paquete final 2026-10-15)*
- [x] RQ1: Friedman/Nemenyi; RQ2/RQ5: rankings y concordancia descriptivos; RQ3: dispersión descriptiva sin prueba de interacción.
- [x] RQ4: 1 984 Mann–Whitney bilaterales sobre muestras independientes, Bonferroni; Tabla 11: familia separada de 1 984 Mann–Whitney con Holm.
- [x] Runtime por razón de medianas independientes; dinámicas y figuras regeneradas con el dataset consolidado.
- [x] Las salidas finales están en `results/final_dataset_20261015/`; H3 factorial/bootstraps históricos no forman parte de la inferencia final.

## Fase 6 — Manuscrito MDPI Mathematics  *(✅ CERRADA; compilado el 2026-10-15)*
## Fase 7 — Consolidación editorial

> Guía editorial vigente: `EDITORIAL_BEST_PRACTICES.md`. Los documentos fuente anteriores se conservan en `archive/editorial_guidance_sources_20261015/`. Decisiones asociadas: `03_decisiones_metodologicas.md::D13–D19`.
> No es necesario ejecutar todo de inmediato; este bloque fija el rumbo y el orden de prioridad.

### Estado y pendientes actuales  *(actualizado 2026-10-15)*

| Prioridad | Tareas |
|---|---|
| **Autor** | Aprobar asignación CRediT y decidir si se añade un depósito público con DOI; el ZIP suplementario actual no es un repositorio público independiente. |
| **Media** | — |
| **Agente/editorial** | No quedan cambios metodológicos o análisis pendientes para la versión final. |

Los análisis finales RQ1–RQ5, las tablas, las figuras, la formalización y los apéndices están producidos. RQ3 es descriptiva: no se usa el bootstrap factorial histórico por `run_id` como evidencia porque los identificadores no son semillas compartidas. RQ4 y Tabla 11 usan pruebas independientes Mann–Whitney con Bonferroni y Holm en familias separadas. No volver a ejecutar el batch.

### 7.1 Análisis por función individual  *(✅ HECHO 2026-09-24 — era el vacío principal)*
- [x] Generador: `code/11_generate_function_level_analysis.py`. Salidas:
  `results/level3_rankings/function_level_{per_instance,per_function}.csv`,
  `manuscript/tables/tab_function_level.tex` (cuerpo, 23 filas),
  `manuscript/tables/tab_function_level_full.tex` (apéndice, 62 filas en 3 partes),
  `manuscript/figures/fig_function_heatmap.{png,pdf}` (62 instancias × 33 configuraciones).
- [x] Tabla del cuerpo: `Fn | Landscape class | Dims | Best FCS | PSO rk | FCS rk | FCS wins | Sig. | A12 | Median OH (%)`.
- [x] Heatmap con la columna del baseline delimitada y separador S1/S2.
- [x] Nomenclatura `FCS-n-Rk` aplicada en la tabla y en la figura (D17).
- [x] Con `f* = 0` no se usa gap porcentual; las instancias con empate total se marcan con guión.
- [x] Redactada la subsección 5.2 con los hallazgos verificados contra los datos.
- **Hallazgos finales:** la mejor configuración FCS rankea por delante de PSO en 50/62 instancias; 32 comparaciones son nominalmente significativas y 17 sobreviven Bonferroni en la familia RQ4;
  PSO rankea por delante en 6 y hay 6 empates; **15 configuraciones FCS distintas** registran al menos una victoria rank-based;
  `FCS-3-R1` aporta 30/50 victorias (28 de 46 en S1). En F16 y F17 todos los gaps normalizados por corrida son cero; F19 tiene 33 gaps no nulos de 1023, aunque todas sus medianas por configuración son cero.
  en F23 el baseline es la mejor opción.
- [x] La tabla por función informa overhead como razón de medianas de muestras independientes; no se empareja por `run_id`.
- [x] La tabla completa de 62 instancias se incluye en el Apéndice A del artículo; el cuerpo conserva la tabla-resumen de 23 funciones y el heatmap de rangos.
- [x] F16, F17 y F19: el empate de medianas de normalized gap se distingue de los valores por corrida. F16 tiene Mann–Whitney nominal $p=0.0419$, pero Bonferroni ajustado $p=1.000$; F23 tiene $p=0.0234$, también no significativo tras Bonferroni.
- [x] F23: se menciona explícitamente que el baseline es la mejor opción, aclarando que la
  diferencia no alcanza significancia ($p = 0.150$, $A_{12} = 0.34$).

### 7.2 Reestructurar la sección de Resultados  *(✅ ESQUELETO Y ANÁLISIS PRINCIPAL HECHOS)*
- [x] La sección 5 tiene siete subsecciones en el orden acordado: global → función → clase → reglas → granularidad → robustez/escalamiento → dinámica.
- [x] 5.1 Global ranking of fuzzy-control configurations (Friedman / Nemenyi / CD).
- [x] 5.2 Function-level performance (tabla de 23 funciones, matriz/apéndice de 62 instancias, heatmap).
- [x] 5.3 Problem-class dependence (ranking por clase, Kendall τ, Pareto S1/S2).
- [x] 5.4 Effect of rule-base structure (grilla semántica, pares espejo y de eje único, tamaños de efecto).
- [x] 5.5 Effect of linguistic granularity (n = 3,5,7,9 por regla, distribución y sensibilidad).
- [x] 5.6 Robustness, dimensional scaling, and computational overhead (Wilcoxon, escalamiento, mapa media–dispersión y overhead paired).
- [x] 5.7 Dynamic behavior of the controller (trayectorias `w(t)`/XPL y convergencia representativa).
- [x] La cadena `rule base → control surface → inertia trajectory → convergence → performance` está enlazada entre 3.4 y 5.4–5.7.

### 7.3 Regla editorial de versión final  *(bloqueante antes de cualquier envío)*
- [x] Auditar `sections/*.tex` y `main.tex` en busca de lenguaje de planificación, placeholders y nombres genéricos; retirar o corregir los hallazgos (2026-10-13).
- [x] Convertir resultados ejecutados a pasado/presente; conservar futuro solo para extensiones reales en Future Work (2026-10-13).
- [x] Reescribir Abstract (180 palabras) y Conclusions/Future Work con resultados verificados y la cautela exploratoria de H3 (2026-10-13).
- [x] Revisar el título y el Abstract contra el estudio factorial y su mensaje; Abstract final estimado en 180 palabras (2026-10-13).

### 7.4 Curvas de convergencia representativas  *(✅ HECHO 2026-09-24; ver resultados en 5.7)*
- [x] Casos: F1-D30, F9-D30, F14-D2 y F23-D4; PSO, `FCS-3-R1`, mejor FCS de la función cuando difiere y `FCS-9-R2` como contraste.
- [x] Mediana e IQR sobre 31 corridas, escala simétrico-logarítmica; fuente procesada en streaming por `code/14_analyze_controller_dynamics.py`.
- [ ] Curvas completas para todas las instancias/configuraciones: decidir si se depositan como datos descargables; no expandir el PDF con miles de paneles.

### 7.5 Reforzar la contribución formal  *(✅ HECHO 2026-09-24 — obligatoria por D16)*
- [x] §3.4 define granularidad, cardinalidad $n^2$, generador, ejes semánticos y simetría especular.
- [x] Tabla de ejes generada desde `config/fuzzy_partitions.json`; Proposición 1 enlazada con §5.4 y §5.7.
- [x] Justificación de granularidades impares y compromiso resolución–interpretabilidad.

### 7.6 Reposicionar el mensaje central
- [x] Alinear Introducción, Abstract y Conclusions con el mensaje central del estudio; la última frase de la Introducción enlaza las secciones mediante `\ref` (2026-10-13).
- [x] Explicitar que los patrones de reglas separan más los rankings globales que la granularidad, que los especialistas observados varían entre subconjuntos y que la evidencia no demuestra una configuración universal; H3 se mantiene exploratorio (2026-10-13).

### 7.7 Limitaciones explícitas
- [x] Declarar: solo MFs triangulares; particiones Ruspini uniformes con shoulders; sin gaussianas/trapezoidales/asimétricas ni barrido de solapamiento; una sola defuzzificación; `c1` y `c2` fijos; límite de velocidad, población y presupuesto de 1000 iteraciones fijos; un solo baseline; benchmark clásico sin desplazamientos/rotaciones; sin selector adaptativo.
- [x] Presentarlas como controles que aíslan granularidad y estructura de reglas, no como fallos del diseño.

### 7.8 Nomenclatura única  *(✅ HECHO 2026-09-24)*
- [x] Taxonomía de funciones unificada: clases de paisaje = unimodal F1--F7 / scalable multimodal
  F8--F13 / fixed-dimensional multimodal F14--F23; subconjuntos S1 = F1--F13 (scalable) y
  S2 = F14--F23 (fixed-dimensional), descritos por régimen dimensional y **no** como unimodal vs multimodal.
- [x] Módulo compartido `code/_naming.py` con `short_name()` y las etiquetas de clase; importado por los
  scripts 06, 07 y 11. Una sola fuente de verdad para la nomenclatura.
- [x] Regenerados con `FCS-n-Rk`: `tab_top_configs`, `tab_h4_wilcoxon`, `tab_kendall_class`,
  `tab_scaling_slopes`, `tab_hypothesis_summary`, `fig_cd_diagram_h1`, `fig_pareto_s1_s2`,
  `fig_rule_class_heatmap`, `fig_scaling_curves`, `fig_boxplot_gap_by_n`, `fig_std_R_vs_n`,
  `fig_h4_wilcoxon_bars`. Exportados al manuscrito con el script 08.
- [x] `tab_kendall_class` ya no usa "composed"; ahora dice "Fixed-dimensional".
- [x] Valores corregidos en el texto: mean rank 4.774 (`FCS-3-R1`) y 6.363 (PSO); 33 configuraciones
  en el diagrama CD; τ(S1,S2) = 0.095 con **p = 0.451** (no significativo); especialistas
  S1 = `FCS-3-R5` y S2 = `FCS-5-R6`. Eliminadas las referencias a `PSO_FCS:O2:3:I1:R1`.
- [x] Auditoría textual sin coincidencias para: `O2`, `3.26`, `10.1`, `unimodal F1--F5`,
  `multimodal F6--F20`, `32 configurations`, `composed`, `PSO_FCS:O`, `PSO_FCS:G`, `rule set`.
- [x] `tab_hypothesis_summary` reescrita con `tabularx`: desaparece el overfull de 555 pt.
- [x] Orientación de $A_{12}$ declarada en las notas de tabla: se minimiza el fitness, así que
  $A_{12} = P(\text{FCS} < \text{PSO}) + \tfrac{1}{2}P(\text{FCS} = \text{PSO})$ y $A_{12} > 0.5$ favorece al FCS.
- [x] `pyarrow` instalado en el entorno de análisis usado por los scripts parquet.

### 7.9 Apéndices del artículo  *(cierre editorial; no se entrega SI separado)*
- [x] Apéndice A incorpora las 62 comparaciones por instancia en las Tablas A1--A3; el cuerpo mantiene los resultados resumidos y la matriz completa de rangos.
- [x] Apéndice B incorpora el atlas completo de media--dispersión para las 62 instancias: 62 paneles en 7 páginas con formato de figura extendida MDPI, hasta nueve paneles por página y escalas comunes entre dimensiones de cada función escalable.
- [x] El texto de las subsecciones de resultados remite a los apéndices A y B; el back matter ya no declara un archivo Supplementary Information separado.
- [x] El generador `code/15_generate_mean_dispersion_maps.py` produce el atlas final en `manuscript/figures/appendices/fig_mean_dispersion_by_function.pdf`.
- [x] Artículo autocontenido recompilado el 2026-10-13: 59 páginas, sin errores ni referencias sin resolver.

### 7.10 Revisar preguntas de investigación y criterios de interpretación  *(✅ HECHO 2026-10-13)*
### 7.10 Preguntas de investigación y criterios de interpretación  *(✅ ACTUALIZADO 2026-10-15)*
- [x] RQ1–RQ5 se presentan como preguntas de investigación, no como hipótesis confirmatorias (D14).
- [x] RQ4 reporta comparaciones independientes Mann–Whitney con Bonferroni; no usa el umbral arbitrario del 50 % como regla de decisión.
- [x] Se distinguen significancia estadística y magnitud del efecto, reportando $A_{12}$ y tamaños de efecto factorial junto a los *p*-values.
### 7.11 Consistencia numérica  *(✅ VERIFICADA 2026-10-15)*
- [x] Contrastar texto, tablas y figuras contra el dataset final: 63 426 corridas, 33 configuraciones, 62 instancias, rankings, tamaños de efecto, valores $p$, correcciones Bonferroni/Holm, escalamiento y dinámicas. No se ejecutaron corridas PSO para esta actualización editorial.
### 7.11 Consistencia numérica  *(✅ VERIFICADA 2026-10-15)*
- [x] Rankings RQ1 conciliados: FCS-3-R1 rango medio 4.774, PSO 6.363, CD 6.591; 272/528 pares Nemenyi significativos. RQ4 independiente: 22/906/1056 Bonferroni W/NS/L; FCS-3-R1 = 16/46/0.
### 7.11 Consistencia numérica  *(✅ VERIFICADA 2026-10-15)*
- [x] El suplemento final no incluye resultados H3 factoriales ni scripts heredados; esos materiales se conservan en el archivo histórico del proyecto, fuera del paquete de entrega.
- [x] Reconciliado §5.2: 50 rank wins, 6 ties, 6 losses; 30/50 rank wins con Wilcoxon nominal $p<0.05$, y 31 p-values nominales en total porque F16 es significativo en fitness crudo pese a empate por normalized-gap rank.
### 7.15 Cierre editorial final  *(✅ COMPILADO 2026-10-15)*
- [x] Compilación y revisión visual del PDF completadas: artículo 62 páginas; Supplementary Information 43 páginas; ZIP final validado (2026-10-15).
- [x] Boxplot por granularidad contrastado con gaps run-level transformados: medianas log-gap 0.024/0.222/0.207/0.186 e IQR 3.499/3.194/3.241/3.274 para $n=3,5,7,9$.
- [x] Corregidos captions/criterios de selección de H4 (top-10 por Bonferroni wins, raw wins, mean $A_{12}$) y scaling (cinco slopes medianos menores/mayores; no equivalen a mejor/peor gap absoluto).
- [x] **Reanalizar H3 respetando el bloqueo `instancia × run_id` (2026-10-13).** `code/17_reanalyze_h3_blocked.py` conserva los 1 922 bloques y genera resultados exploratorios por rangos y log-gap. Simulación nula (500 réplicas por distribución; 999 bootstraps cada una): tasa de rechazo bootstrap 6.0% normal y 4.6% t4; la aproximación Wald F es inaceptable (72.8--74.8%). Los p-values H3 son exploratorios; ANOVA/SRH antiguos no se usan.
- [x] Sensibilidad interna por función (23 unidades): RM Greenhouse--Geisser $p=0.152$ en rangos y $p=0.535$ en log-gap; permutación de signos $p=0.086$ y $p=0.0029$, respectivamente. La discordancia entre respuesta/prueba y la asimetría de los contrastes impiden una conclusión inferencial estable.
- [x] Preparado `H3_external_statistical_review.md` con diseño, estructura de dependencia, resultados exploratorios y preguntas para revisión independiente (2026-10-13).
- [x] Cierre H3: pregunta exploratoria/descriptiva; las dispersiones por función y la interpretación inferencial se mantienen dentro de sus límites (2026-10-13). Revisión estadística externa no obligatoria; queda como validación futura opcional si se persiguen afirmaciones confirmatorias.
- [x] Recalculados desde `experiments_meta.parquet` y conciliados con tablas: 63 426 runs, 62 instancias, 33 configuraciones; mean ranks FCS-3-R1 = 4.774 y PSO = 6.363; CD = 6.591; H4 FCS-3-R1 = 27/33/2, 13 wins Bonferroni; S1/S2 especialistas FCS-3-R5/FCS-5-R6, $\tau=0.095$, $p=0.451$.
- [x] §5.2: 50 rank wins, 6 ties, 6 losses; 30/50 wins tienen Wilcoxon nominal $p<0.05$, con 31/62 nominales en total porque F16 es significativo en fitness crudo pese al empate por normalized-gap rank. F16/F17: 1023/1023 gaps cero; F19: 990/1023.
- [x] H4 tabla/figura: corregido el criterio de selección descrito en texto y captions; top 10 ordenados por wins Bonferroni, wins nominales y mean $A_{12}$, según el generador.
- [x] Escalamiento: reconciliados los diez slopes con su CSV; FCS-5-R4 vs FCS-3-R1 en d=10 (0.668 vs $4.52\times10^{-13}$) y d=100 (28.04 vs 7.28).
- [x] §3.1 captions y superficies: output O1 está definido en el universo normalizado [0,1] y luego se reescala; paneles 3D regenerados para mostrar el $w$ efectivo en [0.1,0.9], con captions alineados.
- [x] F7: la tabla usa $f^*=0$ como referencia de gap del solver; el atlas visualiza el objetivo esperado, con ruido aditivo medio 0.5. La diferencia quedó explicitada en la nota de la tabla.
- [x] §5.7: Spearman entre caída de $w$ y mean rank revalidado desde los CSV ($\rho=-0.857$, $p=0.00653$); XPL tardío R4/R8 = 5.19%/3.64%; las cuatro curvas de convergencia citadas coinciden con sus series agregadas.
- [x] Inventario TeX: 37 `includegraphics`, 22 `input`; todos los assets/inputs existen, sin etiquetas duplicadas ni referencias sin resolver en el barrido de fuentes.
- [x] **§5.6 auditada contra sus tablas (2026-09-24).** Errores corregidos: los empates de `FCS-3-R1`
  eran 33 y no 13; los wins con Bonferroni son 13 y no 6; $A_{12}$ medio es 0.669 y no 0.62;
  la frase sobre `R2:n3` con wins significativos era falsa (`FCS-3-R1` es la única con más de un
  win corregido). En escalamiento: la Tabla 11 es por configuración agregada sobre F1–F13, no
  "R4 on F6" ni "R1:F2"; esas referencias no existían en los datos.
- [x] **Desajuste Tabla 11 / Figura 13 explicado en el texto:** la figura muestra las cinco entradas
  de mejor rango medio (incluido PSO) y la tabla las pendientes más suaves y más pronunciadas.
- [x] **Retirada la recomendación "R4 preferable for large-scale problems".** `FCS-5-R4` parte de un
  gap 12 órdenes de magnitud peor que `FCS-3-R1` en $d=10$ y sigue peor en $d=100$ (28.0 vs 7.3):
  su pendiente suave solo refleja que ya era mala y tenía poco margen de degradación.
- [x] **7.11b** Figura 10 verificada en la numeración actual: `surface_panel_7` muestra las superficies R1--R8 para $n=7$; caption y referencia textual concuerdan con el contenido. La nota anterior correspondía a una numeración previa.
- [x] §5.2 reconciliada con `function_level_per_instance.csv`: 50 rank wins FCS (30 nominalmente significativos sobre fitness final), 6 victorias PSO, 6 empates; 15 configuraciones FCS con al menos una victoria; `FCS-3-R1` registra 30 victorias (28 en S1). Se corrigieron las afirmaciones por función y la nota de empate F16/F17/F19.
- [x] Figura 30 (`fig_w_trajectories`) auditada contra el generador, el log del solver y los CSV agregados: 63 426 corridas, 33 configuraciones, 1001 iteraciones y 1922 observaciones por configuración/iteración; PSO coincide con su schedule lineal con error máximo $4.3\times10^{-14}$; `w` y `XPL` quedan dentro de rango con tolerancia numérica. Se alineó XPL pre-update con $w_t$ y el caption distingue que PSO no usa XPL para controlar $w$.
- [x] **Contradicción figura/texto corregida en 5.5:** el texto afirmaba que la desviación entre reglas
  *decrece* con `n`, pero `fig_std_R_vs_n` muestra lo contrario y `h3_std_R_decreasing_with_n` es
  `False` en `summary.json`. Reescrito con los valores reales (rango: 6.78 / 6.40 / 6.69 / 7.52;
  gap crudo: 3.99 → 4.64). `fig_std_R_vs_n` pasa a suplemento.
- [x] Inspección visual de las 59 páginas compiladas y revisión de captions, tablas, figuras, referencias, escalas y disposición; captions acortados donde repetían resultados y se mantuvieron unidades, transformaciones y notas estadísticas necesarias (2026-10-13).
- [x] Búsqueda final de placeholders, instrucciones internas, lenguaje prospectivo impropio y nombres genéricos de revista; sin hallazgos en el texto principal. Pendientes de metadatos de autor y depósito se mantienen como tareas editoriales explícitas.
- [x] Corregido el overfull de 555 pt de `tab_hypothesis_summary.tex` (reescrita con `tabularx`).
  Solo quedan tres overfull por debajo de 10 pt, despreciables.
- [x] §5.5: R1 endpoint increase (3.65 ranks) distinguished from total spread; R2 has the largest spread (5.3) and R4 the next largest (4.5). R6/R7/R8 variation is described comparatively, with the 2.5-rank threshold explicitly descriptive, not an equivalence test.
- [x] §5.3/6/7: Kendall $\tau=0.095$, $p=0.451$ is reported as weak observed concordance and insufficient evidence of positive association; no independence or general transferability conclusion is drawn. The different S1/S2 leaders remain explicit.
- [x] §5.6: non-significant post-Bonferroni comparisons are described as no detected difference, not statistical equivalence; the tests and win/tie/loss results are unchanged.

### 7.12 Reproducibilidad y datos abiertos  *(gestión manual del autor; depósito no realizado)*
- [ ] Preparar y aprobar un depósito persistente con datos brutos, resultados procesados, scripts y configuraciones; asignar DOI antes de declarar disponibilidad pública. Estado verificado 2026-10-13: no hay repositorio público ni DOI.
- [ ] Aprobar la declaración CRediT por autor. El archivo de metadatos confirma orden, afiliaciones y contactos, pero no contiene asignaciones de contribuciones.
- [ ] Incluir `results/tests/h3_factorial_anova/summary.json` y `std_across_R_vs_n.csv` como artefactos históricos requeridos por los scripts 13 y 06; rotular sus resultados H3 como exploratorios/no confirmatorios y no volver a ejecutar el procedimiento antiguo.

### 7.13 Reescribir la discusión  *(✅ HECHO 2026-10-13)*
- [x] La discusión interpreta que los patrones con consequentes de progreso decreciente ocupan los mejores rankings; no atribuye causalidad al eje ni al controlador.
- [x] Explica que las comparaciones entre consequentes de diversidad varían según el patrón nominal de progreso y que los especialistas S1/S2 usan estructuras distintas, sin tratarlas como efectos independientes de entrada.
- [x] Declara que la evidencia no respalda una configuración estática universal y distingue la selección-oráculo por instancia de una política desplegable.
- [x] Presenta la adaptación semántica como pregunta futura que requeriría selección con información disponible durante la optimización.
- [x] Explicita las limitaciones como controles del estudio y evita inferencias causales sobre las clases de paisajes.

### 7.13b Análisis explicativos nuevos  *(alimentan 5.4–5.7)*
- [x] **Tabla factorial semántica de reglas** — `tab_rule_semantic_grid.tex`, grilla progreso × diversidad
  con el mean rank de cada patrón promediado sobre las cuatro granularidades. Generador:
  `code/12_analyze_rule_structure.py`. La grilla se lee casi íntegramente por filas.
- [x] **Mirror-pair analysis** — `tab_rule_pairs.tex`, 1984 comparaciones pareadas por semilla
  (8 pares × 4 granularidades × 62 instancias). Las dos familias se reportan por separado (D20):
  - Pares espejo: R1/R2, R3/R4, R5/R8, R6/R7 invierten todos los ejes no neutrales; los pares R1/R2 y R3/R4 tienen un eje neutral.
  - Pares de eje único: R5/R7 y R6/R8 (progreso); R5/R6 y R7/R8 (diversidad).
- [x] Redactada la subsección 5.4 con los hallazgos verificados.
- **Hallazgos descriptivos de los patrones probados:** las comparaciones de consecuentes con dirección
  decreciente tienen mejores rankings pareados que sus contrapartes crecientes (R1>R2 187/248 con
  $A_{12}=0.99$; R5>R7 170/248; R6>R8 171/248). Entre patrones con distintos consequentes de
  diversidad, los resultados varían según el patrón nominal de progreso: R5>R6 (113 vs 37),
  R8>R7 (160 vs 15), y R4>R3 (123 vs 42). R3 (21.9) y R4 (22.0) son casi indistinguibles en el
  ranking agregado. Estos contrastes comparan estructuras de consequentes bajo la misma inferencia
  Mamdani de dos entradas; no son efectos causales independientes de los inputs.
- [x] **Performance–robustness map** generado desde resúmenes de 31 runs: `fig_mean_dispersion_representative.pdf` en §5.6 y paneles por función en SI-C. Ejes: media y SD del normalized gap, ambos logarítmicos; regla por color, granularidad por marcador y PSO destacado.
- [x] **Efecto de granularidad por regla** — `tab_granularity_by_rule.tex` (8 reglas × 4 granularidades, mejor $n$, spread y tendencia), junto con `fig_granularity_effect.{png,pdf}`. Hallazgos y código en `code/13_analyze_granularity.py`.
- [x] **Trayectorias de `w(t)`** — `fig_w_trajectories.{png,pdf}`: paneles por `n`, ocho patrones por
  panel, coloreados por dirección del progreso, con la fila inferior mostrando XPL. Redactada 5.7.
- **Hallazgos 5.7:** las medias generales de R1 (0.49948--0.49983) son próximas a la de PSO (0.50000),
  pero sus trayectorias no son idénticas a la programación lineal: la diferencia absoluta máxima entre
  curvas es 0.13480, 0.04194, 0.03315 y 0.02731 para $n=3,5,7,9$. Los consequentes de R1 son neutrales
  respecto de diversidad a progreso fijo, pero el output efectivo conserva dependencia débil de diversidad
  bajo inferencia Mamdani min--max. El ranking de R1 no demuestra un beneficio causal de diversity feedback;
  los resultados comparan estructuras de consequentes bajo la misma arquitectura de dos inputs e inferencia.
  R2 es su espejo exacto (sube de 0.16–0.22 a 0.79–0.85). R3 se queda plano cerca de $w_{\min}$ y R4
  cerca de $w_{\max}$. **Spearman entre la caída de `w` y el rango medio = −0.857 (p = 0.007)**;
  el nivel final de exploración NO es predictivo por sí solo (ρ = 0.21, p = 0.61).
  Convergencia: F1 `FCS-3-R1` 1.7e-9 vs PSO 7.7e-6; F9 `FCS-5-R2` se estanca en 38.5 desde la
  iteración 200 y PSO la supera (35.8); F23 PSO y `FCS-5-R6` alcanzan −10.54 mientras `FCS-3-R1`
  se queda en −3.84.
- [ ] **Boxplots selectivos** por función (F1/F2, F5, F9/F10, F11, F21–F23) con PSO, mejor FCS global, mejor FCS de la función y una configuración mala como contraste. Cuerpo: 6–8 funciones; suplemento: todas.

### 7.14 Antecedentes internos OLA/CLEI/WEA  *(regla D19)*
- [x] Regla aplicada: los antecedentes previos solo orientan prácticas internamente; no se nombran ni citan por ese uso.
- [x] Las figuras, tablas y datos del SI se regeneraron desde el batch MDPI actual; no se reciclaron assets de conferencia.
- [x] Búsqueda textual en el manuscrito y el SI: sin nombres OLA2026/CLEI2026/WEA2026, ni frases "inspired by", "adapted from" o equivalentes.
- [x] La discusión final interpreta exclusivamente los resultados MDPI (cerrada en 7.13).

### 7.15 Cierre editorial final
- [x] Sin frases prospectivas sobre resultados, placeholders o nombres genéricos de revista en el texto principal; se removió la frase de créditos que prometía completarse antes del envío (2026-10-13).
- [x] Cifras primarias de texto/tablas y captions/figuras revisadas; ver 7.11. Compilación y revisión visual del PDF completadas (2026-10-13).
- [x] Preguntas H1–H5 alineadas con los resultados obtenidos; H3 descriptivo y R1 interpretado según el Mamdani implementado (2026-10-13).
- [x] Título y Abstract revisados contra el estudio factorial y el mensaje central (2026-10-13).
- [ ] Completar el texto CRediT con asignaciones aprobadas por los autores.
- [ ] Decidir y ejecutar el depósito reproducible antes de declarar los datos públicamente disponibles; véase 7.12.

