# Decisiones metodológicas — Paper MDPI (Scalable Fuzzy PSO Partitions)

> **Propósito:** registro auditable de las decisiones de diseño tomadas en las fases 0–1 del proyecto. Cada entrada documenta el contexto, las alternativas evaluadas, la decisión final y la justificación (con referencias citables cuando aplica). Este documento es la fuente primaria para redactar la sección *Materials and Methods* del manuscrito y para responder eventuales preguntas de revisores.

**Última actualización:** 2026-10-15
**Estado vigente:** dataset final consolidado y validado; F14 usa la definición canónica; artículo y Supplementary Information compilados. RQ3 es descriptiva. Los métodos inferenciales finales y la interpretación están resumidos en D21–D25; los análisis históricos de H3 no forman parte de la evidencia final.
**Revista objetivo:** MDPI **Mathematics** (D16).

---

## Resumen ejecutivo (tabla de decisiones)

| # | Decisión | Resultado | Justificación corta |
|---|---|---|---|
| **D0** | **Posicionamiento dentro de la tesis doctoral** | **Paper preparatorio: estudia FCS estático para justificar empíricamente la necesidad de adaptación semántica** | **El paper NO presupone "fuzzy schemes"; los motiva a partir de evidencia** |
| D1 | Repositorio aislado | Branch `Solver_CEC_Fuzzy_PSO_ARTICULO_MDPI` | Trazabilidad respecto a OLA/CLEI/WEA previos |
| D2 | Foco del paper | Estudio empírico de sensibilidad del FCS Mamdani estático a granularidad y reglas (NO nuevo MH, NO selector dinámico) | Responde la pregunta previa: ¿es necesaria la adaptación semántica? |
| D3 | Familia de partición | Triangular uniforme paramétrica | Estándar Mamdani; reproducible por una sola fórmula |
| D4 | Granularidad evaluada | n ∈ {3, 5, 7, 9} | Cubre rango típico de literatura y extiende a alta resolución |
| D5 | Familia de reglas | 8 patrones aditivos R1–R8 | Cubre las direcciones semánticas (prog↑/↓, div following/compensating) en grilla cerrada |
| D6 | Overlap | 1.0 (Ruspini) | Cobertura completa Σμ=1; descartado overlap=0 (degenerado) |
| D7 | Shoulders en extremos | True para input y output (simétrico) | Cobertura Ruspini en todo [0,1]; saturación exacta de w |
| D8 | Defuzzificación | Centroide + rescalado lineal a [wMin, wMax] | Compatible con cualquier n; sin código ad-hoc |
| D9 | Etiquetas lingüísticas | Definidas en JSON para n∈{3,5,7,9} | Reproducibilidad y trazabilidad declarativa |
| D10 | Validación del FIS | Property-based tests (centros, cobertura, Ruspini, saturación, determinismo) | Verifica matemática, no equivalencia con código previo |
| D11 | Implementación FIS | NumPy puro (sin `skfuzzy`) | Sin dependencias externas; control total del pipeline |
| D12 | Configuración declarativa | `config/fuzzy_partitions.json` | Cambio de partición sin modificar código del solver |
| D13 | Alcance: ¿uno o dos artículos? | **Un solo artículo factorial**; la propuesta adaptativa se pospone | Consolidar primero la base empírica antes de proponer el meta-controlador |
| D14 | Estatus de las preguntas | **RQ1–RQ5 son preguntas de investigación**, no hipótesis confirmatorias | Los criterios históricos de rechazo no se usan como reglas confirmatorias |
| D15 | Granularidad del reporte de resultados | Tres niveles obligatorios: global → clase → **función individual** | La afirmación central (no hay configuración universal) exige evidencia por función |
| D16 | Revista objetivo | **MDPI Mathematics** (confirmado 2026-09-24); §3.4 formal obligatoria | El scope exige contribución matemática, no solo barrido empírico |
| D17 | Nomenclatura de configuración | `FCS-n-Rk` como formato único | Hoy coexisten 3 formatos distintos en texto, tablas y figuras |
| D18 | Regla editorial de versión final | Prohibido el lenguaje prospectivo fuera de *Future Work* | El manuscrito ya tiene resultados; el lenguaje de plan señala borrador no cerrado |
| D19 | Uso de los antecedentes OLA/CLEI/WEA | Referencia interna de organización; **no exponer la genealogía** en el manuscrito | El artículo debe leerse como trabajo autónomo, no como extensión mecánica de conferencias |
| D20 | Simetría especular del banco de reglas | **Verificada en código:** R1↔R2, R3↔R4, R5↔R8, R6↔R7 son los únicos pares espejo | Los dos últimos invierten ambos ejes, así que no aíslan un factor: para eso van R5/R7, R6/R8, R5/R6, R7/R8 |
| D21 | Dataset de publicación y F14 | 63 426 corridas finales; 1 023 ejecuciones F14 usan la función de Shekel con pesos canónicos $1,\ldots,25$ | Una única base final sustenta tablas, figuras y suplemento |
| D22 | Semillas y unidad de réplica | Semilla única `42 + historical_exp_id`; sin semillas compartidas por configuración | `run_id` no define bloques comunes ni justifica pareamiento entre configuraciones |
| D23 | Inferencia de comparaciones por corrida | RQ4: Mann–Whitney independiente, Bonferroni en 1 984 tests; Tabla 11: familia independiente, Holm en 1 984 tests | Las dos familias y sus correcciones se reportan por separado |
| D24 | RQ3 | Dispersión de rangos y log-gap descriptiva; no se estima una interacción factorial | No se usa el bootstrap histórico por `run_id` como inferencia confirmatoria |
| D25 | Paquete editorial final | Main PDF, Supplementary Information y ZIP de datos fechados 2026-10-15 | Las fuentes editoriales previas quedan archivadas; `EDITORIAL_BEST_PRACTICES.md` es la guía activa |

---

## Estado final del análisis y manuscrito (2026-10-15)

- **Dataset:** 63 426 filas, 33 configuraciones, 62 instancias y 31 corridas por configuración–instancia. Las 63 426 semillas están presentes y son únicas; la semilla es $42+$ identificador global del experimento. No hay bloques de semilla compartida entre configuraciones.
- **RQ1:** Friedman sobre rankings por instancia y post-hoc Nemenyi; $\chi^2(32)=1052.38$, $p=1.56\times10^{-200}$, CD $=6.591$, 272/528 pares significativos. Líder: FCS-3-R1, rango medio 4.774; PSO, 6.363.
- **RQ2/RQ5:** concordancia de rankings entre grupos/subconjuntos; $\tau(S_1,S_2)=0.0947$, $p=0.4507$. La no significancia no establece independencia ni transferibilidad.
- **RQ3:** análisis descriptivo de dispersión entre R1–R8 por granularidad y función; no se informa una prueba de interacción. `run_id` no se considera bloque de semilla común.
- **RQ4:** 1 984 pruebas Mann–Whitney bilaterales sobre muestras independientes, asintóticas con corrección de continuidad y Bonferroni ($\alpha=0.05/1984$). W/NS/L ajustado: 22/906/1056; FCS-3-R1: 16/46/0.
- **Tabla 11:** ocho pares × cuatro granularidades × 62 instancias = 1 984 pruebas Mann–Whitney independientes; Holm sobre la familia completa. 1 200/1 984 permanecen significativas y las ocho direcciones dominantes se mantienen.
- **Runtime:** cociente de medianas de grupos independientes; no se emparejan tiempos por `run_id`.
- **F14:** versión final canónica con pesos $1,\ldots,25$; resultados integrados en las mismas 63 426 filas.
- **Entrega:** artículo compilado a 62 páginas; Supplementary Information a 43 páginas; ZIP final con run-level data y resúmenes. No hay DOI ni depósito público independiente; la disponibilidad externa queda sujeta a decisión de los autores.

Las decisiones D0–D20 que siguen documentan el diseño original y su evolución; en caso de conflicto, D21–D25 describen el estado final que debe prevalecer en futuras revisiones.

## D0 — Posicionamiento dentro de la tesis doctoral

**Contexto.** La tesis del autor (ver `documentation/Tesis_DII/proposal.tex`) propone un **Adaptive Fuzzy Control System (AFCS)** con *dual-level adaptation* (parameter-level + semantic-level). El núcleo de la tesis (Obj. específico 2 y 3) es: definir un conjunto estructurado de "fuzzy schemes" y diseñar un mecanismo de selección dinámica (estático, estocástico, Q-Learning, hiperheurística) que cambia el scheme en runtime según métricas del proceso de búsqueda.

**Pregunta previa que este paper debe responder.**

> ¿Es realmente necesario adaptar la semántica del FCS al tipo de problema, o existe una configuración estática del FCS Mamdani que domine globalmente sobre la familia de problemas?

Si una sola configuración estática del FCS (granularidad y reglas fijas) fuera óptima en todo el Classical Benchmark Suite F1–F23, la línea de adaptación semántica de la tesis sería injustificable. Si la configuración óptima depende del tipo de problema, el paper provee la **base empírica** que motiva los próximos pasos de la tesis.

**Alternativas evaluadas.**
- A. Presentar el paper directamente como "caracterización del espacio de fuzzy schemes" (presupone que los schemes ya están definidos como objeto de estudio).
- B. Presentar el paper como **estudio empírico de sensibilidad del FCS estático** que motiva la pregunta de si la adaptación semántica es necesaria.

**Decisión.** Opción B.

**Justificación.**
- **Coherencia lógica.** El paper MDPI no puede presuponer la existencia ni la utilidad de fuzzy schemes; debe **producir la evidencia** que justifica su definición posterior.
- **Cadena argumentativa de la tesis.** El framing en orden:
  1. **MDPI (este paper):** "El FCS Mamdani estático no domina uniformemente; configuraciones distintas son óptimas para problemas distintos." → motiva la necesidad de adaptar la semántica.
  2. **Paper siguiente:** "Dado el resultado anterior, definimos formalmente fuzzy schemes y comparamos N mecanismos de selección dinámica." → propone AFCS.
  3. **Papers posteriores:** validación en SCP, KP, Feature Selection, GA (ver roadmap).
- **Vocabulario del paper MDPI.** Se habla de "configuración del FCS Mamdani" o "parametrización del FIS" (granularidad `n` + patrón de reglas `R`). Los términos *fuzzy scheme* y *AFCS* se reservan exclusivamente para *Discussion / Future Work* como continuación natural sugerida por los resultados.

**Roadmap incremental de la tesis** (acordado 2026-06-27):

| Etapa | MH | Benchmark | FCS | Aporte a la tesis |
|---|---|---|---|---|
| 1. **MDPI (este)** | PSO | Classical F1–F23 (Abualigah et al. 2021) | Estático paramétrico (n × R) | Justifica empíricamente la necesidad de adaptación semántica (OE preparatorio) |
| 2. Paper siguiente | PSO | Classical F1–F23 + CEC2017 / SCP | Adaptive (AFCS): fuzzy schemes + selector dinámico | OE 1 + OE 2 + OE 3 de la tesis |
| 3. | PSO | SCP + KP | AFCS validado | OE 5 (problemas combinatorios) |
| 4. | PSO | Feature Selection + real-world (biomédico/educativo) | AFCS validado | OE 5 (dominios reales) |
| 5. | **GA** | Misma cadena | AFCS validado | OE 4 (generalización MH) |

**Implicación sobre las preguntas de investigación (`04_hipotesis_metricas_analisis.md`).** H5 pregunta si una configuración estática se transfiere entre el benchmark y sus subconjuntos. Es central para el framing del paper, pero se interpreta descriptivamente y no como hipótesis confirmatoria. H1–H4 organizan evidencia complementaria.

**Estado.** Acordado y vinculante para todas las decisiones posteriores del paper.

---

## D1 — Repositorio: branch dedicada al paper MDPI

**Contexto.** El workspace original es la base de tres trabajos previos (OLA2026, CLEI2026, WEA2026) con MFs ad-hoc.

**Alternativas.**
- A. Modificar `main` directamente.
- B. Branch dedicada `Solver_CEC_Fuzzy_PSO_ARTICULO_MDPI`.
- C. Repositorio nuevo (fork).

**Decisión.** Opción B.

**Justificación.** Preserva la trazabilidad respecto a los tres papers anteriores (sus carpetas `FUZZY/1.-OLA2026/`, `2.-CLEI2026/`, `3.-WEA2026/` permanecen intactas para comparación opcional) y mantiene el historial git lineal sin duplicar la infraestructura del pipeline.

---

## D2 — Framing del paper: estudio empírico de sensibilidad del FCS estático

**Contexto.** Los trabajos previos del autor (WEA, CLEI, OLA) proponen PSO_FCS como variante con fuzzy inertia y caracterizan los tres ejes del FIS (output, input, reglas) por separado. La tesis (ver D0) plantea como núcleo el AFCS con adaptación dual (parámetro + semántica). Existe ya literatura abundante de PSO+fuzzy con resultados marginales.

**Alternativas.**
- A. Proponer una nueva variante de PSO (incremental).
- B. Presentar el paper como propuesta de AFCS (anticipar el aporte central de la tesis).
- C. Presentar el paper como **estudio empírico de sensibilidad** del FCS Mamdani estático respecto a granularidad y reglas, evaluando si existe configuración estática óptima global o si los óptimos dependen del problema.

**Decisión.** Opción C.

**Justificación.**
- **Posicionamiento en la tesis (ver D0):** este paper responde una pregunta previa cuyo resultado **motiva** la línea AFCS, no la presenta. Adelantar AFCS aquí dejaría a los siguientes papers sin justificación empírica.
- **Diferenciación frente a literatura PSO+fuzzy:** la literatura existente se enfoca en "proponer y comparar"; un estudio sistemático que **cuestiona la suficiencia del FCS estático** es metodológicamente más fuerte.
- **Coherencia logica:** primero se establece el problema (heterogeneidad de óptimos del FCS estático), luego se propone la solución (AFCS).
- **Alineado con el alcance de MDPI Mathematics** (sistemas difusos paramétricos, diseño factorial controlado, análisis estadístico y caracterización formal de familias de controladores). Ver D16.

**Preguntas de investigación derivadas:** ver `04_hipotesis_metricas_analisis.md`. H5 es central para el framing, pero no se trata como hipótesis confirmatoria.

**Vocabulario.** Este paper habla de **"configuración del FCS Mamdani"** o **"parametrización del FIS"**. Los términos *fuzzy scheme* y *AFCS* solo aparecen en *Future Work*.

---

## D3 — Familia de funciones de membresía: triangulares uniformes paramétricas

**Contexto.** Los papers previos usaban tripletas `(a, b, c)` hardcoded por cada n (p. ej. 5L = `[0.15, 0.35, 0.5, 0.65, 0.85]`), sin fórmula generadora.

**Alternativas.**
- A. Triangulares uniformes (paramétricas, una fórmula).
- B. Gaussianas (suaves, defuzz. continua).
- C. Trapezoidales (plateau en el medio).
- D. Mantener las ad-hoc (bit-equivalencia con WEA).

**Decisión.** Opción A: `make_partition_uniform(n, overlap, shoulders)`.

**Justificación.**
- **Reproducibilidad:** la partición queda definida por 3 parámetros, no por 2n números.
- **Sistematización:** el mismo generador funciona para n ∈ {3, 5, 7, 9, …}; no requiere "inventar" tripletas nuevas por cada granularidad.
- **Estándar académico:** triangulares uniformes con shoulders son la elección por defecto en Mamdani (Pedrycz & Gomide 2007; Yen & Langari 1999).
- **Coste computacional:** evaluación O(n) por inferencia; idéntico a las ad-hoc.

**Cita.** Pedrycz, W. & Gomide, F. (2007). *Fuzzy Systems Engineering: Toward Human-Centric Computing*. IEEE Press / Wiley. Cap. 3.

**Trade-off aceptado.** Los resultados ya no son bit-equivalentes a WEA/CLEI/OLA. Se vuelven a ejecutar todos los experimentos. **Esto es deseable** porque el paper estudia un esquema sistematizado, no replica el ad-hoc.

---

## D4 — Granularidad evaluada: n ∈ {3, 5, 7, 9}

**Contexto.** En literatura de FIS, los valores típicos son n = 3 (low/medium/high), n = 5 (very_low … very_high) y ocasionalmente n = 7. n = 9 es atípico.

**Alternativas.**
- A. Solo n ∈ {3, 5}.
- B. n ∈ {3, 5, 7, 9}.
- C. n ∈ {3, 5, 7, 9, 11, 13}.

**Decisión.** Opción B.

**Justificación.**
- **n = 3** y **n = 5** son la referencia obligada (literatura).
- **n = 7** y **n = 9** extienden el rango hacia alta granularidad para testear la hipótesis de retornos decrecientes (H1).
- **n = 11+** no aporta diferencias semánticas (las etiquetas se vuelven artificiales) y multiplica el costo experimental sin justificación.
- Sólo se usan valores impares para que exista una MF "medium" central simétrica.

**Etiquetas lingüísticas** declaradas en `config/fuzzy_partitions.json::labels_by_n` (siempre simétricas, con "medium" central).

---

## D5 — Familia de reglas: 8 patrones aditivos R1–R8

**Contexto.** Una regla Mamdani con dos entradas de n_labels cada una requiere n² consecuentes. Codificar cada matriz a mano es propenso a errores y no escala a n = 7, 9.

**Alternativas.**
- A. Codificar cada matriz a mano por cada (n, R).
- B. Generar reglas por una fórmula paramétrica que codifique la **semántica direccional** (progress increasing/decreasing, diversity following/compensating).
- C. Reglas aprendidas por algún optimizador (ANFIS, GA-tuning).

**Decisión.** Opción B: `make_rule_matrix(pattern, n_labels)`.

**Justificación.**
- **Sistematización:** R1–R8 cubren las 8 combinaciones de direcciones semánticas posibles para dos entradas (3 prog × 3 div − 1 caso trivial = 8 patrones útiles).
- **Escalabilidad:** las matrices se generan automáticamente para cualquier n.
- **Interpretabilidad:** cada Rk tiene una descripción semántica explícita en `rule_patterns._desc`.
- **Verificación:** modelo aditivo de dos regímenes (identidad si un solo efecto activo; bandas de 2 si ambos activos) — *originalmente derivado para garantizar bit-equivalencia con WEA, ahora retenido por consistencia matemática y verificado por property test*.

**Justificación de descartar C.** Aprender las reglas obscurece el espacio de diseño (¿qué regla "ganó"?). El objetivo del paper es justamente reportar el efecto de las reglas como **factor controlado**, no como variable a optimizar.

---

## D6 — Overlap: 1.0 (Ruspini partition)

**Contexto.** El parámetro `overlap` controla cuánto se solapan dos MFs vecinas. overlap=0 hace que los hombros se aplasten contra los extremos (clipping); overlap=1 produce una partición Ruspini perfecta (Σμ=1 ∀x).

**Alternativas.**
- A. overlap = 0 (sin solapamiento).
- B. overlap = 0.5 (parcial).
- C. overlap = 1.0 (Ruspini estricta).
- D. Estudiar overlap como variable adicional.

**Decisión.** Opción C para la corrida principal; opción D queda **abierta** como extensión futura (el JSON ya es paramétrico).

**Justificación.**
- **overlap = 0** hizo I1 y O1 visualmente indistinguibles (los shoulders fueron absorbidos por el clip) y degeneró la cobertura.
- **overlap = 1.0** es la partición canónica en la teoría de Ruspini (1969): Σμ_i(x) = 1 ∀ x ∈ [0,1]. Toda inferencia tiene "peso total" 1, sin pérdida de evidencia.
- **overlap = 0.5** sería un punto intermedio sin justificación teórica específica.
- Estudiar `overlap` como variable triplica el costo experimental sin pertenecer al *core thesis* del paper (granularidad y reglas). Se reserva para *future work*.

**Cita.** Ruspini, E. H. (1969). *A new approach to clustering*. Information and Control, 15(1), 22–32.

---

## D7 — Shoulders en los extremos: True para input y output (esquema simétrico)

**Contexto.** El parámetro `shoulders` controla si las MFs extremas tienen "hombro" (μ=1 en x=0 ó x=1) o son triángulos completos desplazados hacia el interior. Pregunta planteada explícitamente por el usuario (2026-06-27): *¿hay problema metodológico en que el input no sea Ruspini completa como el output?*

**Alternativas evaluadas** (plot comparativo en `FUZZY/plots/compare_3_schemes.png`):

| Esquema | I1 | O1 | Ruspini en [0,1] | Saturación w | Estándar |
|---|---|---|---|---|---|
| A: Simétrico con shoulders | True | True | ambos | exacta | sí (Pedrycz&Gomide) |
| B: Simétrico sin shoulders | False | False | ninguno (solo interior) | NO llega a wMin/wMax | no |
| C: Asimétrico (I False, O True) | False | True | solo O1 | sí | poco común |

**Decisión.** Esquema A: `shoulders=true` en ambos universos.

**Justificación.**
- **Cobertura completa de evidencia:** Σμ(x) = 1 ∀ x ∈ [0,1] en input y output. La inferencia no se "diluye" en los bordes (críticos en PSO: `progress = 1/maxIter ≈ 0` al inicio; `diversity → 0` al converger; `diversity → 1` al inicio).
- **Estándar académico Mamdani:** una sola frase justifica el esquema ante revisores (cita Pedrycz & Gomide 2007).
- **Coherencia semántica:** "very_low" es un concepto saturante ("una vez que diversity ≤ d, ya es máximamente 'very_low'"); los shoulders codifican esto naturalmente.
- **Saturación exacta de w** en wMin y wMax cuando solo la MF extrema está activa.

**Decisión histórica.** El esquema C (asimétrico) estuvo activo brevemente entre 2026-06-27 mañana y tarde; se descartó tras evaluación explícita del trade-off (`FUZZY/plots/compare_3_schemes.png`). El parámetro `shoulders` permanece configurable en el JSON por si futuros trabajos quieren explorar el espacio.

---

## D8 — Defuzzificación: centroide con rescalado lineal a [wMin, wMax]

**Contexto.** Mamdani requiere defuzzificación. El centroide es el método más usado pero produce un valor en `[c_min, c_max]` del universo del output (en nuestro caso [0,1]), no directamente en [wMin, wMax].

**Alternativas.**
- A. Centroide + rescalado lineal `[0,1] → [wMin, wMax]`.
- B. MOM (Mean of Maxima).
- C. Modificar O1 para que ya esté definida en [wMin, wMax].

**Decisión.** Opción A.

**Justificación.**
- **Estándar:** el centroide es la defuzzificación canónica de Mamdani (cita: Mendel 2001).
- **Separación de concerns:** el universo del FIS es siempre [0,1] (independiente de wMin/wMax); el rescalado se aplica como capa fina. Cambiar wMin/wMax no requiere reconstruir las MFs.
- **Saturación:** con O1 shouldered + Ruspini, el centroide alcanza exactamente 0 y 1 cuando solo MF[0] o MF[n-1] están activas, garantizando que `w` cubre `[wMin, wMax]` completo.

**Cita.** Mendel, J. M. (2001). *Uncertain Rule-Based Fuzzy Logic Systems*. Prentice Hall.

---

## D9 — Etiquetas lingüísticas declaradas en JSON

**Contexto.** Cada n requiere etiquetas lingüísticas para que las reglas sean legibles e interpretables.

**Decisión.** `config/fuzzy_partitions.json::partitions.{I1,O1}.labels_by_n`.

| n | Etiquetas |
|---|---|
| 3 | low, medium, high |
| 5 | very_low, low, medium, high, very_high |
| 7 | very_low, low, medium_low, medium, medium_high, high, very_high |
| 9 | very_very_low, very_low, low, medium_low, medium, medium_high, high, very_high, very_very_high |

**Justificación.** Etiquetas simétricas con "medium" central. Para n=7 y n=9 se introducen modificadores compuestos (medium_low, very_very_low) en lugar de inventar términos nuevos, manteniendo la semántica clara para un revisor.

---

## D10 — Validación: property-based tests, no equivalencia con código previo

**Contexto.** El primer plan (Fase 1 v1) buscaba bit-equivalencia con las MFs ad-hoc de WEA para "no romper" resultados previos. Fue descartado.

**Decisión.** Validar el FIS por **propiedades matemáticas** (no por igualdad numérica con un baseline arbitrario).

**Propiedades verificadas** (`FUZZY/4_verify_fis_properties.py`):
1. Centros equiespaciados según fórmula (todas las combinaciones n × overlap × shoulders).
2. Cobertura del dominio (Σμ > 0 en el rango esperado).
3. Ruspini exacta (Σμ = 1) en el rango esperado.
4. Cardinalidad de reglas = n² para cada R1–R8.
5. `w(d, t)` alcanza wMin y wMax dentro del dominio.
6. Determinismo (mismo input → mismo output, bit-a-bit, en repeticiones).

**Estado actual:** todas las propiedades PASS.

**Justificación.** Los resultados de WEA/CLEI/OLA fueron generados con MFs ad-hoc; reproducirlos no es un objetivo del paper MDPI. Validar las **propiedades teóricas** es más fuerte que validar la equivalencia con un baseline.

---

## D11 — Implementación FIS: NumPy puro

**Contexto.** Alternativas estándar: `scikit-fuzzy`, `simpful`, `pyfuzzylite`.

**Decisión.** Implementación propia en NumPy (`FUZZY/fuzzy_controller_auto.py`).

**Justificación.**
- **Control total:** se necesita acceder a estados intermedios (grados de activación, centroides) para los plots de análisis (Fase 5).
- **Sin dependencias volátiles:** las librerías fuzzy de Python tienen mantenimiento irregular y APIs cambiantes.
- **Performance:** vectorización numpy directa, sin overhead de objetos.
- **Reproducibilidad:** menos superficie de incompatibilidad entre versiones.

**Coste:** el código vive en un único archivo de ~300 LOC, cubierto por los property tests.

---

## D12 — Configuración declarativa: JSON

**Contexto.** Conviene que añadir/modificar particiones no requiera tocar código del solver.

**Decisión.** `config/fuzzy_partitions.json` (declarativo, leído por `FuzzyInertiaController_Auto`).

**Justificación.** Permite que un revisor o el propio autor experimente con `overlap = 0.5`, shoulders mixtos, o nuevas familias de reglas modificando un solo archivo. El solver no se entera.

---

## D13 — Alcance: un solo artículo factorial, sin dividir

**Contexto.** Con los resultados ya ejecutados surgió la opción de separar el material en dos artículos: uno con el estudio factorial estático y otro con la propuesta adaptativa.

**Alternativas.** A. Dividir ahora en dos papers. B. Consolidar un solo artículo factorial sólido y dejar la propuesta adaptativa para el paper siguiente del roadmap.

**Decisión.** Opción B.

**Justificación.** El artículo factorial todavía no está cerrado (falta el nivel de función individual, las curvas de convergencia y la formalización de las familias de reglas). Dividir ahora produciría dos manuscritos débiles en lugar de uno sólido. Además, la propuesta adaptativa necesita como premisa el resultado de este trabajo, de modo que el orden es secuencial y no paralelo. Esto es coherente con D0 y con el roadmap incremental de la tesis.

---

## D14 — Preguntas de investigación, no hipótesis confirmatorias

**Contexto histórico.** El plan inicial etiquetó las preguntas como H1–H5 y asignó criterios formales de rechazo. Algunos criterios (umbral del 50 % en H4, $\tau<0.7$ en H5) se fijaron o ajustaron durante el análisis, no antes de ver los datos. El manuscrito final identifica las preguntas como RQ1–RQ5 y no usa esos criterios históricos para decisiones confirmatorias.

**Alternativas.** A. Mantener el marco confirmatorio con criterios formales de rechazo. B. Presentar RQ1–RQ5 como preguntas de investigación estructuradas. C. Preregistrar y ejecutar un nuevo estudio confirmatorio.

**Decisión.** Opción B.

**Justificación.** Presentar como confirmatorias unas hipótesis refinadas durante el análisis exploratorio es un riesgo editorial evidente ante un revisor metodológicamente exigente. La opción C es inviable en costo. La formulación acordada para el manuscrito:

> RQ1--RQ5 are research questions that organize the analysis; they are not treated as confirmatory hypotheses.

**Consecuencias.** Los resultados se reportan como respuestas descriptivas a preguntas de investigación, separando significancia estadística de relevancia práctica y acompañando los *p*-values con tamaños de efecto.

**Actualización 2026-10-13.** Se retiraron el umbral mayoritario de H4 y el corte de $\tau$ de H5 como reglas de decisión. H3 se presenta descriptivamente; el bootstrap cruzado da p-values exploratorios, con calibración limitada a simulaciones nulas de tamaño finito. La aproximación Wald F se descartó por inflación severa del error tipo I. La validación independiente queda pendiente antes del envío.

---

## D15 — El reporte de resultados exige tres niveles, incluido el de función individual

**Contexto.** El análisis actual presenta rankings globales, agregados por clase de problema y tests estadísticos generales. Falta el detalle función por función.

**Decisión.** La sección de resultados reporta obligatoriamente tres niveles: global, por clase de problema y **por función individual** (F1…F23).

**Justificación.** La afirmación central del artículo es que la configuración óptima depende del paisaje de optimización. Esa afirmación no se sostiene con rankings agregados: requiere evidencia desagregada por función. Sin ella, un revisor puede señalar que la conclusión excede a la evidencia presentada.

**Implementación.** Tabla sintética en el cuerpo (una fila por función) y matriz completa 33 × 62 en material suplementario. Ver `01_task_list.md::7.1`.

---

## D17 — Nomenclatura única de configuración: `FCS-n-Rk`

**Contexto.** En texto, tablas y figuras coexisten al menos tres formatos: `PSO_FCS:O1:3:I1:R1`, `PSO_FCS:G3:I1:R1:O1` y `n=3` / `G3`. La capa 0 del pipeline ya hizo una conversión a formato canónico, pero no es el formato de lectura del artículo.

**Decisión.** Formato único de lectura en el manuscrito: `FCS-n-Rk` (p. ej. `FCS-3-R1`). Los identificadores extendidos se conservan solo en los artefactos de datos.

**Justificación.** `O1` e `I1` son constantes en todo el experimento, así que incluirlos en cada etiqueta añade ruido sin información. Un único formato elimina la ambigüedad entre secciones y facilita la lectura de las figuras.

**Terminología asociada a uniformar:** `rule-base pattern` (no `rule set`), `fixed-dimensional multimodal` (no `composed`), `normalized gap` en prosa (los nombres `gap_final`/`gap_median` quedan para los CSV), `S1` = F1–F13 y `S2` = F14–F23 definidos una sola vez.

---

## D18 — Regla editorial de versión final

**Contexto.** El manuscrito presenta resultados ya ejecutados pero conserva lenguaje de protocolo y de informe de avance: *"the results section will report..."*, *"the exact tests will be frozen..."*, *"will be completed before submission"*.

**Decisión.** Regla vinculante para cualquier edición posterior del manuscrito, humana o asistida:

> Todo texto del manuscrito debe estar redactado como artículo científico final, no como plan de trabajo, protocolo pendiente, informe de avance ni reporte de agente. Si una sección contiene resultados, el texto describe lo que se hizo, lo que se observó y lo que se concluye. Queda prohibido dejar expresiones prospectivas o de planificación tales como *will report*, *will assess*, *planned analysis*, *to be completed*, *future results*, *preliminary analysis not shown*, *the final version will*, *this section will*, o cualquier formulación equivalente. Las únicas referencias a futuro se ubican en la sección de limitaciones o trabajo futuro, y se refieren a extensiones reales no ejecutadas, no a partes pendientes del mismo manuscrito.

**Justificación.** El lenguaje prospectivo en una sección de resultados transmite que el manuscrito no está cerrado, que mezcla protocolo con hallazgos o que fue ensamblado por acumulación automática de bloques. Es una señal negativa inmediata para un revisor.

**Verificación.** Búsqueda textual obligatoria antes de cada envío sobre `will`, `planned`, `preliminary`, `not shown`, `to be completed`, `future`, `before submission`. Cada ocurrencia se elimina, se convierte a pasado/presente, o se conserva solo si está en *Future Work* (ver `01_task_list.md::7.3`).

---

## D19 — Uso de los antecedentes internos OLA/CLEI/WEA sin exponer la genealogía

**Contexto.** Los tres trabajos de conferencia previos (`FUZZY/1.-OLA2026/`, `FUZZY/2.-CLEI2026/`, `FUZZY/3.-WEA2026/`) contienen análisis, tablas y figuras cuya **estructura** es directamente aprovechable para el journal:

| Antecedente | Aporte estructural |
|---|---|
| OLA2026 | Narrativa de dependencia del paisaje; tabla PSO vs variantes fuzzy por función |
| CLEI2026 | Tabla "PSO vs best PSO_FCS per function"; performance–robustness map; heatmap de configuraciones; boxplots por función |
| WEA2026 | Ranking global + por función; análisis por grupos; **mirror-pair analysis**; tabla factorial semántica de reglas; trayectorias de `w(t)`; efecto de granularidad por regla |

**Alternativas.** A. Ignorarlos y rediseñar el análisis desde cero. B. Reutilizarlos y declarar explícitamente que el journal extiende los trabajos de conferencia. C. Usarlos como referencia interna de organización, reconstruyendo todo desde los datos actuales y sin declarar la genealogía.

**Decisión.** Opción C.

**Regla vinculante.**

> Los papers de conferencia pueden orientar la estructura de análisis, tablas, figuras y discusión, pero el manuscrito final **no** debe decir que "se inspira en", "se basa en", "extiende directamente", "reutiliza ideas de" o "toma como modelo" esos trabajos, salvo que exista una razón bibliográfica explícita y formal para citarlos. El artículo debe leerse como un trabajo científico autónomo, con su propia pregunta de investigación, metodología, resultados y contribución.

**Lenguaje prohibido.** *"This analysis is inspired by our previous conference paper"*, *"Following the structure of the CLEI paper"*, *"As in our WEA paper"*, *"This figure is adapted from the OLA version"*, *"We extend our previous conference results"*, y equivalentes.

**Lenguaje aceptable.** Formulaciones autónomas: *"To characterize the function-level behavior, we report the best configuration per benchmark function"*, *"A performance–robustness map is used to jointly examine final quality and dispersion"*, *"The rule bases are organized according to their semantic axes to support interpretability"*.

**Justificación.** Un journal presentado como extensión mecánica de tres conferencias propias invita a la pregunta de cuánto material es realmente nuevo, y expone el trabajo a objeciones de solapamiento. La contribución del journal es el diseño factorial completo (4 granularidades × 8 patrones × 62 instancias × 31 corridas), que ningún antecedente cubre. La opción A desperdiciaría diseño analítico ya validado sin beneficio alguno.

**Implicación operativa.** Todas las figuras y tablas se **regeneran desde los datos actuales**; ninguna se recicla. Checklist de verificación en `01_task_list.md::7.14`.

---

## D16 — Revista objetivo: MDPI *Mathematics*

**Contexto.** El objetivo inicial era MDPI *Biomimetics* (descuento disponible, scope de metaheurísticas bio-inspiradas). La revisión editorial planteó *Mathematics* como alternativa, con un nivel de formalización mayor.

**Alternativas.** A. Biomimetics, con la formalización como refuerzo opcional. B. *Mathematics*, con contribución formal obligatoria.

**Decisión.** Opción B, **confirmada por el autor el 2026-09-24**.

**Consecuencias vinculantes.**
1. La subsección `3.4 Formal characterization of the rule-base families` pasa de recomendable a **obligatoria**: definición de índices lingüísticos, función generadora de consecuentes $R_k(i,j)$, relación $n \mapsto n^2$ reglas, direccionalidad/monotonicidad de cada patrón, acotamiento de la superficie de control, preservación de cobertura y normalidad.
2. Las **propiedades verificadas del banco de reglas** (simetría especular, cierre bajo inversión semántica — ver D20) deben enunciarse como proposiciones, no como observaciones empíricas.
3. El diseño factorial debe justificarse matemáticamente, no solo describirse.
4. El manuscrito debe estar editorialmente cerrado: sin frases en futuro, sin placeholders, sin contradicciones entre tablas y texto, sin captions que contradigan figuras (D18).
5. Reproducibilidad: *Mathematics* valora datos, scripts y material suplementario; el repositorio debe estar listo antes del envío.

**Cambios ya aplicados.** `manuscript/main.tex` usa `\documentclass[journal=mathematics,...]`; los encabezados de los documentos de planificación y del manuscrito fueron actualizados.

---

## D20 — Simetría especular del banco de reglas (verificada en código)

**Contexto.** El análisis de pares espejo propuesto en la revisión editorial asume que R1↔R2, R3↔R4, R5↔R8 y R6↔R7 son pares espejo. La termografía de las matrices lo sugería, pero no estaba verificado contra el generador.

**Verificación.** Ejecutada sobre `make_rule_matrix` y sobre las superficies defuzzificadas, para $n \in \{3,5,7,9\}$ y las 28 combinaciones posibles de R1–R8. Test permanente en `FUZZY/4_verify_fis_properties.py::sección 7`.

**Resultado.** Exactamente cuatro pares cumplen la reflexión, y son los previstos:

| Par | Ejes invertidos | Propiedad verificada |
|---|---|---|
| R1 ↔ R2 | progreso | $i_a + i_b = n-1$ en las $n^2$ celdas |
| R3 ↔ R4 | diversidad | idem |
| R5 ↔ R8 | progreso **y** diversidad | idem |
| R6 ↔ R7 | progreso **y** diversidad | idem |

Además, en la superficie de control defuzzificada se cumple, hasta precisión de máquina ($<10^{-15}$):

$$w_{R_a}(d,p) + w_{R_b}(d,p) = w_{\min} + w_{\max} \quad \forall (d,p) \in [0,1]^2$$

Esto es consecuencia de tres propiedades combinadas: el modelo aditivo de `make_rule_matrix` (la inversión de un efecto cambia el signo del desplazamiento respecto del centro), la simetría de la partición Ruspini uniforme con hombros (D6, D7) y la linealidad del centroide con rescalado (D8). **Es un resultado enunciable como proposición en §3.4.**

**Matiz metodológico importante.** Los pares R5↔R8 y R6↔R7 invierten **ambos** ejes simultáneamente, de modo que **no aíslan un solo eje semántico**. Para atribuir un efecto a un único eje hay que usar:

| Par | Eje aislado | Contexto fijo |
|---|---|---|
| R5 vs R7 | dirección del progreso | diversidad = following |
| R6 vs R8 | dirección del progreso | diversidad = compensating |
| R5 vs R6 | reacción a la diversidad | progreso = decreasing |
| R7 vs R8 | reacción a la diversidad | progreso = increasing |

**Consecuencia para el análisis.** El *mirror-pair analysis* del manuscrito debe distinguir los dos tipos de comparación: los cuatro pares espejo miden el efecto de la **inversión semántica completa**; los cuatro pares de eje único miden el efecto **marginal** de cada factor. Confundirlos invalidaría la atribución causal.

---

## Apéndice — Referencias bibliográficas
- Mendel, J. M. (2001). *Uncertain Rule-Based Fuzzy Logic Systems*. Prentice Hall.
- Pedrycz, W. & Gomide, F. (2007). *Fuzzy Systems Engineering: Toward Human-Centric Computing*. IEEE Press / Wiley.
- Ruspini, E. H. (1969). A new approach to clustering. *Information and Control*, 15(1), 22–32.
- Yen, J. & Langari, R. (1999). *Fuzzy Logic: Intelligence, Control, and Information*. Prentice Hall.

---

## Apéndice — Historial de cambios de este documento

| Fecha | Cambio |
|---|---|
| 2026-06-27 | Creación inicial. Cubre decisiones D1–D12 de las fases 0 y 1. |
| 2026-09-24 | Añadidas D13–D18 (consolidación editorial); las recomendaciones fuente se preservan en `archive/editorial_guidance_sources_20261015/`. |
| 2026-09-24 (2.ª) | Ampliación del documento de recomendaciones (§12–13 + anexo A–G): añadida **D19** (uso de antecedentes internos sin exponer la genealogía). |
| 2026-09-24 (3.ª) | **D16 confirmada: revista objetivo pasa de Biomimetics a Mathematics.** Añadida **D20** (simetría especular del banco de reglas, verificada con test permanente en `FUZZY/4_verify_fis_properties.py`). |
