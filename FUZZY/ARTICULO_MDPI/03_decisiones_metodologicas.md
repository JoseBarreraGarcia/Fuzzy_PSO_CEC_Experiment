# Decisiones metodológicas — Paper MDPI (Scalable Fuzzy PSO Partitions)

> **Propósito:** registro auditable de las decisiones de diseño tomadas en las fases 0–1 del proyecto. Cada entrada documenta el contexto, las alternativas evaluadas, la decisión final y la justificación (con referencias citables cuando aplica). Este documento es la fuente primaria para redactar la sección *Materials and Methods* del manuscrito y para responder eventuales preguntas de revisores.

**Última actualización:** 2026-06-27
**Estado del proyecto:** Fase 1 completa (FIS paramétrico validado). Fase 2 pendiente.

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

---

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

**Implicación sobre las hipótesis (`04_hipotesis_metricas_analisis.md`).** La hipótesis **H5** (no existe configuración óptima única en todo el benchmark) es **la hipótesis clave** del paper MDPI: si se sostiene, justifica toda la línea de tesis posterior; si se rechaza, debilita la motivación de la tesis y obliga a replantear la propuesta. Las hipótesis H1–H4 son evidencia complementaria.

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
- **Alineado con el alcance de MDPI Biomimetics** (bio-inspired + fuzzy control + ablation/sensitivity studies).

**Hipótesis derivadas:** ver `04_hipotesis_metricas_analisis.md`. La hipótesis **H5** es la clave del paper: la no existencia de un óptimo único global motiva la tesis.

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
