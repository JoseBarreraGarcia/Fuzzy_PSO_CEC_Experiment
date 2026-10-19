# Diagnóstico técnico CEC 2017 y condiciones previas al Paper 2

**Proyecto:** *Beyond Ruspini Partitions: Membership-Function Overlap, Rule Activation, and Computational Trade-offs in Mamdani Fuzzy-Controlled Particle Swarm Optimization*  
**Fecha:** 19 de octubre de 2026  
**Estado:** diagnóstico preliminar; no autoriza todavía la campaña experimental.  
**Fuentes:** archivo `cec2017.rar` facilitado para revisión; `README_benchmark_functions.md`; observaciones de la auditoría técnica reportada en la conversación. **Alcance de la evidencia:** los resultados numéricos detallados consignados abajo proceden de la revisión previa descrita en esta conversación; no representan una segunda validación independiente ni equivalencia certificada con la referencia oficial.

## 1. Dictamen ejecutivo

**NO-GO para lanzar las ejecuciones CEC 2017 con la implementación actual sin corregir y validar.** Se reportó un defecto numérico de normalización de pesos en las funciones de composición F21–F30 que produce `NaN` cuando la evaluación coincide exactamente con un vector de desplazamiento. La ejecución de pruebas aleatorias con resultados finitos no basta para descartar estos defectos ni para demostrar fidelidad a la suite oficial.

**Recomendación:** conservar provisionalmente la implementación local como candidata, corregir el defecto, implementar pruebas automatizadas y contrastar sus valores contra una referencia independiente con idénticos datos de desplazamiento, rotación y permutación. Solo después congelar una versión apta para experimentos.

## 2. Inventario documentado

- **Suite clásica:** `Problem/Benchmark/Problem.py`, F1–F23. Útil como estudio de continuidad, no equivale a CEC 2017.
- **CEC 2017 local:** `Problem/Benchmark/CEC/cec2017/`, módulos descritos en el README: `simple.py`, `hybrid.py`, `composition.py`, `functions.py`, `transforms.py`, `basic.py` y datos asociados.
- **Tercera opción:** `opfunu`, integrada parcialmente desde `BD/sqlite.py`; el README enumera únicamente seis funciones CEC 2017 configuradas mediante esta ruta, por lo que su cobertura en el *pipeline* debe comprobarse antes de considerarla sustituto directo.
- **Identificadores distintos:** `F24CEC2017` (implementación local) y `F242017` (`opfunu`) son convenciones diferentes; nunca identificar una función únicamente por el prefijo.
- **F2:** aparece implementada en el paquete, pero debe excluirse de la batería CEC 2017 que se use en la publicación, respetando su situación retirada/deprecada y preservando la numeración oficial de las restantes 29 funciones.

## 3. Hallazgos de la revisión previa y nivel de certeza

| ID | Hallazgo reportado | Severidad | Estado de validación |
|---|---|---|---|
| CEC-01 | F21–F30 devuelven `NaN` al evaluar el primer punto de desplazamiento para D30 y D50. | **Crítico** | Reportado mediante ejecución previa; reproducir con test automatizado y conservar salida. |
| CEC-02 | En `composition.py`, el peso para distancia nula se establece como `inf` y la normalización puede efectuar `inf/inf`. | **Crítico** | Causa señalada en la revisión previa; inspeccionar la línea exacta en la versión congelada. |
| CEC-03 | Para puntos aleatorios, las 29 funciones seleccionadas devolvieron valores finitos y deterministas en D10, D30, D50 y D100. | Favorable pero insuficiente | Pruebas de humo reportadas; no prueban exactitud respecto de CEC oficial. |
| CEC-04 | F9 mostró una desviación aproximada de 3,26 en D30 y 5,08 en D50 al evaluar el vector interpretado como desplazamiento. | Importante | **Por investigar**: puede intervenir la transformación o una hipótesis incorrecta sobre el óptimo; no declarar F9 defectuosa sin referencia. |
| CEC-05 | Otras funciones mostraron desviaciones pequeñas en la evaluación de vectores de desplazamiento. | Importante | Determinar si la desviación es inherente a la construcción de cada función o a un error. |
| CEC-06 | Errores secundarios en ejemplos o textos impresos de `example.py`. | Menor | Verificar; sin relevancia principal para el cálculo hasta comprobar integración. |
| CEC-07 | No se ha revisado todavía el despacho efectivo desde `solverBEN.py`, la persistencia y las configuraciones reales. | **Crítico para el proyecto** | Pendiente por falta del resto de los archivos del repositorio. |

## 4. Corrección necesaria: pesos de composición

Para una función de composición con pesos `w_i`, la coincidencia exacta con un centro produce distancia nula. No es correcto formar pesos infinitos para normalizarlos directamente, porque puede obtenerse `inf/inf = NaN`.

**Especificación para la corrección:**

1. Detectar distancias nulas con el criterio numérico establecido por la referencia, no con una tolerancia arbitraria introducida sin justificación.
2. Asignar el peso correspondiente a la componente coincidente conforme a la formulación de referencia; aclarar qué hacer si, de forma excepcional, coincide más de un centro.
3. Calcular la normalización estable para distancias no nulas, evitando desbordamientos y divisiones no finitas.
4. Verificar continuidad o comportamiento límite numérico a ambos lados del centro: `x=s`, `s ± εe_j` para varios ε.
5. Ejecutar regresión sobre **todas** las composiciones F21–F30 y dimensiones admitidas.
6. No sustituir un `NaN` por un número fijo ni desplazar artificialmente todos los puntos de evaluación: eso ocultaría el error.

**Criterio de aceptación:** todas las salidas de prueba son finitas y coinciden con una referencia validada dentro de tolerancias predefinidas; los casos de coincidencia exacta tienen cobertura explícita de tests.

## 5. Auditoría independiente de funciones

### 5.1 Manifiesto de identidad

Para cada una de las 29 funciones: registrar `source_id`, número oficial `f_i`, tipo (básica/híbrida/composición), denominación, dominio, dimensiones, valor óptimo/bias, archivo fuente, versión, hashes SHA-256 de código y datos (`shift`, `rotation`, `shuffle`). Excluir F2 sin renumerar el resto.

### 5.2 Pruebas automáticas mínimas

1. **Carga:** importación sin errores y presencia efectiva de matrices/vectores en las dimensiones utilizadas.
2. **Determinismo:** dos evaluaciones del mismo punto en las funciones deterministas deben coincidir.
3. **Finitud:** vectores aleatorios, ceros, límites, puntos próximos a transformaciones y casos patológicos reportados.
4. **Dimensionalidad:** formas y dimensiones adecuadas; fallo explícito para las no admitidas.
5. **Óptimos:** comprobar valores conocidos solo cuando se disponga de vectores óptimos oficiales y se haya verificado su correspondencia con los datos de transformación.
6. **Comparación cruzada:** evaluar **los mismos vectores y los mismos datos oficiales** con implementación local y referencia; medir diferencia absoluta y relativa, con umbrales fijados antes del análisis.
7. **Perturbaciones locales:** pequeñas variaciones alrededor de centros de composición, verificando ausencia de `NaN` y de saltos no justificados.
8. **Híbridas/composición:** comprobar indexaciones, permutaciones, segmentos y dimensiones intermedias.
9. **Integridad:** registrar versión de NumPy, plataforma, entorno y artefactos de entrada.

**Nota de comparabilidad:** dos implementaciones de un mismo nombre matemático que cargan distintas matrices de rotación o vectores de desplazamiento no necesariamente deben dar el mismo valor. Auditar primero la identidad de esos datos.

## 6. Integración del benchmark con PSO (pendiente)

Solicitar/inspeccionar: `Solver/solverBEN.py`, despachador de benchmarks, `BD/sqlite.py`, `1_0_poblarDB.py`, `2_main.py`, `config/experiments.json` y código del generador de semillas.

Comprobar:

- Nombres `F1CEC2017` a `F30CEC2017` asignados a funciones correctas; F2 excluida.
- Límites, dimensión y óptimo guardados correctamente; no confundir fitness bruto con `f(x)-f*`.
- Orden de argumentos, conversión de vectores y validación de tipos/dimensiones.
- Presupuesto real `nfev`, manejo de límites y condiciones de parada idénticos.
- Excepciones, `NaN`/`inf` y fallos marcados como errores; prohibido clasificarlos como buenos resultados.
- Resultados etiquetados por versión de benchmark y hash del código/datos.
- Control de aleatoriedad: CEC 2017 es determinista si sus datos son fijos; las semillas 42–72 corresponden a PSO, no a transformar arbitrariamente los óptimos de la suite.

## 7. Protocolo estadístico y semillas del Paper 2

- Réplicas `r=1,...,31`; **semilla maestra `41+r`**, es decir, `42,...,72`.
- Misma semilla maestra por réplica para las 96 configuraciones y PSO en cada instancia.
- Flujos separados para inicialización y coeficientes de PSO, con consumo estable por iteración, partícula y coordenada; ninguna clave de configuración debe alterar los flujos comunes.
- Verificar condiciones iniciales idénticas entre tratamientos emparejados, guardar checksums y pruebas de reproducción fuera de orden.
- Diferencias pareadas **dentro de instancia y réplica**; rankings entre instancias son una unidad de análisis distinta; la correlación de dimensiones de una misma función debe reconocerse.
- Todos los tratamientos se ejecutan nuevamente, incluso las 32 configuraciones overlap 100 % y PSO clásico; no mezclar corridas históricas como bloques CRN.

## 8. Selección de suite y presupuesto

**Candidato principal:** CEC 2017, 29 funciones sin F2, inicialmente D30 y D50. **Control secundario:** F1–F23, con extensión acotada y predeterminada. **Alternativa técnica:** `opfunu` solo si supera equivalencia y la integración resulta confiable.

Antes de congelar el diseño, definir si se seguirá el presupuesto oficial por dimensión o uno propio y, en este último caso, evitar afirmar adhesión íntegra al protocolo de competición. Las pruebas oficiales pueden emplear distinta cantidad de ejecuciones y evaluaciones que las 31 réplicas del estudio: distinguir expresamente *uso de funciones CEC* de *reproducción del protocolo CEC*.

No calcular el costo computacional únicamente por cantidad de ejecuciones: las funciones híbridas y de composición tienen costos por evaluación superiores a muchas funciones clásicas. Medir duración real en pilotos.

## 9. Secuencia de implementación y puntos GO/NO-GO

| Fase | Acción | Evidencia requerida |
|---|---|---|
| G0 | Congelar código/datos recibidos | Hashes y manifiesto de archivos |
| G1 | Reproducir y corregir CEC-01/02 | Tests de regresión F21–F30 |
| G2 | Examinar F9 y desviaciones | Comparación referencial justificada |
| G3 | Auditar todas las funciones/dimensiones | Informe con resultados numéricos y tolerancias |
| G4 | Auditar `solverBEN.py` y base de datos | Pruebas extremo a extremo de despacho y `nfev` |
| G5 | Implantar semillas maestras 42–72 | Tests CRN, replay y checksums |
| G6 | Validar overlap 0/50/100, inferencia y límites | Tests de cobertura, frontera, reglas y finitud |
| G7 | Ejecutar piloto y estimar costo | Logs, tiempos, calidad y reproducibilidad |
| **GO** | Autorizar campaña experimental | G0–G7 completos, versionados, sin defectos críticos |

## 10. Cambios exigidos al roadmap del Paper 2

El archivo previo `Roadmap_Paper_2_Ruspini_Overlap_PSO_FCS.md` **no está totalmente actualizado**:

1. **Benchmark:** aún declara F1–F23 como experimento principal (62 instancias), con CEC como validación externa. Cambiar CEC 2017 a **candidato principal, condicionado a superar la auditoría**, y F1–F23 a bloque secundario; recalcular número de ejecuciones según dimensiones aprobadas.
2. **Semillas:** sustituir la derivación general desde `(global_seed, instance_id, replicate_id)` como semilla maestra por el contrato explícito **`master_seed(r)=41+r`** y derivación de subflujos desde esa semilla, con identificación de instancia sin romper el CRN intrainstancia.
3. **Gate de benchmarks:** incorporar G0–G4 como bloqueo obligatorio previo a pilotos y a la campaña.
4. **Estadística:** fijar contrastes pareados intrainstancia y criterios para comparar tendencias entre familias y dimensiones; no tratar instancias correlacionadas como problemas independientes sin discusión.
5. **Eficiencia:** separar tiempo de evaluación de función, inferencia y solver completo; costear las funciones de composición.
6. **Proveniencia:** registrar hashes de la implementación y transformaciones, versión de dependencias y batería de pruebas.
7. **Factibilidad:** el antiguo total **186.434 ejecuciones** corresponde a F1–F23 (62 instancias × 31 repeticiones × 97 tratamientos) y **ya no describe** la campaña principal si pasa a CEC 2017.

## 11. Limitaciones de este diagnóstico

Este documento separa **hallazgos reportados en la revisión previa**, que requieren su registro y reproducción en tests, de **validaciones todavía no realizadas**. No certifica concordancia con código oficial ni inspecciona el repositorio completo; la decisión definitiva de biblioteca depende de esos pasos. No se ha proporcionado un *journal* objetivo definitivo, por lo que cualquier conclusión sobre ajuste editorial Q1 sigue siendo provisional.
