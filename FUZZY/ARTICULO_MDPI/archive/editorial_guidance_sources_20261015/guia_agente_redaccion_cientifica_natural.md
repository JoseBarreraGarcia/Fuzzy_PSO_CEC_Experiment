# Catálogo documental de patrones de redacción científica genérica y criterios de calidad textual

**Versión:** 2.0  
**Fecha:** 13 de octubre de 2026  
**Tipo de recurso:** base de conocimiento descriptiva, no prompt ni instrucciones de agente  
**Ámbito:** redacción académica, especialmente artículos científicos escritos en inglés.

## Alcance conceptual

Este documento reúne definiciones, casos y ejemplos de problemas habituales de escritura académica: fórmulas vacías, repetición retórica, vaguedad metodológica, exageración de resultados y homogeneidad de estilo. Algunos coinciden con señales generales descritas por proveedores de detectores de texto generado por IA, pero **ninguno constituye por sí solo evidencia de autoría artificial**.

Es importante distinguir **calidad de redacción**, **procedencia del texto** y **resultados de clasificadores automáticos**. No existe una combinación de palabras o estructuras cuya modificación garantice que un detector clasifique el texto como humano. La finalidad documental es reconocer formulaciones poco informativas y comprender qué hace que una alternativa sea científicamente más precisa, no ocultar una autoría ni sustituir las reglas editoriales de declaración de asistencia automatizada.

## Conceptos y definiciones

- **Predictibilidad léxica (*perplexity*, en ciertos modelos):** medida de sorpresa que produce una secuencia bajo un modelo lingüístico particular. Un valor bajo no demuestra generación por IA; la terminología especializada puede ser muy convencional.
- **Variabilidad de la escritura (*burstiness*, según el uso del proveedor):** diferencias de longitud o patrón sintáctico entre oraciones. No hay un estándar único de medición ni una variabilidad óptima universal.
- **Plantilla retórica:** estructura que se repite independientemente de la función informativa, por ejemplo introducciones ceremoniales y conclusiones genéricas.
- **Vaguedad argumentativa:** afirmación que no permite identificar qué se evaluó, qué se observó o bajo qué condiciones.
- **Voz autoral académica:** conjunto coherente de elecciones terminológicas, sintácticas y argumentativas del investigador, sujeto a convenciones disciplinares y editoriales.
- **Falso positivo:** texto de autoría humana clasificado incorrectamente como generado por IA.
- **Falso negativo:** texto generado por IA clasificado incorrectamente como humano.

## Evidencia y límites de las afirmaciones sobre detección


### Evidencia y documentación

| Patrón o problema | Estatus | Implicación editorial legítima |
|---|---|---|
| Repetición de palabras, conectores y giros sintácticos | Descrito por Grammarly como señal que algunos detectores consideran | Eliminar redundancias cuando no cumplen una función argumentativa. |
| Uniformidad de longitud y construcción de oraciones (*burstiness*) | Descrito por Grammarly; no es prueba de autoría | Variar la sintaxis únicamente cuando la relación lógica o la legibilidad lo justifican. |
| Lenguaje muy predecible (*perplexity* baja) | Señal estadística descrita por Grammarly y estudiada en la literatura | Priorizar especificidad disciplinar, no rareza artificial de vocabulario. |
| Tono genérico, ausencia de detalle y de voz autoral | Descrito por Grammarly | Incorporar decisiones metodológicas, resultados concretos y límites de inferencia fundamentados. |
| Estructuras retóricas formulaicas reiteradas | Observación editorial derivada de patrones de repetición; **no** lista oficial de expresiones detectadas | Revisar si cada oración hace avanzar la argumentación. |
| Uso de palabras supuestamente «prohibidas» | **No existe una lista universal y validada** | Evaluar palabras en contexto; no aplicar listas negras automáticas. |
| Puntuación de «% IA» | Estimación dependiente del sistema, versión, idioma y dominio | No interpretarla como probabilidad forense de que una persona usó IA. |
| Edición profesional de textos humanos | Evidencia reciente indica cambios sustanciales y divergentes en puntuaciones | No confundir buena corrección lingüística con demostración de generación automática. |

**Precaución:** no todos los sistemas calculan directamente *perplexity* o *burstiness*; algunos emplean clasificadores propietarios entrenados sobre ejemplos. No inferir reglas internas exactas a partir de páginas de divulgación.

### Hallazgos relevantes

- Grammarly (2026) menciona repetición, predictibilidad, uniformidad de la estructura y falta de voz personal como rasgos que pueden examinar los detectores.
- Grammarly advierte que una clasificación positiva puede ser errónea y que un texto generado automáticamente puede no ser identificado.
- Liang et al. (2023) documentaron sesgos contra ciertos conjuntos de escritura inglesa de personas no nativas: la tasa media de falsos positivos del conjunto TOEFL examinado fue del 61,3 % en siete detectores. **No extrapolar esta cifra a manuscritos científicos ni a productos actuales.**
- Park et al. (2026, preprint) analizaron 135.389 pares de textos de antes y después de edición profesional y describieron discrepancias importantes entre 13 detectores. **Evidencia preliminar, no revisión por pares confirmada aquí.**
- OpenAI retiró en julio de 2023 un clasificador público por su baja precisión.
- Un estudio sobre el corrector de Grammarly aplicado a textos académicos encontró sugerencias erróneas y limitaciones con vocabulario especializado. **El corrector gramatical y el detector de IA son funciones diferentes.**

## Catálogo de 15 patrones y formulaciones a evitar


Los casos siguientes son fenómenos estilísticos y de argumentación. Su presencia no prueba que el texto haya sido generado por una herramienta.

### P01. Aperturas vagas o ceremoniales

**Manifestación típica:** «In recent years…», «With the rapid advancement of…», «In today's rapidly evolving landscape…», «It is widely recognized that…».

**Problema y alternativa editorial:** reemplazar una generalidad por el problema científico, su contexto y, cuando corresponda, evidencia citada. No eliminar introducciones generales si son necesarias para una audiencia interdisciplinaria.

### P02. Afirmaciones de importancia sin sustento

**Manifestación típica:** «plays a crucial role», «is of paramount importance», «has garnered significant attention», «is highly relevant».

**Problema y alternativa editorial:** explicar importancia mediante una consecuencia, magnitud, dificultad metodológica o vacío investigativo **comprobable**.

### P03. Conectores automáticos o redundantes

**Manifestación típica:** sucesiones de «Furthermore», «Moreover», «Additionally», «In addition», «It is worth noting that», «Importantly».

**Problema y alternativa editorial:** utilizar conectores cuando exista una relación lógica concreta: adición, contraste, causa, restricción o consecuencia. La continuidad temática no requiere siempre un conector explícito.

### P04. Simetría y cadencia excesivamente mecánicas

**Manifestación típica:** varios párrafos consecutivos con igual estructura «afirmación → explicación general → conclusión», o varias oraciones que empiezan igual.

**Problema y alternativa editorial:** estructurar párrafos según su función científica real: objetivo, decisión de diseño, evidencia, interpretación, limitación. **No introducir variación aleatoria.**

### P05. Verbos débiles y sustantivos abstractos

**Manifestación típica:** «provides valuable insights», «offers a comprehensive understanding», «leverages», «facilitates the enhancement», «underscores the importance».

**Problema y alternativa editorial:** usar verbos que describan lo realizado o observado: *estimated, compared, excluded, increased, decreased, remained, failed, was associated with*, según evidencia.

### P06. Promesas de novedad o superioridad no demostradas

**Manifestación típica:** «groundbreaking», «novel and innovative», «unprecedented», «revolutionary», «robust and highly effective», «significantly better» sin prueba estadística o comparación apropiada.

**Problema y alternativa editorial:** definir exactamente la contribución y las condiciones en las que se sostiene. «Significant» debe especificar si significa importancia práctica o significación estadística.

### P07. Conclusiones genéricas

**Manifestación típica:** «The findings contribute to the existing body of knowledge»; «These results pave the way for future research».

**Problema y alternativa editorial:** señalar qué hipótesis, mecanismo, decisión de diseño o interpretación resulta apoyada o cuestionada; indicar límites de generalización.

### P08. Parafraseo redundante

**Manifestación típica:** varias oraciones consecutivas que expresan la misma idea con sinónimos.

**Problema y alternativa editorial:** conservar una formulación precisa y utilizar el espacio para información sustantiva.

### P09. Exceso de adjetivos y adverbios

**Manifestación típica:** «remarkably», «notably», «highly», «substantially», «comprehensive», «seamless», «meticulous» cuando no agregan significado medible.

**Problema y alternativa editorial:** conservar los que tengan una definición operacional o descriptiva útil; retirar intensificadores decorativos.

### P10. Vaguedad metodológica

**Manifestación típica:** «Several models were evaluated using appropriate metrics».

**Problema y alternativa editorial:** exigir definición de modelos, número de corridas, partición temporal, métricas y criterios de comparación si esos datos están disponibles. Nunca inventarlos.

### P11. Interpretación causal impropia

**Manifestación típica:** «X led to Y» para datos observacionales; «proved», «confirmed» o «guaranteed» para evidencia limitada.

**Problema y alternativa editorial:** ajustar al diseño: *was associated with*, *was consistent with*, *suggests*, *under the evaluated setting*, según proceda. Evitar cautela excesiva cuando un diseño experimental permite afirmaciones causales.

### P12. Voz pasiva y activa empleadas mecánicamente

**Manifestación típica:** cadenas de pasivas que ocultan el actor o activas que personalizan procedimientos estandarizados.

**Problema y alternativa editorial:** escoger según función: «We excluded…» cuando la decisión investigadora importa; «Samples were stored…» cuando importa el procedimiento. Seguir las normas de la revista.

### P13. Homogeneización de la voz del autor

**Manifestación típica:** sustitución sistemática de elecciones estilísticas legítimas por formulaciones genéricas típicas de asistentes.

**Problema y alternativa editorial:** respetar terminología recurrente, grado de cautela, preferencias de voz y convenciones de la disciplina, siempre que sean correctas.

### P14. Citas ornamentales o no verificadas

**Manifestación típica:** citas añadidas sin comprobar que respaldan la afirmación, DOI inexistentes, referencias inventadas.

**Problema y alternativa editorial:** mantener marcadores explícitos como `[SOURCE NEEDED]` si falta sustento; jamás generar bibliografía como si estuviera verificada.

### P15. «Humanización» artificial

**Manifestación típica:** errores insertados deliberadamente, coloquialismos impropios, sinónimos raros, cambios azarosos de puntuación o longitud, reescrituras diseñadas solo para bajar un porcentaje.

**Problema y alternativa editorial:** prohibir estas transformaciones. Mantener inglés científico correcto y legible.

## Casos ilustrativos de escritura científica (antes y después)


> Los datos de estos ejemplos son **hipotéticos** y no deben reutilizarse como resultados de una investigación real.

**Ejemplo A: introducción**

Antes:
> In recent years, machine learning has gained significant attention in healthcare, playing a crucial role in improving clinical decision-making.

Después:
> Machine-learning models are increasingly evaluated for emergency-department triage, but their reported performance depends on whether predictors are available at the time the decision is made.

**Justificación:** delimita aplicación y problema metodológico; exige una referencia si se afirma una tendencia empírica.

**Ejemplo B: métodos**

Antes:
> A comprehensive evaluation was performed using various algorithms and several relevant metrics.

Después:
> We compared three classifiers under two predictor sets and evaluated macro-F1, calibration, and recall in the critical class.

**Justificación:** reemplaza abstracciones por decisiones medibles. Usar solo si estos detalles son reales.

**Ejemplo C: resultados**

Antes:
> The proposed approach achieved outstanding results and significantly outperformed existing methods.

Después:
> Under the prespecified test protocol, the model achieved a macro-F1 of 0.72, compared with 0.68 for the baseline. The uncertainty interval for this difference should be reported before claiming statistical superiority.

**Justificación:** cuantifica y separa resultado observado de inferencia estadística.

**Ejemplo D: discusión**

Antes:
> These findings provide valuable insights and highlight the importance of considering multiple factors.

Después:
> The performance gap between predictor sets suggests that variables recorded during triage may carry information unavailable at initial assessment. This interpretation requires an audit of predictor timing and provenance.

**Justificación:** especifica mecanismo plausible y comprobación necesaria; no convierte hipótesis en hecho.

**Ejemplo E: limitación**

Antes:
> Despite its strengths, this study has certain limitations that should be considered in future research.

Después:
> Only 33 critical cases were available in the external test period; consequently, estimates of critical-class recall are imprecise and should be accompanied by an appropriate confidence interval.

**Justificación:** identifica limitación, consecuencia inferencial y medida de transparencia. El valor numérico es ilustrativo.

## Interpretación responsable de resultados de detectores


1. El porcentaje de un detector no debe interpretarse el porcentaje devuelto por un detector como probabilidad calibrada de autoría artificial, salvo validación específica.
2. No existen evidencias suficientes para establecer umbrales universales de «texto seguro».
3. Una palabra aislada no permite afirmar que palabras aisladas provocan una clasificación determinada.
4. Una puntuación de «0 % IA» no es un criterio validado de calidad académica.
5. En casos de clasificación inesperada, son relevantes el proceso editorial y las evidencias de autoría: borradores, notas, versiones, historial y fuentes.
6. Es necesario diferenciar **autoría intelectual**, **asistencia lingüística automatizada** y **generación sustantiva de contenido** según las normas del editor.

## Fuentes documentales y estudios


### Documentación de plataformas

1. Grammarly. (2026, 27 de abril). *How to Avoid AI Detection (the Right Way): Top Writing Strategies*. https://www.grammarly.com/blog/ai/how-to-avoid-ai-detection/
2. Grammarly. (2026). *How Do AI Detectors Work? Key Methods and Limitations*. https://www.grammarly.com/blog/ai/how-do-ai-detectors-work/
3. Grammarly. (2026). *Are AI Detectors Accurate? What You Should Know*. https://www.grammarly.com/blog/ai/ai-detectors-accuracy/
4. OpenAI. (2023). *Nuevo clasificador de IA para detectar textos generados por IA* (actualización de retirada, 20 de julio de 2023). https://openai.com/es-ES/index/new-ai-classifier-for-indicating-ai-written-text/

### Estudios y análisis académicos

5. Liang, W., et al. (2023). GPT detectors are biased against non-native English writers. *Patterns, 4*(7), 100779. https://doi.org/10.1016/j.patter.2023.100779
6. *Exploring the use of Grammarly in assessing English academic writing*. (2024). *Heliyon, 10*(15), e34893. https://doi.org/10.1016/j.heliyon.2024.e34893
7. Park, H., Jeong, G., & Kim, B. (2026). *Style as a Confound: False Positives in AI Detection of Non-Native Academic Writing*. arXiv preprint, arXiv:2608.26710. https://arxiv.org/abs/2608.26710
8. Angelier, V. (2026). *The pitfalls of AI detection in academic writing: bias, false positives, and the need for inclusive assessment*. *AI and Ethics*. https://link.springer.com/article/10.1007/s43681-026-01376-w

**Nota bibliográfica:** las referencias 1–4 describen herramientas o sus propias afirmaciones comerciales; no validan de forma independiente su precisión. Las referencias 5–8 aportan evidencia y análisis con alcances y limitaciones distintos. La versión de arXiv es un preprint.


**Advertencia:** los ejemplos «después» son alternativas de redacción científica, no técnicas verificadas para modificar una puntuación de detección. Los resultados hipotéticos solo ilustran estructura textual y nunca deben presentarse como evidencia real.
