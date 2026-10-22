# Contrato de datos experimentales y análisis

**Estado:** decisiones metodológicas aprobadas para diseñar v2.  
**Alcance:** contrato; todavía no describe el esquema SQLite implementado.

## 1. Réplica

Una réplica es una corrida independiente de una configuración experimental. En
las campañas habituales se ejecutan 31 réplicas.

Una configuración queda determinada por:

```text
problema + instancia/función + dimensión
+ algoritmo + parámetros
+ presupuesto + configuración difusa
```

Entre réplicas sólo deben variar `replica_index`, semilla y resultados
observados. El identificador autoincremental de la base no define la réplica ni
puede utilizarse como semilla científica.

## 2. Fuente de verdad de una campaña

La base SQLite es la fuente primaria y autoritativa de los datos crudos y de la
procedencia de cada campaña. Debe contener:

- definición y versión de la campaña;
- configuración resuelta, no sólo la ruta de un JSON;
- problema, instancia, función y dimensión;
- algoritmo y parámetros;
- réplica, semilla y presupuesto;
- estado, errores y tiempos;
- resultado final, solución y factibilidad;
- métricas y trazas seleccionadas;
- versiones de código, esquema y definiciones de métricas.

Agregaciones, rankings, pruebas estadísticas, tablas y figuras son derivados y
no deben competir como fuentes primarias.

### Sellado de campaña

Durante la ejecución la base permanece activa. Al finalizar debe cerrarse y
acompañarse de:

```text
base SQLite cerrada
configuración resuelta
versión del esquema
commit del código
manifiesto de procedencia
hashes de integridad
exportación canónica de tablas primarias
```

La exportación sirve para preservación e intercambio; no es otra autoridad. Si
difiere de una base sellada cuyo hash es válido, se regenera desde la base.
Las bases de campañas no se versionan en el repositorio v2.

## 3. Registro de métricas

Todas las métricas relevantes deben formar parte de un registro central. Que
una métrica esté registrada significa que el sistema conoce su definición; no
obliga a almacenarla en todas las campañas.

Cada definición debe declarar:

| Campo | Significado |
|---|---|
| `metric_id` | Identificador estable y legible por máquina. |
| `version` | Versión de la definición o fórmula. |
| `name` | Nombre para documentación. |
| `description` | Semántica y fórmula. |
| `scope` | Campaña, réplica, iteración, individuo, dimensión o evento. |
| `source` | Componente que la calcula y variables de origen. |
| `dtype` y `unit` | Tipo y unidad. |
| `direction` | Minimizar, maximizar, objetivo o sólo diagnóstico. |
| `valid_range` | Dominio esperado y tratamiento de no finitos. |
| `sampling` | Frecuencia permitida. |
| `aggregation` | Agregaciones válidas y advertencias. |
| `missing_policy` | Significado de dato ausente/no aplicable. |

La configuración admitirá:

- `all` para todas las métricas aplicables;
- perfiles `minimal`, `convergence`, `optimizer` y `fuzzy`;
- una lista explícita de `metric_id`;
- inclusión/exclusión adicional y frecuencia de muestreo.

### Métricas mínimas no desactivables

- estado y error de la réplica;
- `replica_index` y semilla;
- objetivo final y solución;
- evaluaciones y presupuesto consumido;
- duración total;
- factibilidad y violación, cuando correspondan.

### Familias que deben estar disponibles

- resultado: mejor, media y dispersión de fitness, *gap* y RDP;
- coste: evaluaciones, iteración, tiempo total y por paso;
- búsqueda: diversidad global y por dimensión, entropía, exploración y
  explotación;
- restricciones: factibilidad, violación y reparación;
- controlador difuso: entradas, grados de pertenencia, reglas activadas,
  fuerza de activación, salida normalizada y parámetro aplicado;
- algoritmo: métricas específicas registradas mediante el mismo contrato.

Las trazas de alta frecuencia podrán guardarse en cada iteración, en puntos de
control o por eventos. La selección controla volumen, no elimina la definición
de la métrica del sistema.

### Base de implementación preparada

La primera versión del contrato está materializada en:

- `src/afcs/metrics/definitions.json`: catálogo versionado, métricas obligatorias y
  perfiles;
- `src/afcs/metrics/registry.py`: carga, validación y resolución sin efectos
  laterales;
- `tests/fixtures/`: réplicas y trazas sintéticas;
- `tests/test_metrics_registry.py`: pruebas de validez y selección.

El catálogo puede sincronizar sus definiciones y selección con el esquema
SQLite v2 preparado, pero todavía no está conectado a los solvers ni al runner
heredado. Por tanto, no cambia los datos que produce una ejecución actual.

El esquema SQLite v2 preparado posteriormente se documenta en
[`../architecture/SQLITE_V2_SCHEMA.md`](../architecture/SQLITE_V2_SCHEMA.md).
Permanece en paralelo al esquema heredado y aún no cambia la ejecución actual.

## 4. Análisis jerárquico

El orden aprobado es:

1. análisis general de tendencias;
2. desagregación por factores relevantes;
3. análisis por función o instancia;
4. análisis de dinámica para explicar relaciones observadas.

Los resultados agregados y específicos estiman efectos diferentes. Una
diferencia entre ellos no implica por sí misma una contradicción; debe
investigarse heterogeneidad, ponderación y posibles efectos tipo Simpson.

## 5. Familias de hipótesis y Holm

Una familia contiene contrastes que responden a una misma pregunta científica.
Pueden existir familias diferentes para comparaciones globales, dimensiones,
familias de funciones, funciones individuales, configuraciones difusas o
granularidad.

El test ómnibus y la corrección post hoc no son lo mismo. Por ejemplo, Friedman
puede detectar diferencias globales y Holm ajustar después las comparaciones
múltiples planificadas. No se deben mezclar automáticamente todos los valores
`p` del proyecto en una sola familia.

Cada resultado inferencial debe registrar:

```text
analysis_id
research_question
analysis_level
family_id
scope
test
raw_p_value
adjusted_p_value
correction
alpha
confirmatory_or_exploratory
```

La familia y el nivel del análisis deben definirse antes de observar los
resultados confirmatorios. Las desagregaciones motivadas posteriormente deben
marcarse como exploratorias.

## 6. Diferencias con el esquema actual

El esquema actual sólo tiene `instancias`, `experimentos`, `resultados` e
`iteraciones`; las trazas se almacenan como CSV dentro de un BLOB. No registra
de forma explícita campaña, réplica, semilla, catálogo de métricas, versión de
esquema ni sellado. Por ello requiere migración y no debe adoptarse sin cambios
como contrato v2.

Además, `Solver/solverBEN.py` escribe actualmente `Divj_max0` en las filas de
iteraciones posteriores, aunque calcula `divj_max` para la iteración corriente.
Esto debe corregirse para campañas v2 y cubrirse con una prueba. Los datasets
históricos no deben modificarse retroactivamente ni reinterpretarse sin dejar
constancia de esta limitación.
