# Recomendaciones editoriales para fortalecer el paper Fuzzy-PSO

## Diagnóstico general

El manuscrito tiene una estructura defendible como artículo único de análisis factorial. La idea central es pertinente: estudiar la sensibilidad del controlador difuso de inercia en PSO frente a dos factores de diseño, la granularidad lingüística y la estructura de reglas. Sin embargo, en su estado actual el paper todavía se lee más como un informe experimental agregado que como un artículo final de journal.

La recomendación principal es **no dividirlo ahora en dos artículos**. Conviene primero consolidarlo como un artículo factorial sólido y dejar para un segundo paper la propuesta adaptativa o meta-controladora basada en los resultados obtenidos.

La narrativa más fuerte debería ser:

> Bajo un diseño factorial controlado, la estructura de reglas explica más el desempeño del Fuzzy-PSO que el aumento del número de etiquetas lingüísticas, y no existe evidencia suficiente de una configuración estática universalmente transferible entre clases de funciones.

---

## 1. Reforzar los resultados por función individual

El principal punto débil actual es que los resultados están demasiado agregados. El paper presenta rankings globales, análisis por clase de problema y pruebas estadísticas generales, pero falta mostrar con mayor claridad qué ocurre función por función.

Esto es importante porque el propio artículo sostiene que no existe una configuración universalmente dominante y que el desempeño depende del tipo de paisaje de optimización. Para sostener esa afirmación, no basta con rankings globales o clases agregadas; es necesario mostrar evidencia a nivel de F1, F2, ..., F23.

### Mejora recomendada

Agregar una tabla o figura tipo heatmap con resultados por función individual.

Una tabla útil sería:

| Function | Problem type | Best configuration | Best `n` | Best rule | PSO rank | Best FCS rank | Gain/loss vs PSO | Significant? |
|---|---|---:|---:|---:|---:|---:|---:|---|
| F1 | Unimodal | ... | ... | ... | ... | ... | ... | ... |
| F2 | Unimodal | ... | ... | ... | ... | ... | ... | ... |
| F3 | Unimodal | ... | ... | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

No es necesario incluir las 32 configuraciones completas en el cuerpo principal. Se puede mostrar una tabla sintética en el manuscrito y dejar la matriz completa en material suplementario.

### Objetivo editorial

El lector debe poder responder rápidamente:

- ¿en qué funciones gana claramente el Fuzzy-PSO?
- ¿en qué funciones PSO clásico sigue siendo competitivo?
- ¿en qué funciones domina R1?
- ¿en qué funciones cambian las mejores reglas?
- ¿la ventaja global se distribuye en muchas funciones o se concentra en pocas?

---

## 2. Separar resultados globales, por clase y por función

La sección de resultados debería seguir una progresión analítica más clara.

### Estructura recomendada

```text
5.1 Global ranking of configurations
5.2 Performance by problem class
5.3 Function-level analysis
5.4 Dimensional scaling
5.5 Baseline comparison against classical PSO
5.6 Inertia-weight dynamics
```

### Lógica esperada

**Nivel 1: resultado global.**  
Ranking medio de todas las configuraciones en las 62 instancias. Este nivel ya existe, pero deben corregirse inconsistencias numéricas entre texto y tablas.

**Nivel 2: resultado por clase de problema.**  
Comparación entre funciones unimodales, multimodales escalables y funciones multimodales/composite de dimensión fija.

**Nivel 3: resultado por función individual.**  
Este nivel falta y debe agregarse. Es clave para validar la afirmación de que la mejor configuración depende del paisaje de optimización.

---

## 3. Corregir inconsistencias internas y pasar todo a redacción final

Este punto debe tratarse como una regla editorial estricta. El manuscrito no puede conservar lenguaje propio de planificación, reporte de agente o documento en construcción si ya presenta resultados empíricos.

En la versión actual hay fragmentos redactados como si los resultados aún fueran futuros o estuvieran planificados. Esto genera una señal negativa para un revisor, porque transmite que el manuscrito no está cerrado, que mezcla protocolo con resultados, o que fue producido por acumulación automática de bloques.

### Problema editorial

No puede quedar lenguaje como:

- “the results section will report...”
- “the discussion will assess...”
- “the final conclusion will summarize...”
- “planned analyses...”
- “will be completed before submission...”
- “preliminary analysis not shown...”
- “the exact tests will be frozen...”

Ese tipo de frases son aceptables en un protocolo interno, una propuesta experimental o un informe de avance, pero no en un artículo final con resultados ya ejecutados.

### Regla editorial para trabajar con agentes

Usar la siguiente regla como instrucción permanente para cualquier agente que edite el paper:

> **Regla editorial de versión final:**  
> Todo texto del manuscrito debe estar redactado como artículo científico final, no como plan de trabajo, protocolo pendiente, informe de avance ni reporte de agente. Si una sección contiene resultados, el texto debe describir lo que se hizo, lo que se observó y lo que se concluye. Queda prohibido dejar expresiones prospectivas o de planificación tales como “will report”, “will assess”, “planned analysis”, “to be completed”, “future results”, “preliminary analysis not shown”, “the final version will”, “this section will”, o cualquier formulación equivalente. Las únicas referencias a futuro deben ubicarse en la sección de limitaciones o trabajo futuro, y deben referirse a extensiones reales no ejecutadas, no a partes pendientes del mismo manuscrito.

### Conversión esperada de lenguaje

| Lenguaje no aceptable | Reemplazo esperado |
|---|---|
| “The results section will report the effects...” | “The results show the effects...” |
| “The discussion will assess whether...” | “The discussion shows that...” |
| “The final conclusion will summarize...” | “The conclusion summarizes...” |
| “The planned inferential analysis uses...” | “The inferential analysis used...” |
| “The exact tests will be frozen before analyzing...” | Eliminar si el análisis ya fue ejecutado, o mover al protocolo suplementario si corresponde. |
| “Author contributions will be completed...” | Redactar contribuciones reales o eliminar hasta tener la versión final. |
| “The database will be deposited...” | “The database has been deposited...” o “The database will be deposited before publication”, según el estado real. |

### Revisión específica recomendada

Antes de enviar, hacer una búsqueda textual en todo el manuscrito de:

```text
will
planned
preliminary
not shown
to be completed
future
before submission
will report
will assess
will summarize
will be deposited
```

Cada aparición debe clasificarse en una de tres categorías:

1. **Debe eliminarse**, porque corresponde a texto de trabajo interno.
2. **Debe convertirse a pasado/presente**, porque el resultado ya existe.
3. **Puede quedar solo si está en Future Work**, y si se refiere a una extensión real no ejecutada.

### Objetivo editorial

El artículo debe leerse como una investigación cerrada. No debe parecer un borrador generado por partes, ni una salida de agente pendiente de curación humana.

---

## 4. Agregar curvas de convergencia por funciones representativas

El manuscrito indica que se registran fitness, diversidad, progreso e inertia weight por iteración. Sin embargo, los resultados explotan poco esa información dinámica.

Para que el artículo no sea solo una comparación de rankings y tablas agregadas, conviene incluir curvas de convergencia para funciones representativas.

### Funciones sugeridas

- F1 o F2: unimodal simple.
- F5: Rosenbrock, por su valle estrecho y dificultad estructural.
- F9 o F10: multimodal escalable.
- F14 o F15: multimodal fija clásica.
- F21-F23: Shekel, multimodal/deceptive de baja dimensión.

### Configuraciones sugeridas para mostrar

En cada curva:

- PSO clásico.
- Mejor Fuzzy-PSO global.
- Mejor Fuzzy-PSO para esa clase de problema.
- Una configuración claramente inferior como contraste.

### Métricas visuales

- Curva mediana de mejor fitness.
- Banda intercuartílica.
- Escala logarítmica cuando corresponda.
- Misma escala entre configuraciones para evitar interpretaciones visuales engañosas.

### Objetivo editorial

Mostrar no solo quién gana, sino **cómo gana**:

- convergencia temprana;
- estabilidad final;
- estancamiento;
- exploración tardía;
- sensibilidad a multimodalidad.

---

## 5. Fortalecer la contribución matemática

Para un envío a *Mathematics*, el artículo no debería parecer únicamente un benchmark empírico. Debe reforzar su dimensión formal.

### Mejoras recomendadas

Formalizar con mayor precisión:

1. La familia de particiones triangulares Ruspini.
2. El generador de reglas `R_k(i,j)`.
3. La relación entre granularidad `n` y número de reglas `n^2`.
4. La superficie de control inducida por cada regla.
5. La monotonicidad o direccionalidad de cada regla respecto de diversidad y progreso.
6. La complejidad interpretativa asociada al crecimiento del número de etiquetas.
7. La justificación de usar granularidades impares `n in {3, 5, 7, 9}`.

### Posible subsección nueva

```text
3.4 Formal characterization of the rule-base families
```

Contenido sugerido:

- definición de índices lingüísticos;
- función generadora de consecuentes;
- clasificación de reglas por comportamiento exploratorio/explotativo;
- propiedades básicas de acotamiento;
- preservación de cobertura y normalidad de las particiones.

### Objetivo editorial

Que el artículo no sea leído solo como “se probaron muchas variantes”, sino como una contribución metodológica para estudiar familias parametrizadas de controladores Mamdani.

---

## 6. Reposicionar el mensaje central del artículo

La narrativa actual debe evitar sonar como una exploración masiva de configuraciones.

### Formulación débil

> Se probaron 32 configuraciones de Fuzzy-PSO en F1-F23.

### Formulación fuerte

> Se realizó un estudio factorial controlado para aislar los efectos de la granularidad lingüística y la estructura de reglas en un controlador Mamdani de inercia para PSO.

### Contribución central sugerida

> Los resultados muestran que la estructura de reglas tiene mayor influencia que el aumento de granularidad lingüística, que las mejoras frente a PSO dependen del tipo de función, y que no hay evidencia de una configuración estática universalmente dominante.

### Implicación para la tesis

Este artículo puede funcionar como base empírica para justificar un segundo paper sobre selección adaptativa de esquemas difusos:

```text
Paper 1: Static factorial sensitivity analysis
Paper 2: Adaptive semantic scheme selection / meta-controller
```

---

## 7. Mejorar la sección de limitaciones

La sección de limitaciones está bien planteada, pero debe hacerse más precisa.

### Limitaciones que conviene declarar explícitamente

- Solo se usaron funciones de pertenencia triangulares.
- Solo se evaluaron particiones Ruspini uniformes.
- No se evaluaron funciones gaussianas, trapezoidales ni asimétricas.
- No se variaron niveles de solapamiento.
- No se evaluaron otros métodos de defuzzificación.
- No se adaptaron simultáneamente `c1`, `c2` ni `vmax`.
- Solo se utilizó un tamaño de población.
- Solo se consideró PSO clásico como baseline principal.
- No se evaluaron benchmarks desplazados o rotados tipo CEC.
- No se propuso todavía un mecanismo adaptativo de selección de reglas o particiones.

### Forma correcta de presentarlo

Estas limitaciones no deben presentarse como debilidades graves, sino como decisiones de control experimental:

> These restrictions were deliberate: they allow the study to isolate the effects of linguistic granularity and rule-base structure without confounding them with membership-function shape, overlap, defuzzification, or multi-parameter PSO adaptation.

---

## 8. Reforzar reproducibilidad y datos abiertos

Antes del envío, conviene tener preparados los materiales suplementarios.

### Material mínimo recomendado

- Repositorio GitHub o Zenodo.
- DOI del dataset, si es posible.
- CSV finales.
- Scripts para reproducir tablas y figuras.
- Archivo de configuración de las 32 variantes.
- Semillas utilizadas.
- README con instrucciones mínimas.
- Base SQLite, si no es demasiado pesada.
- Material suplementario con rankings completos.

### Declaración sugerida

```text
The full experimental configuration, random seeds, raw results, processed CSV files, and analysis scripts are available in the associated repository. The repository includes the rule-bank generator, the fuzzy-partition generator, and the scripts required to reproduce all tables and figures reported in this article.
```

Si todavía no está depositado, no afirmar que está disponible. Usar una versión provisional solo internamente y actualizar antes del envío.

---

## 9. Ajustar figuras y material suplementario

El artículo tiene muchas figuras útiles, pero algunas pueden pasar al suplemento.

### Mantener en el cuerpo principal

- Una figura representativa de particiones.
- Una figura de rule bases.
- Una figura de superficies de control.
- Ranking global de configuraciones.
- Heatmap por clase de problema.
- Tabla por función individual.
- Curvas de convergencia representativas.
- Figura Pareto o ranking por clase.

### Mover al suplemento

- Todas las matrices completas de reglas para cada `n`.
- Rankings completos de las 32 configuraciones.
- Resultados completos por función y dimensión.
- Todas las curvas de convergencia.
- Todas las pruebas estadísticas extendidas.
- Detalles completos de seeds y ejecuciones.

### Objetivo editorial

Reducir ruido visual en el manuscrito principal y dejar el cuerpo del artículo concentrado en la historia científica.

---

## 10. Revisar hipótesis y criterios de decisión

El paper incluye hipótesis H1-H5, pero algunas decisiones deben justificarse mejor.

### Aspectos a revisar

- Justificar por qué H4 usa un criterio de 50% de instancias.
- Separar significancia estadística de relevancia práctica.
- Reportar tamaños de efecto junto con p-values.
- Aclarar si las hipótesis fueron definidas antes o después de mirar los resultados.
- Evitar criterios de decisión que parezcan arbitrarios.
- Asegurar que los subconjuntos usados en H5 sean consistentes en texto, tabla y figura.

### Recomendación

Si las hipótesis fueron definidas durante el análisis exploratorio, no presentarlas como hipótesis confirmatorias fuertes. Presentarlas como preguntas de investigación o análisis explicativo.

Ejemplo:

```text
Rather than confirmatory hypotheses, H1-H5 are treated as structured research questions guiding the factorial interpretation of the experiment.
```

Esto reduce riesgo editorial.

---

## 11. Corregir inconsistencias numéricas y de nomenclatura

Antes de cualquier envío, revisar de forma sistemática:

### Números

- Ranking medio en texto versus ranking medio en tablas.
- Número de wins/ties/losses.
- Número de ejecuciones totales.
- Número de instancias.
- Definición de dimensiones para F1-F13 y F14-F23.
- Valores de Kendall tau.
- Valores de p-value.
- Criterio Bonferroni.
- Slope de escalamiento dimensional.

### Nomenclatura

Uniformar:

- `n=3` versus `G3`.
- `PSO_FCS:O1:3:I1:R1` versus `PSO_FCS:G3:I1:R1:O1`.
- `rule set` versus `rule-base pattern`.
- `composed` versus `fixed-dimensional multimodal/composite`.
- `gap_final`, `gap_median`, `normalized gap`.
- `F1-F13` versus `S1`; `F14-F23` versus `S2`.

### Regla

Una configuración debe tener un único formato de nombre en todo el artículo.

Ejemplo recomendado:

```text
PSO_FCS(n=3, R=R1)
```

o

```text
FCS-3-R1
```

Usar nombres largos solo en tablas suplementarias o scripts.

---

## 12. Mejorar la discusión

La discusión debe interpretar, no repetir resultados.

### Preguntas que debe responder

1. ¿Por qué R1 funciona mejor globalmente?
2. ¿Por qué aumentar `n` no mejora necesariamente el desempeño?
3. ¿Qué indica que la regla sea más importante que la granularidad?
4. ¿Qué clases de funciones favorecen reglas más exploratorias o más explotativas?
5. ¿Qué significa que no exista una configuración estática dominante?
6. ¿Qué implicancia tiene esto para futuros meta-controladores difusos?

### Idea interpretativa fuerte

Si la estructura de reglas domina sobre la granularidad, entonces el problema principal no es solo “cuántas etiquetas usar”, sino **qué política de control induce la base de reglas**.

Esto conecta directamente con tu línea doctoral: selección dinámica de esquemas difusos.

---

## 13. Consideraciones específicas para enviar a *Mathematics*

Si el target inicial es *Mathematics*, conviene cuidar tres aspectos:

### 13.1. Aporte formal

El journal puede recibir trabajos aplicados, pero el manuscrito debe mostrar suficiente formalización. Por eso es importante reforzar definiciones, propiedades del controlador, generación de reglas y justificación matemática del diseño factorial.

### 13.2. Reproducibilidad

MDPI suele valorar datos, scripts y material suplementario. Conviene preparar un repositorio limpio antes del envío.

### 13.3. Claridad editorial

El manuscrito debe estar completamente cerrado:

- sin frases en futuro sobre resultados;
- sin placeholders;
- sin nombres de journal genéricos;
- sin contradicciones entre tablas y texto;
- sin captions que contradigan figuras;
- sin hipótesis mal alineadas con los resultados.

---

## Prioridades antes del envío

### Prioridad alta

1. Corregir lenguaje de planificación y convertir todo a redacción final.
2. Corregir inconsistencias numéricas.
3. Agregar análisis por función individual.
4. Revisar contradicción de Figura 10.
5. Uniformar nombres de configuraciones y subconjuntos.
6. Reescribir discusión con interpretación real de resultados.

### Prioridad media

7. Agregar curvas de convergencia representativas.
8. Fortalecer formalización matemática.
9. Mejorar limitaciones.
10. Preparar material suplementario.

### Prioridad baja

11. Ajustar estética de figuras.
12. Reducir redundancia de tablas.
13. Mejorar título y resumen final.

---

## Decisión final recomendada

No dividir el artículo en dos en esta etapa.

Primero conviene consolidar este manuscrito como:

> **A controlled factorial study of linguistic granularity and rule-base structure in fuzzy inertia control for PSO.**

Después, usar sus resultados como base para un segundo artículo:

> **Adaptive selection of fuzzy semantic schemes for PSO parameter control.**

La progresión doctoral queda más sólida así:

```text
1. Evidencia empírica de sensibilidad estática
2. Identificación de ausencia de configuración universal
3. Propuesta de selector adaptativo o meta-controlador difuso
```

Esta secuencia es más atractiva que dividir artificialmente el estudio actual en dos artículos menores.


---

# Anexo operativo para el agente: análisis, figuras y tablas inspiradas en los papers de conferencia

## Uso de los antecedentes

Este anexo está dirigido al agente que trabajará sobre el manuscrito extendido. Su función es indicar qué análisis, tablas y figuras pueden reutilizarse, ampliarse o reformularse a partir de los trabajos previos ubicados en las carpetas del proyecto:

```text
FUZZY\1.-OLA2026 FUZZY
FUZZY\2.-CLEI2026 FUZZY
FUZZY\3.-WEA2026
```

El agente debe revisar los archivos de esas carpetas como antecedentes internos de diseño experimental, organización de resultados y recursos visuales. No debe copiar texto sin revisión, no debe trasladar frases de conferencia sin adaptación, y no debe presentar el manuscrito de journal como una simple extensión mecánica de esos papers.

## Regla editorial estricta sobre antecedentes internos

> **Regla de no exposición de antecedentes internos:**  
> Los papers de conferencia pueden usarse para orientar la estructura de análisis, tablas, figuras y discusión, pero el manuscrito final no debe decir que “se inspira en”, “se basa en”, “extiende directamente”, “reutiliza ideas de”, o “toma como modelo” esos trabajos, salvo que exista una razón bibliográfica explícita y formal para citarlos. El artículo debe leerse como un trabajo científico autónomo, con su propia pregunta de investigación, metodología, resultados y contribución. Las referencias a los papers de conferencia deben quedar fuera del manuscrito principal, salvo que se decida citarlos formalmente por razones académicas justificadas.

### Lenguaje prohibido en el manuscrito final

No usar frases como:

```text
This analysis is inspired by our previous conference paper...
Following the structure of the CLEI paper...
As in our WEA paper...
This figure is adapted from the OLA version...
The conference papers suggested that...
We extend our previous conference results...
```

### Lenguaje aceptable si corresponde metodológicamente

Usar formulaciones autónomas:

```text
To characterize the function-level behavior, we report the best configuration per benchmark function.
A performance–robustness map is used to jointly examine final quality and dispersion.
The rule bases are organized according to their semantic axes to support interpretability.
The inertia-weight trajectories are analyzed to connect rule semantics with search dynamics.
```

---

## A. Elementos del paper OLA2026 que pueden alimentar el journal

### A.1. Narrativa de dependencia del paisaje

El trabajo de OLA2026 es útil por su narrativa clara: el fuzzy control no se presenta como universalmente superior, sino como dependiente del tipo de paisaje. Esa idea debe preservarse en el journal, pero ampliada a todas las funciones y configuraciones.

### Uso recomendado en el journal

Incorporar una discusión que distinga explícitamente:

- funciones unimodales o estructuralmente regulares;
- funciones multimodales escalables;
- funciones multimodales de baja dimensión;
- funciones tipo Shekel o deceptive multimodal.

El objetivo no es decir que “el journal confirma OLA2026”, sino construir una interpretación propia:

> El efecto del controlador difuso depende del paisaje de optimización. En algunos grupos de funciones, la modulación adaptativa de la inercia puede ser innecesaria o contraproducente; en otros, puede mejorar robustez y reducir sensibilidad a óptimos locales.

### A.2. Tabla PSO versus variantes fuzzy

El paper OLA2026 contiene una tabla simple de comparación entre PSO y variantes PSO_FCS por función, con media, desviación estándar, gap y tiempo. Esa estructura es útil, pero para journal debe ampliarse y modernizarse.

### Versión recomendada para el journal

```text
Function | Dim. | Type | PSO median | Best FCS median | Best FCS config | Improvement | Std. reduction | p-value | Effect size | Overhead
```

Esta tabla debe responder directamente:

- dónde gana PSO;
- dónde gana FCS;
- cuánto gana;
- si la mejora es significativa;
- si la mejora es práctica;
- cuánto cuesta computacionalmente.

### A.3. Mensaje interpretativo

La versión journal no debe afirmar solo que “FCS mejora o empeora”. Debe explicar por qué:

- en funciones regulares, el descenso lineal de inercia puede ser suficiente;
- en funciones multimodales, la respuesta a diversidad puede ayudar a escapar o evitar convergencia prematura;
- en algunas funciones, más granularidad no compensa una mala política de reglas.

---

## B. Elementos del paper CLEI2026 que pueden alimentar el journal

### B.1. Tabla “PSO vs best PSO_FCS per function”

El paper CLEI2026 ofrece una estructura muy útil: por cada función se reporta el ganador, la mejor configuración FCS, mejora porcentual, reducción de desviación estándar, p-value y overhead.

### Uso recomendado en el journal

Esta tabla debe estar en el cuerpo principal, extendida a F1-F23 o a todas las instancias si F1-F13 se evalúan en varias dimensiones.

Tabla sugerida:

```text
Function | Dim. | Problem class | Winner | Best FCS | Best n | Best rule | Improvement % | Std. reduction % | p-value | Effect size | Overhead %
```

### Reglas para construirla

- Si `f* = 0`, no usar gap porcentual clásico con división por cero.
- Usar fitness absoluto, normalized gap alternativo o log gap según corresponda.
- Separar mejora estadística de mejora práctica.
- No declarar “wins” si no hay significancia o efecto práctico suficiente.
- Si hay empate estadístico, reportarlo como empate, no como victoria.

---

### B.2. Performance–robustness map

El paper CLEI2026 usa una figura tipo mean fitness versus standard deviation, con PSO como referencia. Esta idea debe mantenerse porque ayuda a interpretar robustez, no solo promedio.

### Versión recomendada para el journal

```text
x-axis: median or mean normalized gap
y-axis: standard deviation, IQR, or coefficient of variation
color: rule base R1-R8
marker: granularity n = 3, 5, 7, 9
star or black marker: PSO baseline
panel: representative functions or problem classes
```

### Objetivo

Mostrar visualmente si una configuración:

- mejora media y robustez;
- mejora media pero aumenta dispersión;
- no mejora media pero estabiliza;
- empeora ambas dimensiones.

Esta figura es especialmente importante para no reducir el análisis a rankings.

---

### B.3. Heatmap de configuraciones

El paper CLEI2026 usa un heatmap para funciones multimodales y configuraciones. En el journal debe extenderse a un mapa función × configuración.

### Versión recomendada

```text
Rows: benchmark functions or function-dimensional instances
Columns: FCS configurations, e.g., n-R pairs
Cell: log10(normalized gap + epsilon), median rank, or win/loss indicator
```

### Recomendación editorial

El heatmap debe tener una lectura clara. Si las 32 configuraciones vuelven ilegible la figura, usar una versión resumida en el cuerpo principal y dejar la matriz completa en suplemento.

Opciones de reducción:

- mejores configuraciones por regla;
- mejores configuraciones por granularidad;
- top 10 configuraciones globales;
- reglas R1-R8 con la mejor granularidad de cada una.

---

### B.4. Boxplots por función

CLEI2026 muestra distribuciones de fitness por función. En el journal, esto debe usarse de forma selectiva.

### Funciones recomendadas

- F1 o F2: unimodal simple.
- F5: Rosenbrock.
- F9 o F10: multimodal escalable.
- F11: Griewank.
- F21-F23: Shekel.

### Configuraciones recomendadas en los boxplots

- PSO baseline.
- Mejor FCS global.
- Mejor FCS de la función.
- Una configuración FCS mala o contrapuesta.

### En cuerpo principal o suplemento

- Cuerpo principal: 6 a 8 funciones representativas.
- Suplemento: todas las funciones e instancias.

---

## C. Elementos del paper WEA2026 que pueden alimentar el journal

### C.1. Ranking global más ranking por función

El paper WEA2026 tiene una buena estructura: ranking global y desagregación por función. Esta idea es clave para el journal porque evita que el ranking global oculte comportamientos locales.

### Versión recomendada para el journal

Tabla compacta:

```text
Function | 1st configuration | 2nd configuration | 3rd configuration | PSO position | Best fuzzy family | Notes
```

O alternativa:

```text
Configuration | Global rank | Mean rank | Functions won | Top-3 count | Worst-case rank | Best problem class
```

### Objetivo

Mostrar si una configuración:

- gana muchas funciones;
- gana pocas pero domina fuertemente;
- es estable en top-3;
- tiene buen promedio pero malos casos extremos;
- es especialista de una clase de funciones.

---

### C.2. Análisis por grupos de funciones

WEA2026 separa resultados por grupos, por ejemplo funciones con óptimo cero y funciones con óptimo no cero. En el journal conviene ampliar esta lógica a grupos más informativos.

### Clasificación recomendada

```text
Unimodal scalable
Multimodal scalable
Fixed-dimensional multimodal
Shekel / deceptive multimodal
```

Para cada grupo:

```text
Problem class | Best config | Best rule | Best n | PSO rank | Mean rank | Median gap | Effect size | Interpretation
```

### Cuidado editorial

Si los grupos son definidos post hoc, no presentarlos como hipótesis confirmatorias fuertes. Presentarlos como análisis explicativo por clase de paisaje.

---

### C.3. Mirror-pair analysis

WEA2026 contiene una idea metodológica fuerte: comparar pares espejo de reglas para aislar ejes semánticos. Esto debe pasar al journal si las reglas R1-R8 están construidas con una lógica ortogonal equivalente.

### Tabla recomendada

```text
Mirror pair | Semantic axis isolated | Expected behavior | Functions with significant difference | Winner | Effect size | Interpretation
```

Ejemplo conceptual:

```text
R1 vs R2 | Progress direction | decreasing vs increasing inertia | F1, F5, F11 | R1 | large | decreasing inertia supports exploitation
R3 vs R4 | Diversity reaction | following vs compensating diversity | ... | ... | ... | ...
R5 vs R8 | Combined axes | ... | ... | ... | ... | ...
R6 vs R7 | Combined axes | ... | ... | ... | ... | ...
```

### Valor editorial

Este análisis transforma el paper desde un benchmark hacia un estudio explicativo. No solo dice qué regla gana, sino qué componente semántico de la regla parece importar.

---

### C.4. Tabla factorial semántica de reglas

WEA2026 organiza las reglas según ejes semánticos de progreso y diversidad. Esta idea debe mantenerse y ampliarse.

### Tabla recomendada

```text
                    Diversity-following | Diversity-neutral | Diversity-compensating
Progress decreasing        R5                   R1                    R6
Progress neutral           R3                   —                     R4
Progress increasing        R7                   R2                    R8
```

En cada celda puede reportarse:

- mean rank;
- median normalized gap;
- mejor granularidad;
- comportamiento típico de `w(t)`;
- clase de problema donde funciona mejor.

### Objetivo

Que las reglas R1-R8 no aparezcan como etiquetas arbitrarias, sino como configuraciones semánticamente interpretables.

---

### C.5. Trayectorias de inertia weight `w(t)`

WEA2026 usa trayectorias de `w(t)` para explicar mecánicamente por qué algunas reglas convergen y otras se estancan. Esta figura es prioritaria en el journal.

### Versión recomendada

```text
x-axis: iteration
y-axis: mean or median inertia weight w(t)
lines: R1-R8
panels: n = 3, 5, 7, 9
optional panels: problem class
```

### Qué debe explicar

- qué reglas inducen exploración temprana y explotación tardía;
- qué reglas mantienen `w` demasiado alto;
- qué reglas bajan demasiado pronto;
- si la granularidad modifica o suaviza la trayectoria;
- si las mejores reglas generan trayectorias similares al schedule lineal o si producen adaptaciones distintas.

### Importancia editorial

Esta figura conecta directamente:

```text
rule base → control surface → inertia trajectory → convergence behavior → final performance
```

Sin esta conexión, el artículo puede parecer solo una comparación empírica.

---

### C.6. Tabla de efecto de granularidad por regla

WEA2026 compara 3 versus 5 etiquetas por regla. En el journal se debe extender a 3, 5, 7 y 9 etiquetas.

### Tabla recomendada

```text
Rule | Best n | Rank n=3 | Rank n=5 | Rank n=7 | Rank n=9 | Diminishing returns? | Interpretation
```

O bien:

```text
Rule | 3 vs 5 | 5 vs 7 | 7 vs 9 | Overall trend | Best trade-off
```

### Objetivo

Responder si aumentar granularidad:

- mejora una buena regla;
- empeora una mala regla;
- reduce diferencias entre reglas;
- genera sobresegmentación;
- mejora estabilidad pero no fitness;
- aumenta costo sin beneficio práctico.

---

## D. Análisis y figuras prioritarias para el journal

### D.1. Deben ir en el artículo principal

1. **Tabla de diseño experimental**
   - configuraciones;
   - factores;
   - niveles;
   - número de ejecuciones;
   - benchmark y dimensiones.

2. **Tabla PSO vs best FCS por función**
   - función;
   - ganador;
   - mejor configuración;
   - mejora;
   - reducción de dispersión;
   - p-value;
   - effect size;
   - overhead.

3. **Heatmap función × configuración**
   - visualiza patrones locales y globales.

4. **Ranking global + ranking por clase**
   - Friedman/Nemenyi o ranking medio;
   - separaciones por clase de función.

5. **Tabla factorial semántica de reglas**
   - muestra la estructura conceptual de R1-R8.

6. **Mirror-pair analysis**
   - aísla ejes semánticos de reglas.

7. **Efecto de granularidad por regla**
   - compara `n = 3, 5, 7, 9`.

8. **Trayectorias de `w(t)`**
   - conecta reglas con dinámica de búsqueda.

9. **Curvas de convergencia representativas**
   - muestra cómo se alcanza el resultado.

10. **Performance–robustness map**
   - muestra media versus dispersión.

---

### D.2. Deben ir en material suplementario

1. Resultados completos de las 32 configuraciones por función e instancia.
2. Todas las matrices de reglas para `n = 3, 5, 7, 9`.
3. Todas las superficies de control.
4. Todas las curvas de convergencia.
5. Todas las trayectorias de diversidad.
6. Todas las trayectorias de `w(t)`.
7. Todos los tests Wilcoxon/Friedman/Nemenyi/Scheirer-Ray-Hare.
8. Resultados por dimensión para F1-F13.
9. CSV procesados y scripts de reproducción.
10. Archivo con seeds y configuración experimental.

---

## E. Estructura recomendada para la sección de resultados

```text
5. Results

5.1 Global ranking of fuzzy-control configurations
- Friedman/Nemenyi/CD diagram.
- Ranking general de 32 configuraciones + PSO.

5.2 Function-level performance
- Tabla PSO vs best FCS por función.
- Ranking por función.
- Heatmap función × configuración.

5.3 Problem-class dependence
- Ranking por clase.
- Kendall tau entre rankings de clases.
- Pareto plot o matriz de transferencia.

5.4 Effect of rule-base structure
- Tabla factorial semántica.
- Mirror-pair analysis.
- Effect sizes por eje semántico.

5.5 Effect of linguistic granularity
- Comparación n=3,5,7,9 por regla.
- Retornos decrecientes.
- Trade-off desempeño/estabilidad/interpretabilidad.

5.6 Robustness and computational overhead
- Mean vs standard deviation.
- Win/tie/loss.
- Execution time overhead.

5.7 Dynamic behavior of the controller
- Convergence curves.
- Diversity trajectories.
- Inertia-weight trajectories w(t).
```

---

## F. Regla editorial para integrar resultados de los antecedentes sin contaminar la redacción

> **Regla de integración limpia:**  
> Las figuras y tablas sugeridas desde los trabajos previos deben reconstruirse desde los datos actuales del journal. No deben insertarse como reciclaje directo, ni deben describirse como “adaptadas desde” los papers de conferencia, salvo que se decida formalmente citarlas. El agente debe usar los papers en `FUZZY\1.-OLA2026 FUZZY`, `FUZZY\2.-CLEI2026 FUZZY` y `FUZZY\3.-WEA2026` como referencias internas de organización, no como texto fuente para el manuscrito.

### Checklist para el agente

Antes de cerrar la versión del manuscrito, verificar:

```text
[ ] El artículo no menciona que se inspiró en los papers de conferencia.
[ ] Las figuras se generaron con datos actuales del journal.
[ ] Las tablas se generaron con datos actuales del journal.
[ ] Ningún caption dice “adapted from”, “based on previous conference paper”, o equivalente.
[ ] La discusión interpreta los resultados actuales, no los resultados antiguos.
[ ] Las citas a trabajos previos, si existen, cumplen una función bibliográfica real.
[ ] La versión final no conserva lenguaje de protocolo, planificación o reporte de agente.
```

---

## G. Síntesis operativa para el agente

El journal debe integrar lo mejor de los antecedentes, pero como una contribución autónoma:

```text
OLA2026 aporta la narrativa de dependencia del paisaje.
CLEI2026 aporta la lógica de tablas por función, robustez y heatmaps.
WEA2026 aporta la estructura de reglas, pares espejo, análisis factorial semántico y trayectorias de w(t).
```

Sin embargo, el manuscrito final no debe explicitar esa genealogía interna. Debe presentarse como:

```text
A controlled factorial analysis of linguistic granularity and rule-base structure in fuzzy inertia control for PSO.
```

La meta editorial es pasar de:

```text
"Probamos muchas configuraciones."
```

a:

```text
"Aislamos factores semánticos del controlador difuso, medimos su efecto por función y clase de paisaje, y explicamos su impacto mediante reglas, superficies de control y trayectorias de inercia."
```
