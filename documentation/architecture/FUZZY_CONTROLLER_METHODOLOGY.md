# Metodología del controlador difuso PSO-FCS v2

**Estado:** decisiones aprobadas para integración; la campaña principal todavía
requiere piloto y autorización explícita.
**Fecha:** 23 de octubre de 2026.

## Contrato congelado para el estudio de solapamiento

El controlador regula exclusivamente la inercia `w` de PSO a partir de dos
antecedentes: diversidad de Hussain normalizada y progreso de iteración. La
inferencia aprobada es Mamdani tipo 1 con conjunción/implicación `min`,
agregación `max`, centroide sobre 501 puntos y escalamiento a `[0.1, 0.9]`.

El factorial principal mantiene funciones triangulares y cruza:

- overlap geométrico compartido `o={0, 0.5, 1}`;
- granularidad `n={3, 5, 7, 9}`;
- base de reglas `R={R1,...,R8}`.

Esto produce 96 tratamientos PSO-FCS. La infraestructura permite overlap
independiente para diversidad, progreso y salida, pero esa modalidad se reserva
para ablaciones posteriores y no modifica el factorial principal.

## Definición triangular y frontera en cero

Para centros adyacentes separados por `Delta`, la semianchura es:

```text
h(o) = Delta * (1 + o) / 2
```

Se conserva `o=0` exacto, no se sustituye por 1 %. El nivel 0 caracteriza la
ausencia de una región de intersección positiva, la discontinuidad y los casos
de frontera que forman parte de las preguntas de investigación. En un punto
medio sin membresía positiva se aplica `nearest_center_tie_upper`: se selecciona
el centro más cercano y, ante empate exacto, la etiqueta superior recibe grado
1. La política no restaura Ruspini y debe registrarse como parte del tratamiento.

Una prueba con 1 % puede realizarse como sensibilidad secundaria, pero no es un
nivel del factorial principal.

## Familia gaussiana preparada

`gaussian_v1` utiliza un índice geométrico basado en el radio efectivo `2 sigma`:

```text
2 sigma = h(o)
sigma(o) = Delta * (1 + o) / 4
```

Así, en overlap nominal 0 los intervalos efectivos ±2σ se tocan; en 100 %, el
radio 2σ alcanza el centro vecino. Una gaussiana ordinaria conserva soporte
infinito y en 2σ vale `exp(-2)`, por lo que el 0 % es nominal/efectivo, no
solapamiento matemático nulo. Gaussianas están implementadas para estudios
posteriores, pero quedan fuera del factorial triangular principal.

## Diversidad de Hussain y normalización

Se conserva la implementación histórica versionada `hussain_diversity_v1`:

```text
H(t) = mean(|x_ij(t) - mean_i(x_ij(t))|)
D(t) = H(t) / max_{tau<=t} H(tau)
```

La versión 1 conserva el redondeo histórico de `H(t)` a tres decimales. Si el
máximo histórico es cero, `D(t)=0`. Una futura versión sin redondeo deberá tener
otra identidad y no podrá mezclarse dentro de la misma campaña.

## Evaluación inicial y progreso

La población inicial se genera y evalúa antes del bucle. Después se calcula
`H(0)`, se inicializa el máximo histórico y se registra el checkpoint 0 con
`progress=0`; no se aplica ni se registra una inercia ficticia en ese punto.

Las transiciones PSO se numeran `t=1,...,T` y el controlador utiliza:

```text
progress(t) = t / T
```

En la primera transición se observa todavía la población inicial, normalmente
`D=1`, y se produce el primer `w`. La población resultante se evalúa y registra
en el checkpoint 1 junto con la inercia que la produjo.

## Configuración y persistencia

La política se identifica como `fuzzy_inertia_mamdani`, versión 1. La
configuración resuelta persiste familia, definición de overlap, granularidad,
reglas, métrica, normalización, progreso, inferencia, frontera, malla del
centroide y límites de `w`. No se admiten ecuaciones evaluadas desde texto.

El ejemplo ejecutable mínimo está en
`config/campaigns/cec2017_pso_fcs_overlap.example.json`. Es una prueba de
integración y no una autorización para lanzar la campaña exhaustiva.

## Instrumentación implementada y preparación científica futura

Las trazas por iteración reciben diversidad de entrada, progreso, grados de
pertenencia, reglas activas, fuerzas de disparo, salida normalizada, reglas
evaluadas y omitidas, tiempo exclusivo del FIS, eventos de frontera, ausencia de
activación, fallbacks y `w`. Al terminar la réplica se persisten los totales de
llamadas, tiempo, reglas evaluadas/omitidas y casos borde.

Existen `dense_v1` y `sparse_v1`. La regresión automatizada compara ambas en una
malla de estados, para las dos familias disponibles y los tres niveles de
overlap, y exige igualdad de reglas activas y salida hasta tolerancia numérica.
La temporización abarca únicamente `controller.infer`: no incluye el cálculo de
diversidad ni la transición de PSO.

Antes de una campaña científica todavía debe realizarse un microbenchmark
representativo con repeticiones, orden aleatorizado y entorno controlado. Este
microbenchmark prepara futuros estudios, pero no bloquea la finalización de la
plataforma v2 ni autoriza por sí mismo una campaña principal.
