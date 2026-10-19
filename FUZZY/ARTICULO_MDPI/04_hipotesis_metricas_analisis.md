# Preguntas de investigación, métricas y análisis final

**Estado: 15 de octubre de 2026.** Este documento resume el diseño ejecutado y los análisis que respaldan la versión final del artículo *Sensitivity of Fuzzy-PSO Inertia Control to Linguistic Granularity and Rule-Base Structure*. Los criterios históricos y análisis exploratorios anteriores se preservan en `archive/project_status_history_20261015/04_hipotesis_metricas_analisis_pre_final.md`; no constituyen la metodología inferencial vigente.

## 1. Diseño y datos

- **Benchmark:** funciones clásicas F1–F23 en 62 instancias función–dimensión. F1–F13 se evaluaron en dimensiones 10, 30, 50 y 100; F14–F23, en sus dimensiones fijas.
- **Configuraciones:** PSO clásico y 32 controladores PSO-FCS, formados por granularidad $n\in\{3,5,7,9\}$ y patrón de consecuentes R1–R8. Identificador de lectura: `FCS-n-Rk`.
- **Presupuesto:** población de 20, 1000 iteraciones y 31 corridas por configuración–instancia; 63 426 registros completados.
- **F14:** los resultados finales usan la función de Shekel Foxholes con los pesos canónicos $1,\ldots,25$.
- **Semillas:** cada corrida tiene una semilla distinta, calculada como $42+$ identificador global del experimento. Las semillas no se comparten entre configuraciones; `run_id` no se usa como bloque de pareamiento.

El gap normalizado es $(f_{\mathrm{best}}-f^*)/\max(|f^*|,1)$, con valores negativos truncados a cero. Los empates de ranking se asignan con rangos promedio. La unidad de bloque de Friedman para RQ1 es la instancia, no la corrida individual.

## 2. Preguntas y análisis

### RQ1. ¿Cómo difieren los rankings de las configuraciones?

Por instancia se calcula la mediana del gap normalizado sobre 31 corridas y se ordenan las 33 configuraciones. Friedman se aplica a los 62 bloques de instancia y Nemenyi a los pares posteriores.

**Resultado final:** $\chi^2(32)=1052.38$, $p=1.56\times10^{-200}$; CD $=6.591$. FCS-3-R1 ocupa el primer lugar (rango medio 4.774) y PSO el segundo (6.363); ambos quedan en el mismo grupo de diferencia crítica. Se identifican 272 pares Nemenyi significativos de 528.

### RQ2. ¿Cómo varían los rankings entre clases de paisaje?

Las clases descriptivas son unimodal (F1–F7), multimodal escalable (F8–F13) y multimodal de dimensión fija (F14–F23). Los rangos de cada configuración se promedian dentro de cada clase; Kendall $\tau$ describe la concordancia entre rankings.

**Resultado final:** $\tau=0.867$ entre unimodal y multimodal escalable; $\tau=0.083$ entre unimodal y dimensión fija; $\tau=0.080$ entre multimodal escalable y dimensión fija. Los mejores por gap mediano son FCS-3-R5, FCS-3-R1 y FCS-5-R6, respectivamente. Estos grupos difieren simultáneamente en más de una característica del benchmark; las diferencias no aíslan efectos causales de modalidad o dimensionalidad.

### RQ3. ¿Disminuye consistentemente la dispersión entre patrones al aumentar $n$?

RQ3 es **descriptiva**; no estima una interacción factorial ni aplica una prueba inferencial de interacción. Para cada función y granularidad se calcula la desviación estándar entre los ocho patrones, por separado para rangos y para log-gap. Los rangos por instancia se promedian sobre dimensiones dentro de función y configuración; para log-gap se usa la mediana de 31 corridas, la transformación $\log_{10}(\max(g,10^{-12})+10^{-12})$ y la misma agregación por dimensión. Cada función recibe igual peso al resumir las dispersiones.

**Resultado final, medianas entre 23 funciones para $n=3/5/7/9$:** dispersión de rangos 8.884/8.366/8.715/9.374; dispersión de log-gap 0.912/1.170/1.173/0.901. Entre $n=3$ y $n=9$, el spread disminuye en 6/23 funciones para rangos y 11/23 para log-gap; solo 3/23 funciones son no crecientes a través de los cuatro niveles para cada medida. No hay una disminución consistente.

No se asume que `run_id` identifique semillas comunes entre configuraciones. Por tanto, un bootstrap factorial bloqueado por `run_id` no forma parte de la evidencia final de RQ3.

### RQ4. ¿Cómo se compara cada FCS fija con PSO?

Cada FCS se contrasta con PSO por instancia usando muestras independientes de 31 valores de fitness final y una prueba Mann–Whitney $U$ bilateral, asintótica y con corrección de continuidad. El tamaño de efecto es Vargha–Delaney:

$$A_{12}=\frac{\#(x_r<y_s)+\tfrac12\#(x_r=y_s)}{31^2},$$

donde $A_{12}>0.5$ favorece FCS porque se minimiza el fitness. Bonferroni se aplica sobre los 1 984 contrastes (32 configuraciones $\times$ 62 instancias), con $\alpha=0.05/1984=2.5202\times10^{-5}$. Las comparaciones que no alcanzan el umbral son no significativas, no empates ni evidencia de equivalencia.

**Resultado final agregado, W/NS/L:** 22/906/1056 después de Bonferroni. Para FCS-3-R1: 30/30/2 nominal y 16/46/0 tras corrección.

### RQ5. ¿Concuerdan los rankings de los subconjuntos dimensionales?

$S_1$ comprende F1–F13 y $S_2$ F14–F23. La concordancia de Kendall entre los rankings inducidos por gap mediano se presenta descriptivamente.

**Resultado final:** $\tau(S_1,S_2)=0.0947$, $p=0.4507$. Los mejores por gap mediano son FCS-3-R5 en $S_1$ y FCS-5-R6 en $S_2$. El resultado no significativo no establece independencia ni transferibilidad.

## 3. Tabla 11: contrastes entre patrones

Los ocho pares de patrones se comparan, para cada granularidad e instancia, con pruebas Mann–Whitney $U$ bilaterales sobre muestras independientes. Esta familia es distinta de RQ4: $8\times4\times62=1984$ pruebas. Holm se aplica una sola vez sobre toda la familia, con $\alpha=0.05$. La dirección se determina con $A_{12}$; los resultados no significativos se etiquetan como tales.

**Resultado final:** 1450 pruebas son significativas con $p<0.05$ nominal y 1200 permanecen significativas después de Holm. Los ocho patrones dominantes conservan más victorias significativas que derrotas. La clase donde R4 supera más claramente a R3 es multimodal escalable bajo el criterio Holm.

## 4. Runtime y dinámica

- **Runtime:** overhead calculado como $100[\mathrm{median}(t_{FCS})/\mathrm{median}(t_{PSO})-1]$ a partir de medianas de muestras independientes por configuración–instancia; no se emparejan registros por `run_id`. En los 1984 cocientes, la mediana es 27.75% (IQR 19.81–50.94%).
- **Dinámica:** se describen las trayectorias de $w(t)$ y XPL, la convergencia representativa y la dispersión. La asociación entre caída temprana–tardía de $w$ y rango medio es Spearman $\rho=-0.786$, $p=0.021$; es descriptiva y no identifica un mecanismo causal.

## 5. Estado de reproducibilidad

El artículo principal compila a 62 páginas y el Supplementary Information a 43. El paquete suplementario fechado contiene los 63 426 resultados de corrida, semillas, tablas de análisis y figuras. No se ha hecho un depósito público independiente ni se ha asignado un DOI; cualquier declaración de disponibilidad externa requiere aprobación de los autores.
