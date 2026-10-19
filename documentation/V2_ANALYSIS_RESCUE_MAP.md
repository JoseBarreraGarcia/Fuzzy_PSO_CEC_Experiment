# Mapa de rescate del análisis para v2

**Estado:** inventario funcional; no se han retirado aún los scripts fuente.  
**Objetivo:** seleccionar capacidades autoritativas antes de consolidar código.

## 1. Capas objetivo

```text
SQLite sellada o exportación verificada
                 ↓
         carga y validación
                 ↓
 métricas derivadas y agregaciones
                 ↓
 inferencia y análisis jerárquico
                 ↓
       tablas y visualizaciones
```

Cada capa deberá aceptar entradas explícitas y devolver datos antes de escribir
archivos. Ningún módulo podrá ejecutar consultas, análisis o gráficos durante
su importación.

## 2. Capacidades y fuentes a rescatar

| Capacidad v2 | Fuentes actuales | Decisión de rescate |
|---|---|---|
| Carga de réplicas | `analysis_modules/level1_raw_data.py`, `analysis_modules_cec/level1_raw_data_cec.py` | Unificar tras definir el nuevo esquema; separar SQL de transformación. |
| Lectura de trazas | `level1_raw_data_cec.py`, `convergence_curves_cec.py`, `w_relationships_cec.py` | Crear un lector único del formato versionado de métricas. |
| Nombres de configuraciones | Parsers CEC/WEA y MDPI `_naming.py` | Una sola representación estructurada; el nombre visible no será un identificador. |
| Descriptivos | `level2_aggregated*.py`, `comprehensive_benchmark_analysis.py`, MDPI `21_*` | Tomar las funciones validadas de MDPI como referencia y generalizarlas. |
| Rankings | `level3_disaggregated.py`, WEA y MDPI `21_*` | Consolidar por nivel y declarar unidad experimental. |
| Convergencia | `convergence_curves_cec.py`, `convergence_analysis_cec.py`, CLEI `b2_*` | Usar sólo trazas reales; conservar bandas, submuestreo y paneles como presentación. |
| Diversidad | `diversity_analysis_cec.py`, `level2_aggregated_cec.py` | Prohibir que datos simulados o reconstruidos se presenten como observados. |
| Dinámica de `w` | `detailed_w_analysis.py`, `w_relationships_cec.py`, `w_verification_3d.py`, WEA | Distinguir `w` observado de `w` reconstruido y registrar el método. |
| Controlador difuso | `b1_rule_activation.py`, `input_set_analysis.py`, WEA | Migrar activación, entradas y granularidad al registro de métricas. |
| Escalabilidad | MDPI `04_run_scaling_curves.py`, `comprehensive_benchmark_analysis.py` | Rescatar ajuste de pendiente con entrada tabular explícita. |
| Mapas media-dispersión | MDPI `15_generate_mean_dispersion_maps.py` | Separar cálculo, selección de casos y renderizado. |
| Paisajes | MDPI `16_generate_benchmark_landscapes.py`, `Graficos_Benchmark/*.py` | Unificar visualizador y mantenerlo fuera del análisis inferencial. |
| A12 y Mann–Whitney | MDPI `22_verify_independent_statistical_tests.py` | Convertir implementaciones independientes en pruebas/oráculos pequeños. |
| Wilcoxon/Friedman | WEA y MDPI `21_*` | Generalizar con diseño pareado explícito y validación de réplicas. |
| Holm | MDPI `23_table11_holm_assessment.py` | Convertir en función que reciba una familia declarada y preserve `family_id`. |
| Figuras y tablas | Todos los bloques | Mantener como consumidores; nunca como fuente de datos. |

## 3. Fuentes que requieren especial cautela

- `diversity_analysis_cec.py` contiene una ruta llamada
  `extract_or_generate_diversity_data`; v2 no debe fabricar observaciones
  ausentes. Una reconstrucción sólo puede existir como estimación marcada y no
  participar en pruebas como dato observado.
- `w_relationships_cec.py`, `w_verification_3d.py` y WEA reconstruyen valores de
  `w` en algunos recorridos. Debe distinguirse `observed`, `reconstructed` y
  `expected_from_controller`.
- `b1_rule_activation.py` apunta directamente a una base de CLEI fechada; se
  rescata el cálculo, no la ruta ni esa campaña.
- varios módulos importan la base y fijan rutas `Resultados/...` globales. Esto
  impide pruebas aisladas y debe eliminarse durante la migración.
- los scripts MDPI `21_*`, `22_*` y `23_*` tienen las verificaciones más
  completas, pero están ligados al dataset final y no deben ejecutarse como
  pipeline general sin parametrización.

## 4. Componentes autoritativos propuestos

| Componente futuro | Responsabilidad |
|---|---|
| `analysis/io.py` | Leer esquema SQLite versionado o exportación verificada. |
| `analysis/schema.py` | Validar columnas, tipos, unidades, réplicas y procedencia. |
| `analysis/naming.py` | Etiquetas de presentación derivadas de configuración estructurada. |
| `analysis/descriptive.py` | Resúmenes sin decisiones inferenciales implícitas. |
| `analysis/ranking.py` | Rankings con nivel y unidad experimental explícitos. |
| `analysis/statistics.py` | Tests, tamaños de efecto y ajustes por familia. |
| `analysis/convergence.py` | Alineación por evaluaciones y curvas con incertidumbre. |
| `analysis/dynamics.py` | Diversidad, exploración/explotación y parámetros adaptativos. |
| `analysis/fuzzy.py` | Entradas, pertenencias, reglas y salidas del controlador. |
| `analysis/scaling.py` | Efecto de dimensión y presupuesto. |
| `analysis/plots.py` | Presentación sin recalcular silenciosamente estadísticas. |

Los nombres son destinos de diseño y podrán ajustarse al crear `src/`; no
autorizan todavía movimientos masivos.

## 5. Fixtures mínimos necesarios

1. Resultados finales sintéticos con dos algoritmos, dos instancias y varias
   réplicas.
2. Trazas cortas con evaluaciones, fitness, diversidad y `w` observado.
3. Caso con métrica no aplicable, distinto de dato faltante por error.
4. Caso pareado con semillas/réplicas alineadas y caso no pareado.
5. Familia pequeña de valores `p` con ajuste Holm conocido.
6. Caso con óptimo cero para impedir divisiones inválidas en *gap* relativo.
7. Caso restringido con factibilidad y violación.

Los fixtures no reproducen conclusiones de los artículos y no incluirán las 31
corridas reales.

## 6. Condición para retirar cada fuente histórica

Un script histórico sólo podrá salir de v2 cuando:

- su capacidad reusable tenga una función de destino;
- las fórmulas y supuestos estén documentados;
- exista al menos un fixture y una prueba;
- se haya comprobado equivalencia sobre un extracto autorizado cuando proceda;
- no haya imports ni rutas operativas que lo referencien;
- su ubicación en el commit histórico esté verificada.

## 7. Orden recomendado de implementación

1. Especificar esquema v2 y registro de métricas.
2. Crear fixtures y validación tabular.
3. Implementar lectura sin efectos laterales.
4. Migrar descriptivos y métricas derivadas.
5. Migrar tests estadísticos y familias Holm.
6. Migrar convergencia y dinámica.
7. Migrar visualizaciones.
8. Comparar resultados y retirar duplicados históricos.
