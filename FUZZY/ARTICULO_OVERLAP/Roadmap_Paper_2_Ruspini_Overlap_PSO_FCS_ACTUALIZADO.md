# Roadmap de investigación y protocolo experimental: segundo artículo PSO-FCS

**Título provisional (inglés):** *Beyond Ruspini Partitions: Membership-Function Overlap, Rule Activation, and Computational Trade-offs in Mamdani Fuzzy-Controlled Particle Swarm Optimization*

**Estado:** roadmap actualizado el 19 de octubre de 2026; plan de trabajo, no protocolo ejecutado. **Decisión vigente:** CEC 2017 como candidato principal condicionado a auditoría y F1–F23 como bloque secundario. **Documento asociado:** `Diagnostico_CEC2017_PreExperimentos_Paper2.md`. **Journal objetivo:** por confirmar; evaluación editorial provisional. **Tipo:** artículo original de investigación metodológica y experimental en optimización computacional.

## 1. Posicionamiento y contribución

**Artículo previo:** análisis de sensibilidad estructural de 32 controladores de inercia Mamdani para PSO, definidos por cuatro granularidades (3, 5, 7, 9) y ocho bases de reglas (R1–R8), con particiones triangulares Ruspini, 62 instancias F1–F23 y 31 corridas.

**Nuevo problema:** la condición de Ruspini y la extensión de las funciones de pertenencia estaban fijadas en el artículo previo. No conocemos, bajo un diseño controlado, cómo cambia la inferencia, la dinámica de PSO, la calidad de búsqueda o el costo de cálculo al reducir el solapamiento entre funciones.

**Contribución buscada:** una caracterización matemática, algorítmica y empírica del compromiso entre continuidad/cobertura de la inferencia, cantidad de reglas activadas, costo de inferencia y resultados de optimización cuando se relaja la partición Ruspini. **No afirmar** que relajar Ruspini es novedoso por sí mismo, ni que menos reglas activas equivale automáticamente a menos tiempo, ni que un resultado no significativo demuestra equivalencia.

**Diferenciación respecto del primer artículo:** nueva variable estructural preespecificada (overlap), nuevo protocolo de aleatoriedad emparejada, experimentos íntegramente rerun, instrumentación del costo de inferencia, caracterización formal de cobertura/continuidad y validación externa. Las observaciones del primer artículo se citan como antecedentes, no se duplican como resultados nuevos.

## 2. Preguntas de investigación

- **RQ1, estructura:** ¿Cómo modifica el solapamiento nominal de 0 %, 50 % y 100 % la cobertura, la suma de pertenencias, la activación de reglas, la continuidad y las superficies de salida Mamdani?
- **RQ2, desempeño:** ¿Cómo varían fitness final, convergencia y robustez de PSO al modificar overlap, condicionado a granularidad y patrón de reglas?
- **RQ3, costo:** ¿La reducción de reglas activas produce ahorro de tiempo de inferencia y tiempo total? ¿Depende de implementar evaluación densa o dispersa?
- **RQ4, interacciones y transferencia:** ¿Existen interacciones descriptivas o inferenciales entre overlap, granularidad y regla, y se mantienen las tendencias entre CEC 2017 y F1–F23?

**Claims permitidos solo si se verifican:** reducción de activaciones; reducción de tiempo medida; ventajas puntuales de desempeño; compromisos entre efectividad y costo. No atribuir independencia causal o beneficios generalizables sin controles suficientes.

## 3. Definición operacional de overlap

Centros equiespaciados `c_i`, distancia entre centros `Delta = c_(i+1)-c_i`. Para etiquetas triangulares interiores, definir semianchura de soporte:

`h(o) = Delta * (1 + o) / 2`, con `o ∈ {0, 0.5, 1}`.

`mu_i(x;o) = max(0, 1 - abs(x-c_i)/h(o))`, con tratamiento de hombros y límites explícito.

| Overlap nominal | `h/Delta` | Geometría entre vecinos |
|---|---:|---|
| 0 % | 0.50 | Soportes que solo se tocan en el punto medio; no hay intervalo de intersección positiva |
| 50 % | 0.75 | Soportes superpuestos en una región de anchura positiva |
| 100 % | 1.00 | Cada soporte alcanza el centro vecino; construcción triangular Ruspini habitual bajo hombros compatibles |

**Nota crítica:** los porcentajes son niveles geométricos definidos respecto de distancia entre centros; no son porcentaje de área compartida, porcentaje de reglas activas, altura de intersección ni suma de membresías. Precisar si el diseño usa la misma extensión `o` para las particiones de **diversidad, progreso y salida de inercia**. Recomendación para estudio principal: variar conjuntamente las tres con un único `o` para controlar alcance; en discusión, reconocer que así no se identifica por separado el efecto de antecedente frente a consecuente. Una ablación secundaria 2×2 (solapamiento antecedente/salida) puede aislar mecanismos si el costo lo permite.

### Fronteras con overlap 0 %

En el punto medio entre dos centros, las dos triangulares adyacentes pueden alcanzar pertenencia 0: ninguna regla se activa y el denominador del centroide puede anularse. **Definir antes de ejecutar** una política que garantice cobertura operacional. Opción primaria: convención determinista de etiqueta superior en el punto medio (`tie → upper label`) con activación puntual de pertenencia 1 o asignación categórica al antecedente seleccionado, definida expresamente como extensión del operador de fuzzificación. Opción de sensibilidad: `tie → lower label`; una tercera opción es comparar con una función tipo *nearest centre*. Documentar que estas convenciones introducen discontinuidades y **no equivalen** a una partición triangular continua ni recuperan la condición Ruspini. Validar los extremos `x=0,1`, hombros, clipping y casos de flotantes próximos al límite.

**Alternativa más conservadora:** definir una tolerancia operacional o límites semiabiertos para evitar activación nula y garantizar una sola regla; explicar que sigue siendo una fuzzificación con política de frontera. Nunca tratar como resultado natural de las ecuaciones triangulares algo que depende de la política de implementación.

### Propiedades formales y pruebas

1. **Normalidad** (cada conjunto alcanza 1), convexidad fuzzy, orden de centros, simetría de la familia y cobertura positiva del dominio tras la política de frontera.
2. **Suma de membresías** `S(x)=sum_i mu_i(x)` en una malla fina, y cotas analíticas cuando sea posible; cuantificar desviación respecto de Ruspini.
3. **Número activo** `K(x)=count_i(mu_i(x)>0)`; reglas activas por par de entradas `K_D(d)*K_P(p)`.
4. **Continuidad** de las funciones y de la superficie efectiva `w(d,p)`; detectar y cuantificar saltos en fronteras para `o=0`.
5. **Proposición de simetría:** analizar si las hipótesis de reflexión de las salidas preservan complementariedad de superficies aunque Ruspini se relaje; la simetría puede depender de hombros, normalización del centroide, integración y política de frontera. **No reutilizar sin prueba** la proposición del artículo anterior.
6. **Casos degenerados:** denominador de defuzzificación cercano a cero, saturación de salida y exactitud numérica entre inferencia densa y dispersa.

## 4. Delimitación del segundo artículo: triangulares primero

**Diseño principal:** solo funciones triangulares, sin gaussianas ni cambios simultáneos de métricas de estado. Mantener los dos antecedentes originales (diversidad normalizada y progreso de iteración), la salida `w`, min–max Mamdani, centroide, límites de `w`, y el mismo algoritmo base. Esta decisión aísla mejor la nueva dimensión experimental.

**Extensión futura o suplementaria opcional:** familia gaussiana con equivalencia de brazo por `2 sigma = h(o)` ⇒ `sigma(o)=Delta*(1+o)/4`. El valor a 2 sigma es `exp(-2)≈0.1353`, **no cero**. Gaussianas ordinarias tienen soporte infinito, de modo que overlap 0 % solo es nominal/efectivo; la truncación en ±2 sigma es una modificación adicional que debe analizarse por separado. No incluirlas en el factorial principal salvo rediseño explícito de las hipótesis.

## 5. Diseño factorial de optimización

| Factor | Niveles | Número |
|---|---|---:|
| Solapamiento geométrico `o` | 0; 0.5; 1.0 | 3 |
| Granularidad `n` | 3; 5; 7; 9 | 4 |
| Patrón consecuente `R` | R1–R8 | 8 |
| **PSO-FCS** | **3 × 4 × 8** | **96** |
| Baseline común | PSO con inercia decreciente lineal | 1 |

### 5.1 Benchmark principal: CEC 2017, condicionado a validación

**Decisión de diseño propuesta:** 29 funciones de CEC 2017, excluida F2 sin renumerar las demás; dimensiones inicialmente `D={30,50}`; **31 réplicas** con semillas maestras 42–72. La implementación local (`Problem/Benchmark/CEC/cec2017/`) **no está aún aprobada**: el diagnóstico asociado recoge un fallo de no finitud reportado en F21–F30 en vectores coincidentes con centros de composición, así como anomalías que requieren aclaración en F9 y otras funciones. Es obligatorio reproducir, corregir y validar frente a referencia antes de la campaña. No interpretar las pruebas de humo como certificación de equivalencia.

- Instancias CEC: `29 × 2 = 58` combinaciones función–dimensión.
- Tratamientos: `96 FCS + 1 PSO = 97`.
- Corridas FCS: `96 × 58 × 31 = 172.608`.
- Corridas PSO: `1 × 58 × 31 = 1.798`.
- **Total CEC principal previsto: 174.406 corridas** (condicionado a aprobación de las 58 instancias).
- **Todas las corridas son nuevas**, incluido overlap 100 % y PSO; los resultados del primer artículo no se reciclan como observaciones emparejadas.

**Presupuesto de evaluaciones: DECISIÓN ABIERTA.** Comparar dos opciones antes de aprobar la campaña: (A) protocolo de referencia de CEC 2017, con presupuesto ligado a dimensión, normalmente `10.000 × D` evaluaciones (D30: 300.000; D50: 500.000); (B) presupuesto propio explícito y uniforme por tratamiento/dimensión, justificado por factibilidad. Las 31 réplicas no reproducen por sí mismas todas las condiciones de competición CEC. En el escenario A el total nominal sería `87.203 × 300.000 + 87.203 × 500.000 = 69.762.400.000` evaluaciones, **sin autorizar todavía ese costo**. Definir contador exacto de `nfev`, inicialización, parada y costo en un piloto antes de congelar parámetros. No reutilizar automáticamente el presupuesto anterior de 20.020 evaluaciones.

**Criterio de factibilidad:** estimar CPU-horas, tiempo total, almacenamiento y costo de cada tipo de función, particularmente híbridas y composiciones. Si el protocolo completo excede recursos, justificar de antemano un presupuesto menor o un diseño escalonado, sin describirlo como protocolo oficial CEC.

### 5.2 Benchmark secundario: F1–F23

Conservar F1–F23 (13 escalables con cuatro dimensiones + 10 de dimensión fija = **62 instancias**) para continuidad histórica y comprobación cruzada. **No incluir automáticamente las 62 instancias × 97 tratamientos**; elegir antes de revisar resultados CEC entre:

- **Opción secundaria completa:** 62 × 97 × 31 = **186.434 corridas nuevas**; presupuesto nominal previo de 20.020 evaluaciones por corrida solo si se mantiene explícitamente.
- **Opción secundaria acotada (preferible por factibilidad):** subconjunto predefinido de funciones/dimensiones y tratamientos, estratificado por clase y representatividad estructural; calcular tamaño una vez congelado el manifiesto. No escoger configuraciones ganadoras utilizando resultados CEC de prueba, salvo que se declare un análisis de selección/exploratorio separado.

El uso de F1–F23 como bloque secundario no convierte sus 62 instancias en 62 funciones independientes. F7 incluye ruido objetivo y exige gestionar su fuente aleatoria con especial cuidado. CEC 2017 utiliza funciones objetivo deterministas con datos de transformación fijos; no introducir aleatoriedad artificial en sus evaluaciones.

### 5.3 Comparadores externos

El mínimo del factorial es PSO de inercia decreciente lineal. Para mejorar la interpretación frente a revisores de optimización, identificar y justificar al menos uno o dos PSO adaptativos publicados, con presupuesto idéntico. Si su inclusión hace inviable ejecutar todas las combinaciones, compararlos con un subconjunto de FCS seleccionado mediante una regla **predefinida y independiente del bloque final de prueba**; no presentarlos como controles factoriales de los 96 FCS.

### 5.4 Invariantes de comparación

Congelar límites CEC `[-100,100]^D`, valores bias/óptimos, transformaciones, tamaño poblacional, coeficientes PSO, manejo de límites de posición y velocidad, precisión numérica, tratamiento de errores, contador `nfev` y entorno de ejecución. No mezclar bibliotecas de benchmark o versiones de transformaciones dentro del mismo bloque comparativo.

## 6. Arquitectura de aleatoriedad: requisito crítico de la nueva campaña

**Objetivo:** resultados replicables por (función, dimensión, réplica, tratamiento) y corridas comparables mediante los mismos elementos exógenos donde sea metodológicamente válido. Las semillas compartidas **no hacen idénticas** las trayectorias de los métodos, pero pueden reducir ruido y habilitar análisis pareados.

### 6.1 Índices y claves

Definir:

- `instance_id`: función y dimensión, por ejemplo `F9_D30`.
- `replicate_id ∈ {1,...,31}`; `master_seed=41+replicate_id` (42–72).
- `config_id`: `PSO` o `FCS-o{0,50,100}-n{3,5,7,9}-R{1,...,8}`.
- `experiment_version`, `git_commit`, `env_hash`, `seed_protocol_version`.

### 6.2 Plan de generadores

**Contrato de semillas maestras:** para réplica `r ∈ {1,...,31}`, `master_seed(r)=41+r`. Por tanto, cada instancia y tratamiento utiliza exactamente el conjunto **42, 43, ..., 72**. La misma réplica comparte la misma semilla maestra en todas las configuraciones, incluido PSO. El identificador `config_id` **no** interviene en los flujos comunes.

Derivar subflujos independientes y estables por propósito mediante `numpy.random.SeedSequence` u otro esquema especificado y versionado. Para que las pruebas sean independientes entre instancias sin perder CRN entre tratamientos, se puede incluir un identificador numérico estable de `instance_id` en las claves de los **subflujos**, conservando `master_seed=42,...,72` como semilla maestra visible por réplica. Documentar y almacenar tanto la semilla maestra como los identificadores de subflujos. **Nunca** usar `hash()` aleatorio de Python para identificar instancias entre procesos.

Derivar flujos independientes por propósito:

- `rng_init`: posiciones iniciales y cualquier inicialización estocástica común.
- `rng_pso_cognitive`: coeficientes aleatorios cognitivos `r1`.
- `rng_pso_social`: coeficientes aleatorios sociales `r2`.
- `rng_objective`: ruido exógeno de la función objetivo, especialmente F7 (si corresponde, controlar índice de evaluación o utilizar un plan explícito de ruido común).
- `rng_selector`: reservado para futuro selector dinámico; el controlador estático del segundo paper no requiere consumo aleatorio.

**Recomendación fuerte:** generar los coeficientes `r1` y `r2` según `(t, partícula, coordenada)` o precalcular flujos con consumo fijo, para evitar que distintas ramas de código desalineen secuencias. Iniciar todos los tratamientos de una misma `(instancia, réplica)` desde exactamente las mismas posiciones; mantener dimensión, límites y reglas de clipping idénticos. Registrar las semillas efectivas y un checksum de condiciones iniciales. Los métodos pueden divergir después por sus decisiones, lo cual es esperable.

### 6.3 Definir emparejamiento real y pruebas

- La unidad emparejada por ejecución es **(instancia, réplica)**, porque todos los tratamientos comparten condiciones iniciales y aleatoriedad exógena planificada.
- Validar comparabilidad con tests automáticos: posiciones iniciales iguales, `r1/r2` iguales en el mismo índice, semillas reproducibles y ausencia de contaminación por orden de ejecución.
- Los **tests pareados** de diferencias por réplica solo son apropiados cuando los pares están correctamente instrumentados y los supuestos o el procedimiento de permutación corresponden al contraste. Evitar reutilizar Mann–Whitney de la campaña antigua por inercia.
- Para inferencia global, tratar la dependencia entre dimensiones de una misma función. No interpretar 31 réplicas × múltiples dimensiones como problemas independientes.

### 6.4 Auditoría mínima de semilla

1. Misma clave ⇒ mismos iniciales, mismos arreglos de ruido exógeno y mismo resultado bit a bit en entorno controlado, o tolerancia documentada si hay paralelismo numérico.
2. Cambiar `config_id` ⇒ **no cambiar** la semilla del bloque común `(instancia, réplica)`.
3. Cambiar `replicate_id` ⇒ cambiar el bloque de ruido e inicialización.
4. Ejecutar en distinto orden o distinto trabajador ⇒ mismas entradas estocásticas.
5. Reanudar corrida incompleta ⇒ no duplicar ni alterar resultados.
6. Si se modifica la implementación después del piloto, fijar nueva versión de protocolo y no mezclar versiones incompatibles.

## 7. Inferencia densa vs dispersa: separación obligatoria

Medir dos realizaciones del **mismo** controlador, sin cambiar sus decisiones:

- `dense`: evalúa la tabla completa de `n²` reglas o la implementación original equivalente.
- `sparse`: detecta etiquetas activas y evalúa únicamente pares antecedentes activados, con reglas de frontera idénticas.

**Control esencial:** para cada `(o,n,R,d,p)` comparar `w_dense` y `w_sparse` con tolerancia numérica fijada. **No duplicar** toda la campaña principal CEC 2017 (174.406 corridas previstas) solo por método de inferencia si se ha demostrado equivalencia de salida y la diferencia únicamente afecta ejecución: realizar un microbenchmark separado y representativo de los estados visitados, con suficientes repeticiones de temporización, orden aleatorizado y control del entorno. Si no hay equivalencia, tratarla como factor algorítmico adicional, no como mera optimización de código.

Tiempo de inferencia y tiempo total deben medirse por separado; además contar etiquetas y reglas activas, evaluadas y saltadas. La reducción teórica de activaciones no implica automáticamente ventaja de tiempo si domina la defuzzificación sobre una malla de 501 puntos u otros costos de Python/vectorización.

## 8. Piloto y criterios de avance

**Piloto sugerido (NO evidencia confirmatoria; ejecutar solo tras la auditoría CEC):** `o={0,0.5,1}` × `n={3,9}` × `R={R1,R5,R6}` = **18 controladores**; 6 funciones CEC variadas y validadas × 2 dimensiones × 10 réplicas = **2.160 corridas FCS**, más 120 PSO, total **2.280 corridas**. Estas cifras son configurables según tiempo real.

**Objetivo del piloto:** comprobar cobertura, tasa de fallbacks, independencia de semillas, reproducibilidad, equivalencia dense/sparse, costo por inferencia, trayectorias discontinuas y viabilidad de cómputo. No elegir los niveles que resultaron ganadores y presentarlos después como un diseño confirmatorio sin declarar la selección.

**Go/no-go antes del principal:**
- La auditoría de CEC 2017 aprobó las funciones/dimensiones principales, incluidos tests específicos para composiciones F21–F30, F9 y datos shift/rotation/shuffle, según diagnóstico asociado.
- Todas las configuraciones cumplen rango de salida `w ∈ [0.1,0.9]`, sin NaN/Inf.
- Política de frontera de `o=0` definida, probada y congelada.
- Los tratamientos comparten exactamente la inicialización por bloque.
- Los generadores son deterministas bajo distinto orden de ejecución.
- `nfev` coincide con presupuesto para todos los métodos.
- El log registra `active_labels`, `active_rules`, `w`, `diversity`, `iteration`, `fitness_best`.
- Tiempo de evaluación de función objetivo, tiempo de inferencia y tiempo total se registran por separado; relación entre tiempos reportada sin asumir causalidad general.
- Se estima y aprueba costo en CPU/hora/disco; se documenta versión del entorno.

## 9. Resultados y análisis predefinido

### 9.1 Resultados primarios

1. **Calidad final**: brecha normalizada o fitness final por instancia y configuración, resumido sobre 31 réplicas.
2. **Costo de inferencia**: tiempo por llamada bajo dense/sparse; número de reglas activas y porcentaje de llamadas con fallo de cobertura, si aplica.
3. **Tiempo total**: wall-clock por ejecución y sobrecarga relativa al PSO baseline, en entorno comparable.

### 9.2 Secundarios

- Convergencia del `best-so-far`, variabilidad y tasa de éxito con umbrales predefinidos.
- Trayectorias `w_t`, diversidad y estancamiento; saltos en `w` cerca de fronteras.
- Sensibilidad a la convención de empate de `o=0` como análisis secundario.
- Caracterización `S(x)=sum mu` y superficies `w(d,p)` por `o,n,R`.
- Robustez ante dimensión, modalidad, costos y restricciones del benchmark.

### 9.3 Estrategia inferencial

**Contrastes primarios planeados (no todos contra todos):** dentro de cada pareja `(n,R)` comparar `o=0` vs `o=1`, `o=0.5` vs `o=1`; opcional `o=0` vs `o=0.5`. Preespecificar familia de comparaciones, ajuste Holm y tamaño de efecto pareado. Usar réplicas compartidas como pares dentro de cada instancia; resumir diferencias por función–dimensión y evaluar consistencia por función y familia. Para evaluación factorial confirmatoria, considerar un modelo jerárquico con interacciones `overlap × n`, `overlap × R` y dependencia por función/instancia; **definir estimando y escala antes de usarlo**, y comprobar si datos y recursos permiten el modelo. No inferir efectos independientes de `n` si cambia simultáneamente cardinalidad de reglas; separar resultados descriptivos de conclusiones causales.

**Análisis por benchmark:** Friedman/Nemenyi solo si responde a una pregunta comparativa claramente justificada y se respetan bloques; un ranking global de 97 algoritmos puede ser estadísticamente poco informativo. No basar claims principales en el “ganador por instancia” elegido retrospectivamente (oracle). No confundir `p>0.05` con equivalencia; si la hipótesis es no deterioro del fitness, establecer **margen de no inferioridad** científicamente interpretable y diseñar su prueba/IC antes de ejecutar.

**Tiempo:** comparar inferencia en condiciones controladas, registrar calentamiento, carga, CPU, paralelismo, GC, instrumentación, distribución de latencias y variabilidad; mediana e IQR y estimación de incertidumbre. Evitar benchmarks de microsegundos sin aislamiento de ruido.

## 10. Validación cruzada, alcance y prevención de *salami slicing*

**CEC 2017 es el candidato principal**, no la validación secundaria. **F1–F23 constituye el bloque de continuidad**, ejecutado nuevamente con el protocolo CRN actualizado, completo o con subconjunto preespecificado según recursos. La consistencia de resultados entre ambas suites constituye evidencia de robustez, pero **no debe interpretarse como generalización universal**. Una tercera suite (por ejemplo CEC 2020) o problemas continuos de ingeniería sería una extensión opcional y con presupuesto independiente; no incorporar por mera novedad cronológica.

El primer paper evaluó `(n,R)` con overlap triangular 100 % en F1–F23. El segundo examina explícitamente propiedades de partición, solapamiento, cobertura, continuidad, inferencia eficiente y efectos condicionados `overlap × n × R`, con **nuevo protocolo de semillas y benchmark principal más exigente**. Citar el artículo anterior y transparentar elementos compartidos. Si el incremento experimental solo reproduce rankings sin explicar estos mecanismos, la contribución puede resultar incremental pese al uso de CEC.

## 11. Reproducibilidad, estructura de repositorio y paquetes entregables

Estructura orientativa:

```text
project/
  config/
    study_preregistered.yaml
    benchmark_manifest.csv
    cec2017_validation_manifest.csv
    configs_97.csv
    seed_protocol.yaml
  src/
    pso_core.py
    fuzzy_membership.py
    rule_bank.py
    fuzzy_inference_dense.py
    fuzzy_inference_sparse.py
    rng_streams.py
    benchmarks.py
  tests/
    test_overlap_geometry.py
    test_boundaries.py
    test_rule_activity.py
    test_symmetry.py
    test_dense_sparse_equivalence.py
    test_rng_pairing.py
    test_cec_composition_centres.py
    test_cec_reference_equivalence.py
    test_cec_dispatch_nfev.py
    test_reproducibility.py
  scripts/
    run_pilot.py
    run_main.py
    analyze_main.py
    benchmark_inference.py
    generate_figures.py
  results/
    pilot/
    main/
    external/
  supplementary/
    README.md
    data_dictionary.md
    statistical_results.csv
    checksums.sha256
```

**Registro por corrida:** agregar obligatoriamente `benchmark_suite`, `benchmark_impl_commit`, `benchmark_data_sha256`, `function_official_id`, `function_bias`, `benchmark_validation_version`, `master_seed` (42–72), y separar `runtime_objective_s`, `runtime_fis_s`, `runtime_solver_s`.

**Registro por corrida:** `experiment_id`, `commit`, `instance`, `dimension`, `replicate_id`, `master_seed`, `config_id`, `o`, `n`, `R`, `seed_block_id`, `seed_init`, `seed_r1`, `seed_r2`, `seed_objective`, `fitness_best`, `normalized_gap`, `nfev`, `runtime_total_s`, `runtime_fis_s`, `num_fis_calls`, `fallback_count`, `active_rules_mean`, `active_rules_max`, `status`.

**Registro de trayectoria:** conservar serie temporal de `iteration`, `w`, `diversity`, `fitness_best`, `active_labels_D`, `active_labels_P`, `active_rules`, `stagnation`, `velocity_norm` (si se mide). Dimensionar almacenamiento: 174.406×1000 iteraciones equivaldrían a ~174 millones de filas en el bloque CEC (si se registran 1000 iteraciones por corrida); el número real dependerá del presupuesto y del tamaño de población; proponer parquet comprimido/series agregadas más trazas detalladas por muestra predefinida, sin perder la capacidad de reproducir gráficos declarados.

**Datos complementarios:** tablas procesables de 97 configuraciones, comparaciones corregidas, superficies (mallas), pruebas de cobertura, pruebas de simetría, microbenchmark dense/sparse, resultados externos, manifest y controles de integridad. Especificar entorno, bibliotecas, SO, CPU, opciones de paralelismo, protocolo de seeds, duración y presupuesto.

## 12. Secuencia de trabajo y puertas de calidad

| Hito | Actividad | Evidencia para cerrar |
|---|---|---|
| H0 | Congelar preguntas, factores, diseños CEC y F1–F23, política de fronteras y protocolo estadístico | Prerregistro y manifiesto fechado |
| H1 | **Auditoría CEC 2017**: congelar código/datos, reproducir/solucionar NaN F21–F30, revisar F9, cotejar referencia y validar despacho | Tests numéricos y equivalencia aprobados, hashes; **GO/NO-GO** |
| H2 | Implementar `o=0,0.5,1` y tests geométricos/formales | Cobertura, normalidad, simetría, casos límite |
| H3 | Refactorizar RNG para semillas maestras 42–72, CRN y flujos separados | Tests de pairing, replay y ejecución desordenada |
| H4 | Construir inferencia densa y dispersa | Igualdad numérica validada; microbenchmark |
| H5 | Seleccionar presupuesto `nfev` CEC y ejecutar piloto con funciones aprobadas | Informe de QA, tiempos CPU y costo autorizado |
| H6 | Congelar benchmark, código, presupuestos, seeds y análisis; ejecutar CEC principal | **174.406 resultados esperados** si se aprueba D30+D50, sin faltantes/duplicados |
| H7 | Ejecutar F1–F23 secundario según manifiesto predefinido | Resultados nuevos con CRN y trazabilidad |
| H8 | Auditoría estadística, robustez, figuras y suplementarios | Scripts reproducibles, checksums y tablas reconciliadas |
| H9 | Redactar artículo y paquete de reproducibilidad | Manuscrito y software/datos consistentes |

No asignar plazos en semanas sin conocer recursos de cómputo. Estimar tiempo de pared con benchmarks representativos incluyendo inferencia por cada `n,o,R` y costo de archivos.

## 13. Riesgos y mitigaciones

- **Colapso de inferencia en o=0:** resolver antes mediante convención de frontera explícita; registrar fallback y probar sus discontinuidades.
- **No Ruspini ≠ no cobertura:** evaluar `S(x)` y `max_i mu_i(x)` por separado; sin cobertura no siempre existe salida definida.
- **Semillas mal pareadas:** pruebas de inicialización, coeficientes por índice y ejecución fuera de orden; rerun completo indispensable.
- **Costos artificiales:** si el código recorre todas las reglas, el ahorro teórico no se materializa; separar dense/sparse.
- **Comparabilidad de gaussianas:** no incorporarlas al principal sin convención de 2σ/truncamiento y nueva justificación.
- **Múltiples pruebas y cherry picking:** preregistrar endpoints y familias, evitar seleccionar el mejor método desde el test.
- **Dependencia de funciones:** no usar 62 instancias como 62 familias de problema independientes.
- **Aporte marginal por benchmark repetido:** incorporar validación externa y evidencia de mecanismo, además del fitness.
- **Costo total:** CEC 2017 D30/D50 con 10.000×D por corrida implicaría ~69.762 millones de evaluaciones; **cifra orientativa no aprobada**. El cálculo antiguo de ~3.73 mil millones corresponde exclusivamente al bloque completo F1–F23 con presupuesto de 20.020; estimar antes de lanzar.

## 14. Bosquejo del manuscrito en inglés académico

1. Introduction: motivación, diferencia respecto del estudio de granularidad y reglas, contribuciones verificables.
2. Related Work: particiones Ruspini y relajadas, geometría de membresía, métodos de inferencia eficiente, control difuso en PSO.
3. Formalization: overlap nominal, familias triangulares, tratamiento de fronteras, propiedades, complejidad y superficies.
4. Experimental Methods: factorial, CEC 2017 validada, F1–F23 de continuidad, presupuesto `nfev`, unidad experimental, implementación RNG compartida, métricas, baselines, inferencia dense/sparse, hipótesis/contrastes predefinidos.
5. Results: caracterización de partición y superficie; activación/costo; desempeño y robustez; efectos condicionados e interacciones; validación externa.
6. Discussion: compromisos y mecanismos plausibles; qué se puede y no se puede inferir; comparación con artículo anterior.
7. Limitations: una familia de membresía, un controlador Mamdani, una implementación PSO, benchmark clásico más validación acotada; discontinuidades del 0 %, ausencia de equivalencia inferencial cuando no se pruebe.
8. Conclusions and Future Work: gaussianas con 2σ y selección dinámica estructural como extensiones independientes.

## 15. Decisiones que deben cerrarse antes de programar

1. Confirmar si `o` afecta simultáneamente **entrada diversidad, entrada progreso y salida** (recomendación inicial: sí, reportando que son un tratamiento conjunto).
2. Precisar la definición exacta de hombros triangulares en `[0,1]` y las funciones de salida para centroide.
3. Elegir política primaria de frontera en `o=0`: superior, inferior o vecino más cercano; especificar si se asigna membresía 1 en el punto.
4. Determinar si se conserva exactamente la integración del centroide a 501 puntos o se mejora implementación de forma idéntica para todos los tratamientos y se vuelve a ejecutar todo; registrar cambios.
5. Fijar CEC 2017 principal (funciones/dimensiones aprobadas), F1–F23 secundario (completo o acotado), presupuesto `nfev`, baseline PSO, 31 réplicas y semillas maestras 42–72; declarar la derivación y consumo de flujos RNG.
6. Completar auditoría CEC 2017 y del despacho PSO; fijar manifiesto secundario F1–F23 antes de observar resultados principales.
7. Definir estimando principal de fitness y de eficiencia, familia de contrastes y corrección estadística.
8. Estimar CPU/hora y almacenamiento, y fijar criterio de detención ante fallos técnicos.

**Recomendación de cierre:** el segundo paper es viable como propuesta metodológica, pero su aceptación Q1 dependerá de que la relajación de Ruspini se estudie como fenómeno matemático y computacional con inferencia válida, no solo como otro factor que produce un ranking. La prioridad operativa inmediata es corregir y validar las semillas por réplica, congelar la política de overlap 0 % y después repetir absolutamente toda la campaña bajo el nuevo protocolo.

## 16. Estado de decisiones y bloqueos (actualización 2026-10-19)

| Elemento | Estado | Condición para cerrar |
|---|---|---|
| Hipótesis del paper: relajación de Ruspini mediante overlap | Definida provisionalmente | Formalización final de hombros y fronteras |
| Factorial 3 overlaps × 4 granularidades × 8 reglas | **Fijado: 96 FCS** | Tests geométricos y de inferencia |
| Familia de membresía principal | Triangular | Gaussianas `2σ` se reservan para extensión |
| Semillas | **Acordadas: 42–72**, 31 réplicas, CRN | Implementación y tests reproducibles |
| Repetición completa de campañas | **Obligatoria** | No reutilizar corridas anteriores como pares |
| Suite principal | **CEC 2017, candidato**, 29 funciones D30+D50 | Auditoría y validación numérica **pendientes** |
| Estado funciones CEC | Hallazgos previos reportan NaN F21–F30, anomalías F9 | Reproducción, corrección, equivalencia externa y E2E |
| Presupuesto principal | **Sin cerrar** | Piloto de factibilidad y decisión entre protocolo CEC o presupuesto propio |
| Suite secundaria | F1–F23 | Elegir manifiesto completo o reducido antes del análisis |
| Baselines adaptativos adicionales | Por evaluar | Justificar selección e igualdad de presupuesto |
| Journal objetivo | No definido | Evaluación de journal fit provisional |

**Dependencia documental:** leer conjuntamente `Diagnostico_CEC2017_PreExperimentos_Paper2.md`. Este roadmap es un **plan actualizado**, no evidencia de que los defectos CEC hayan sido reparados ni de que los resultados experimentales estén disponibles.
