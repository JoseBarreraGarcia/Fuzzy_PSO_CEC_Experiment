# Plan de mejora científica y editorial

**Manuscrito:** *Sensitivity of Fuzzy-PSO Inertia Control to Linguistic Granularity and Rule-Base Structure*  
**Journal objetivo:** *Mathematics* (MDPI)  
**Documento de referencia:** versión compilada del 14 de octubre de 2026, 61 páginas; cuerpo principal hasta p. 31 y apéndices A–D en un solo PDF.  
**Estado:** Fases I–III completadas. T2 y T3 aprobadas, implementadas y validadas; no se modificaron resultados numéricos ni datos experimentales.

## 1. Objetivo y delimitación

Fortalecer la presentación y el valor interpretativo de los resultados **ya obtenidos** mediante síntesis tabulares agregadas, verificables y no redundantes. La ampliación crítica de **Introduction**, **Related Work** y **Discussion**, incluida la contrastación con literatura científica mediante Consensus, es una línea **separada**, a cargo del autor y ChatGPT. El agente de Visual Studio Code no debe adelantarse a esa revisión bibliográfica.

**Principio rector:** no confundir más estadísticas, más tablas o mejor presentación con mayor novedad científica demostrada. Cada tabla propuesta debe responder una pregunta concreta y aportar información que el lector no obtiene fácilmente de las Tablas 5–13 y Figuras principales.

## 2. Responsables y fronteras del trabajo

| Responsable | Alcance | No debe hacer |
|---|---|---|
| **Agente VS Code** | Auditar artefactos y scripts existentes; identificar vacíos de síntesis; verificar cálculos; generar prototipos de tablas y documentación de procedencia; detectar contradicciones entre cifras y texto; proponer ubicación MAIN/APPENDIX | Modificar datos brutos, ejecutar PSO, cambiar el diseño, reformular hipótesis, añadir pruebas inferenciales no acordadas, editar Introduction/Related Work/Discussion, buscar o inventar referencias |
| **Autor + ChatGPT + Consensus** | Verificar bibliografía; elaborar comparación crítica de trabajos anteriores; robustecer Introduction y Related Work; discutir resultados frente a fuentes comprobadas; revisar novedad científica y claims | Atribuir a la literatura resultados no verificados; prometer innovación matemática o causalidad no demostrada |
| **Autor** | Aprobar qué tablas se incorporarán, ubicación final y redacción científica; más adelante validar CRediT y preparar repositorio público | Publicar datos o atribuciones sin verificación y autorización |

## 3. Condiciones metodológicas inalterables

- **Diseño:** 4 granularidades (n = 3, 5, 7, 9) × 8 patrones R1–R8, más baseline PSO; 33 configuraciones, 62 instancias, 23 funciones, 31 corridas por celda y 63.426 ejecuciones totales.
- Arquitectura Mamdani común de dos entradas, inferencia min–max y control de inercia; cualquier comparación se refiere a los **patrones de consecuentes implementados**, no a eliminar o añadir entradas.
- **H3 está cerrado como análisis descriptivo exploratorio.** No reabrir tests de interacción, no buscar nuevos p-values, ni convertir dispersiones o rangos en inferencias confirmatorias.
- **R1 está cerrado.** Su neutralidad es de consecuentes nominales; la salida efectiva puede depender de diversidad por activación y agregación Mamdani. No afirmar que replica la recta lineal de PSO.
- No interpretar p no significativo como equivalencia o independencia.
- No atribuir causalmente resultados a clases de paisaje, modalidad o diversidad sin controles pertinentes.
- **Oracle** por instancia no es una política de selección desplegable.
- Todos los apéndices científicos permanecerán en **el mismo PDF**; no crear archivos independientes de Supplementary Materials.
- No modificar por ahora CRediT, Data Availability, título, referencias ni depósito público.

## 4. Fase I: auditoría e inventario antes de generar tablas

1. Identificar los resultados, CSV, scripts y fragmentos LaTeX **efectivamente existentes** que sustentan Tablas 5–13, Figura 5 (ranking/CD), Figura 6 (por clase), Figura 7 (S1/S2), Figuras 8–9 (granularidad), Tabla 12 (comparaciones PSO) y apéndices.
2. Construir una **matriz de cobertura**: pregunta H1–H5 → estadísticos ya publicados → representación actual → información difícil de localizar → tabla candidata.
3. Comprobar que los agregados usan unidades compatibles: *run*, instancia función–dimensión, función y subconjunto/clase. Indicar siempre si primero se agregan 31 corridas, luego dimensiones o instancias, y cómo se pondera cada función.
4. Identificar denominadores, tratamiento de empates, normalización de gap, clipping, escalas logarítmicas, y nivel de corrección de multiplicidad. No mezclar conteos nominales y corregidos.
5. Examinar si propuestas duplican Tablas 5, 6, 7, 8, 9, 11 o 12. Documentar por qué una tabla nueva se justificaría frente a modificar una existente.

**Entregable Fase I (COMPLETADO, 2026-10-14):** matriz de cobertura y candidatas priorizadas, entregadas y aprobadas. Auditoría de solo lectura; no se modificaron datos ni el manuscrito en esta fase.

## 5. Fase II: propuestas de tablas agregadas (prototipos, no inserción automática)

### Candidata T1: síntesis de granularidad × patrones de consecuentes — NO REQUERIDA

**Pregunta:** ¿qué diferencias descriptivas exhiben los niveles de granularidad y las familias de reglas dentro del factorial realizado?

Proponer una tabla compacta que separe claramente:
- Por granularidad n: ranking medio agregado sobre patrones, mejor rango observado, dispersión entre los ocho patrones y cantidad de reglas n² (9, 25, 49, 81).
- Por patrón R1–R8, si agrega valor y no reproduce Tabla 11: rango medio sobre granularidades y spread entre granularidades.
- Si se resume por familia de progreso (decreasing/neutral/increasing), aclarar composición y agregación; no inferir *main effects* independientes ni causalidad.

**Criterio de no redundancia:** antes de añadir T1, evaluar si basta **mejorar Tabla 11** o agregar un pequeño panel, en vez de crear otra tabla con valores repetidos.

**Reglas:** los rangos Friedman son relativos a 33 configuraciones dentro de instancias; no describir promedio de rangos como magnitud de mejora en fitness. Evitar ANOVA, tamaños de efecto o pruebas de interacción no validadas. Distinguir SD de rangos globales, SD por función, spreads max–min y dispersión de gaps: **son estimandos diferentes**.

### Candidata T2: resultados agregados por clase de benchmark — IMPLEMENTADA EN FASE III

**Pregunta:** ¿dónde cambia el liderazgo y cuánta heterogeneidad se observa entre grupos del benchmark?

Filas sugeridas, respetando la clasificación existente:
- F1–F7: unimodal, 28 instancias.
- F8–F13: scalable multimodal, 24 instancias.
- F14–F23: fixed-dimensional, 10 instancias.

Columnas candidatas: número de funciones/instancias; configuración de menor ranking **dentro de la clase** y valor/rango (definir criterio); posición del PSO en esa clase; rango de FCS-3-R1; síntesis de concordancia relevante (si no repite innecesariamente Tabla 8). Incluir incertidumbre solo si existe un procedimiento apropiado predefinido; no inventarla.

**Control crucial:** no etiquetar F14–F23 como efecto puro de modalidad o de dimensionalidad; el régimen dimensional y las familias de funciones están confundidos. Distinguir **mejor fijo según ranking agregado de clase** de **ganador oracle por instancia**. No declarar transferibilidad a problemas externos.

**Criterio de no redundancia:** comparar T2 con Tabla 7, Tabla 8 y Figuras 6–7. Si basta adaptar una tabla actual, proponer esa solución más breve.

### Candidata T3: mejorar Tabla 6, H1–H5 — IMPLEMENTADA EN FASE III

Revisar si se puede reemplazar o ajustar la tabla de preguntas existente para tener: **pregunta | evidencia | hallazgo | alcance/limitación**. H3 debe permanecer descriptiva; H4 debe diferenciar comparaciones nominales y Bonferroni; H2/H5 deben evitar afirmar independencia o transferibilidad general; H1 debe distinguir ranking líder de significancia Nemenyi.

No crear otra tabla-resumen si Tabla 6 se puede mejorar conservando la correspondencia con H1–H5.

### Candidata T4: otros agregados solo si revelan un vacío real — NO REQUERIDA

Pueden examinarse, sin compromiso de inclusión, la distribución de victorias corregidas por regla/granularidad y la heterogeneidad del overhead. No incorporar por volumen ni por tener disponibles los datos. Cada propuesta requiere pregunta, unidad de agregación, procedencia y beneficio explícito.

## 6. Fase III: trazabilidad, implementación y verificación (COMPLETADA, 2026-10-14)

Se completaron los controles de procedencia, unidad de análisis, denominadores y redundancia. T2 se incorporó en Section 5.3 como Table 8; informa posiciones por media de medianas de gap normalizado y aclara que no son Friedman mean ranks. T3 reemplazó Table 6 con cuatro columnas para H1–H5 y sus límites interpretativos. Ambos usos coinciden con los resúmenes archivados.

La docstring H1 ahora documenta `gap_final` como métrica predeterminada, la mediana de 31 corridas por configuración–instancia, los rangos promedio para empates y Friedman/Nemenyi sobre 62 bloques, además de la opción `fitness_best`. No cambió la implementación estadística. La documentación de nombres ahora especifica que `composed` mapea exactamente a F14–F23 y se presenta como “fixed-dimensional”; claves y asignación permanecen iguales.

El PDF final conserva 61 páginas, el artículo principal hasta p. 31 y los apéndices A–D y referencias en el mismo archivo. Table 6 aparece en p. 15, Table 8 en p. 21 y Table 9 en p. 22. Se verificaron las etiquetas automáticas, referencias, 54 elementos con caption y legibilidad de las tablas. No se ejecutaron PSO ni nuevas pruebas estadísticas.

Los pasos siguientes registran la trazabilidad aplicada durante esta fase; no son tareas pendientes para volver a calcular o regenerar resultados.

Para cada tabla candidata:

1. Identificar archivos fuente exactos y scripts/generadores responsables.
2. Dar la fórmula o secuencia de agregación (pseudocódigo suficiente), unidad de análisis, denominador, ponderación y tratamiento de ties.
3. Contrastar valores coincidentes con las tablas/figuras actuales, sin sobreescribir resultados.
4. Probar invariantes verificables: 33 configuraciones, 62 instancias, 23 funciones, 31 runs y 63.426 registros; comprobar excepciones y semillas compartidas según protocolo.
5. Marcar cualquier diferencia entre valores computados y manuscrito: **no corregir silenciosamente**; clasificarla y explicar posible origen.
6. Crear, si hace falta, scripts de **solo lectura sobre datos originales** para agregados descriptivos; registrar entradas/salidas y versiones. No reejecutar el optimizador ni alterar análisis validados.
7. Producir prototipos de tabla (Markdown y/o fragmentos TeX en espacio de trabajo separado), con captions autodescriptivos, escalas, unidades y notas de alcance. **No insertarlos en main.tex ni 05_results.tex sin autorización.**

## 7. Decisión editorial de Fase III (APROBADA E IMPLEMENTADA)

Decisión final: T2 se implementa en el cuerpo principal, Section 5.3. T3 sustituye la Table 6 existente. T1 no se requiere porque la Tabla 11 y sus figuras ya cubren ese resumen; T4 no se requiere porque no se identificó un vacío adicional. No se añadieron tablas distintas de T2 ni la Table 6 revisada.

Los criterios editoriales aplicados para esas decisiones fueron:

| Campo | Requisito |
|---|---|
| Identificador | T1, T2, T3... |
| Pregunta que responde | Formulación concreta |
| Evidencia/valores | Derivada de datos existentes, identificando fuente |
| Novedad frente a tablas actuales | Qué añade realmente |
| Destino sugerido | MAIN / APPENDIX A o B / NO AÑADIR / MODIFICAR EXISTENTE |
| Coste editorial | Filas, columnas, espacio estimado, modificaciones de texto |
| Riesgo inferencial | Interpretación incorrecta que debe evitarse |
| Estado | Implementada / no requerida / reservada para flujo separado |

**Preferencia editorial:** mantener el cuerpo principal concentrado (~31 páginas actualmente); trasladar documentación exhaustiva a apéndices **del mismo PDF**. El total de páginas puede crecer moderadamente si existe valor científico claro. No perseguir un número artificial de tablas.

## 8. Trabajo reservado para autor + ChatGPT + Consensus (NO ejecutar por el agente)

En una fase posterior y coordinada:

1. Verificar literatura específica sobre ajuste de inercia en PSO, Mamdani/type-1/type-2 FIS, granularidad, rule-base design, análisis de sensibilidad y configuración de metaheurísticas.
2. Elaborar matriz crítica de estudios previos: variables modificadas, controles, benchmarks, tratamiento estadístico y contribución; no suponer ausencia de factoriales sin comprobar fuentes.
3. Revisar la Introducción y Related Work para justificar **por qué importa científicamente** aislar decisiones estructurales bajo arquitectura controlada.
4. Fortalecer la Discusión con contraste explícito y verificable de: (a) complejidad representacional vs. mejora efectiva; (b) semántica de consecuentes vs. comportamiento efectivo bajo Mamdani; (c) simetría matemática de controladores vs. asimetría de resultados; (d) robustez global vs. especialización por función, y diferencia respecto de selección oracle.
5. Revisar afirmaciones residuales de 'attributable to', 'main effects', 'interaction' en Introduction y Related Work para alinearlas con alcance descriptivo de H3. No afirmar partición causal o inferencia confirmatoria no realizada.
6. Actualizar Discussion y conclusiones **solo después** de decidir las tablas aceptadas y verificar publicaciones originales.

## 9. Criterios de cierre y prohibiciones

**Cierre de Fases I–III (COMPLETADO, 2026-10-14):** diagnóstico y matriz entregados; T2 y T3 implementadas y verificadas contra resultados archivados; T1 y T4 no requeridas; PDF compilado, con estructura y referencias validadas. No se introdujeron cálculos estadísticos nuevos ni se modificaron datos.

**Prohibido:** ejecutar PSO, alterar datos CSV, editar generadores que cambien análisis ya aprobados, introducir tests inferenciales nuevos, reabrir H3/R1, editar bibliografía o Related Work, usar referencias inventadas, sobrerreclamar novedad, modificar CRediT o Data Availability, mover apéndices a archivos separados, publicar código o datos, y reescribir el artículo integralmente.

## 10. Formato de respuesta solicitado al agente (FASES I–II COMPLETADAS)

Responder con estas secciones:

1. **Audit of existing aggregate evidence**: cobertura y vacíos reales.
2. **Candidate tables**: prototipos completos con valores respaldados, fuente y cálculo.
3. **Reconciliation with existing manuscript**: coincidencias, diferencias y posibles duplicaciones.
4. **Recommended placement**: MAIN / apéndice del PDF / no incluir / adaptar tabla actual.
5. **Risks and limitations**: dependencia, agrupación, inferencia y sobreclaims.
6. **Files created or changed**: indicar expresamente si no modificó fuentes del manuscrito ni datos.
7. **Author approval required**: decisiones concretas, ordenadas por impacto.

**Fases I–III:** completadas. **Trabajo restante en el flujo separado de revisión bibliográfica:** verificar literatura con el autor, ChatGPT y Consensus; fortalecer Introduction y Related Work; contrastar Discussion y el posicionamiento de la contribución con fuentes verificadas. Esos cambios quedan fuera de esta implementación y requieren revisión/aprobación de los autores.
