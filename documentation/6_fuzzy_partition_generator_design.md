# Diseño: Generador Automático de Particiones Difusas

## Motivación
Simplificar la definición de fuzzy sets para cualquier variable (w, diversity, progress, fitness improvement, etc.) usando parámetros semánticos en vez de coordenadas numéricas (a,b,c) de triángulos.

## Contexto previo: wMin/wMax y rescalado
- PSO estándar: w decrece linealmente de 0.9 a 0.1 (verificado en PSO.py y solverSCP.py)
- FIS opera siempre en universo normalizado [0,1], luego rescala: `w = wMin + w_norm * (wMax - wMin)`
- Compresión del centroide: el centroide Mamdani nunca alcanza 0 ni 1
  - 3L: w_norm máximo real ≈ 0.75, mínimo real ≈ 0.25
  - 5L: w_norm máximo real ≈ 0.83, mínimo real ≈ 0.167
- wMax=1.2 compensa la compresión superior (0.75×1.2=0.90, equipara a PSO estándar)
- wMin=0.0 se mantiene (decisión deliberada): el mínimo real queda en 0.30 (3L) / 0.20 (5L), que es razonable y justificable

---

## Parámetros de una partición difusa (4 parámetros)

| Parámetro | Tipo | Default | Descripción |
|---|---|---|---|
| `n_labels` | int | 3 | Número de etiquetas lingüísticas |
| `spacing` | `"proportional"` o lista de floats | `"proportional"` | Distribución de centros |
| `overlap` | int (0–100) | 100 | Solapamiento entre MFs adyacentes |
| `shoulders` | lista de strings | `[]` | `[]`, `["left"]`, `["right"]`, `["left","right"]` |

### Definición de overlap
- 0% = los brazos de dos MFs adyacentes se tocan en el punto medio entre centros (un solo punto de contacto, sin zona muerta significativa)
- 100% = el brazo de cada MF llega al centro del vecino (partición de Ruspini, Σμ=1)
- Fórmula: `brazo = d/2 + (p/100) * (d/2)` donde d=distancia entre centros, p=overlap%

### Efecto de shoulders en "proportional"
- `spacing="proportional"` distribuye centros equidistantes DENTRO del espacio utilizable dado los shoulders
- Con ambos hombros: centros en [0.0, 0.5, 1.0] para n=3 (d=0.5)
- Sin hombros: centros en [0.25, 0.5, 0.75] para n=3 (d=0.25) — necesitan margen para brazos exteriores
- Con hombro solo izquierdo: distribución asimétrica — centros ≈ [0.0, ~0.4, ~0.8]
- **Importante**: "proportional" significa equidistante relativo al espacio utilizable, no al dominio completo

---

## Reglas difusas: también parametrizables

### Opción A: Matriz explícita (control total)
```json
"R1_3x3": {
  "n_input_labels": 3,
  "matrix": [
    ["high",   "high",   "medium"],
    ["high",   "medium", "low"],
    ["medium", "low",    "low"]
  ]
}
```
Filas = diversity labels (low→high), columnas = progress labels (early→late).

### Opción B: Reglas generadas por patrón
Patrones base (ej: "diagonal", "exploitation_biased", "exploration_biased") que generan la matriz automáticamente para cualquier n_labels. Opcionalmente con overrides puntuales:
```json
"R_auto_diagonal": {
  "pattern": "diagonal",
  "n_input_labels": 5,
  "overrides": {"0,4": "very_high", "4,0": "very_low"}
}
```

### Decisión: Ambas opciones soportadas
- Si se proporciona `"matrix"` → se usa directamente (Opción A)
- Si se proporciona `"pattern"` → se genera automáticamente (Opción B)
- La generación automática es la propuesta principal; la matriz explícita es el fallback para control total

---

## Estructura de archivos de configuración

### `config/fuzzy_partitions.json` (nuevo)
```json
{
  "partitions": {
    "input_diversity_3L": {
      "n_labels": 3,
      "spacing": "proportional",
      "overlap": 100,
      "shoulders": ["left", "right"]
    },
    "output_w_3L_no_shoulders": {
      "n_labels": 3,
      "spacing": "proportional",
      "overlap": 75,
      "shoulders": []
    },
    "output_w_5L_custom": {
      "n_labels": 5,
      "spacing": [0.0, 0.2, 0.5, 0.8, 1.0],
      "overlap": 80,
      "shoulders": ["left", "right"]
    }
  },
  "rules": {
    "R1_3x3": {
      "n_input_labels": 3,
      "matrix": [...]
    },
    "R_auto_diag_5": {
      "pattern": "diagonal",
      "n_input_labels": 5
    }
  }
}
```

### `config/experiments.json` (referencia por nombre)
```json
"PSO_FCS": [{
  "partition_input_div": "input_diversity_3L",
  "partition_input_prog": "input_diversity_3L",
  "partition_output_w": "output_w_3L_no_shoulders",
  "rule_set": "R1_3x3",
  "wMin": 0.0,
  "wMax": 1.2
}]
```

---

## Implementación: controlador único

- Reemplazar `fuzzy_controller_w_3L.py` y `fuzzy_controller_w_5L.py` con un único `fuzzy_controller_auto.py`
- Los archivos 3L y 5L se mantienen para reproducibilidad de experimentos ya corridos
- La lógica Mamdani (fuzzificación → inferencia → defuzzificación) es idéntica; solo cambian MFs y reglas, que ahora vienen de config
- Funciona para cualquier variable (w, diversity, progress, fitness improvement, etc.)

---

## Validaciones necesarias

1. Sin hombros + overlap bajo + n grande: verificar que d_min > 0 (centros no se compriman a 0)
2. Spacing custom + sin hombros: centro en 0.0 sin hombro izquierdo no tiene espacio → error o ajuste
3. Spacing custom + shoulders parciales: inconsistencia si centro extremo no tiene hombro pero está en el borde
4. Overlap + spacing custom: d variable entre pares → brazos asimétricos por MF (válido pero documentar)
5. n_labels de reglas debe coincidir con n_labels de las particiones de input

---

## Reglas difusas: diseño por forma de curva de w

### Motivación
En vez de diseñar reglas desde la intuición (diversidad baja → explorar más), partir de la **forma deseada de la curva de w(t)** y construir reglas que la produzcan. La diversidad actúa como modulador (±1 label) en vez de driver principal.

### Familias de curvas
- **Cóncava**: baja rápido, explota pronto → candidato para unimodales (F1-F19)
- **Lineal**: descenso uniforme → baseline, replica PSO estándar
- **Convexa**: mantiene w alto, baja tarde → candidato para multimodales (F20-F30)
- **Sigmoide**: meseta alta → caída rápida → meseta baja → funciones híbridas

### Taxonomía de rule sets
| Categoría | Driver principal | Ejemplo |
|---|---|---|
| **Por forma** (concave, linear, convex, sigmoid) | Progress domina, diversity modula | Curva de w predefinida |
| **Por reactividad** (reactive_exploit, reactive_explore, reactive_balanced) | Diversity domina, progress modula | Reglas tradicionales |
| **Híbridas** (adaptive_concave, adaptive_convex) | Ambos con peso similar | Combinación |

### Ejemplo 5×5 cóncava (progress domina)
Filas=diversity(very_low→very_high), Columnas=progress(very_early→very_late)
```
high       medium    low       very_low  very_low
high       medium    low       very_low  very_low
very_high  high      medium    low       very_low
very_high  high      medium    low       very_low
very_high  very_high medium    low       very_low
```

### Ejemplo 5×5 convexa (progress domina, exploración prolongada)
```
very_high  very_high high      medium    low
very_high  very_high high      medium    low
very_high  very_high high      medium    very_low
very_high  very_high very_high high      low
very_high  very_high very_high high      medium
```

### Problema del feedback loop en unimodales (3L)
- Regla `(low_diversity, early) → high_w` asume multimodalidad
- En unimodales, diversidad baja temprana es señal de convergencia correcta
- Con 3 labels no se puede distinguir — `early` cubre 0%-33%
- Con 5 labels: 4 celdas en la zona (baja div, etapas intermedias) permiten transición gradual
- Las reglas por forma (cóncava) resuelven esto: progress domina, diversity solo modula

---

## Visión de alto nivel: Arquitectura de 2 niveles

### Nivel 1: Esquemas difusos como configuraciones atómicas
Cada esquema = (partition_input, partition_output, rule_set, wMin, wMax)
El generador automático de particiones permite crear decenas de esquemas sin código — solo JSON.

Ejemplos de esquemas:
- S1: 3L, overlap 100%, hombros, reglas cóncavas → explotación rápida
- S2: 5L, overlap 75%, sin hombros, reglas convexas → exploración prolongada
- S3: 5L, overlap 100%, hombros, reactive_balanced → adaptativo clásico
- S4: 3L, overlap 50%, hombro derecho, reglas lineales → simula PSO estándar

### Nivel 2: Meta-selector / hiperheurística
Selecciona qué esquema usar basándose en indicadores observables:

Indicadores disponibles:
- Tasa de mejora del fitness (historial de iteraciones)
- Diversidad promedio (cálculo existente)
- Dimensionalidad (de la instancia)
- Landscape estimation / FLA (muestreo inicial)
- NFE consumidos / restantes (contador existente)

Modos de operación:
| Modo | Cuándo cambia esquema | Complejidad |
|---|---|---|
| Estático offline | Pre-ejecución (features del problema) | Baja — clasificador |
| Dinámico por ventana | Cada N iteraciones (indicadores runtime) | Media — switching |
| Dinámico continuo | Cada iteración, blending de esquemas | Alta — portfolio |

### Por qué es competitivo
1. Fuzzy PSO solo pierde cuando el esquema no calza con el problema → buen selector = siempre competitivo
2. Espacio de esquemas finito y enumerable → selección discreta, no optimización continua
3. Esquemas se evalúan offline primero (pipeline actual en CEC2017) → tabla de "qué esquema gana dónde" = training data del meta-selector

---

## Pendiente de diseño
- Definir qué patrones automáticos de reglas soportar y cómo se generan para n_labels arbitrario
- Definir nombres de labels automáticos según n_labels (ej: 3→low/medium/high, 5→very_low/low/medium/high/very_high)
- Definir estructura de la tabla de rendimiento esquema×problema para el meta-selector
- Definir indicadores mínimos viables para el meta-selector estático offline (primer modo a implementar)
- Definir cómo se integra el switching dinámico dentro del loop de PSO_FCS (cambio de FCS en runtime)
- Configurar un fuzzy PSO competitivo en F1-F19 (unimodales) antes de implementar el generador
