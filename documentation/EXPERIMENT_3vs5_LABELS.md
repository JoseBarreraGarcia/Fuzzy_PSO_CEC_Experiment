# Experimento: 3 vs 5 Etiquetas Lingüísticas en Fuzzy PSO

## Objetivo
Comparar el desempeño de PSO_FCS con **3 etiquetas lingüísticas** (original) vs **5 etiquetas lingüísticas** (nuevo) para determinar si mayor granularidad en la fuzzy logic mejora la adaptación del inertia weight.

## Cambios Implementados

### 1. **Nuevo Controller: `fuzzy_controller_w_5labels.py`**

Clase `FuzzyInertiaController_5labels` con:

#### Entradas (diversidad e iteración) con 5 etiquetas cada una:
```
Diversidad:        very_low  │  low  │  medium  │  high  │  very_high
                    (0,0.1,0.2) (0.1,0.25,0.4) (0.3,0.5,0.7) (0.6,0.75,0.9) (0.8,0.9,1.0)

Progreso iteración: very_early │ early │ mid │ late │ very_late
                    (0,0.1,0.2) (0.1,0.25,0.4) (0.3,0.5,0.7) (0.6,0.75,0.9) (0.8,0.9,1.0)
```

#### Salida (inertia weight) con 5 etiquetas cada una:
```
Inertia Weight w:  very_low   │   low   │  medium  │   high   │  very_high
Set A:            (0,0.1,0.2) (0.1,0.2,0.35) (0.25,0.4,0.55) (0.45,0.6,0.75) (0.65,0.85,1.0)
Set B:            (0,0.15,0.3) (0.15,0.3,0.45) (0.35,0.5,0.65) (0.55,0.7,0.85) (0.7,0.85,1.0)
Set C:            (0,0.2,0.4) (0.2,0.35,0.5) (0.3,0.5,0.7) (0.5,0.65,0.8) (0.6,0.8,1.0)
Set D:            (0,0.1,0.25) (0.1,0.25,0.4) (0.25,0.4,0.55) (0.45,0.65,0.85) (0.75,0.9,1.0)
```

#### Reglas Mamdani: 5×5 = 25 reglas

Lógica semántica clara:
- Diversidad BAJA + iteración TEMPRANA → exploración máxima (very_high)
- Diversidad BAJA + iteración TARDÍA → aceptar convergencia (low/very_low)
- Diversidad ALTA → favorecer exploración (high/very_high)
- Transiciones suaves en estados intermedios

### 2. **Cambios en `fuzzy_controller_w.py` (3 labels)**

- **wMin** cambió: `0.1` → `0.0`
- **wMax** cambió: `0.9` → `1.0`
- Función factory agregada: `get_fuzzy_controller(w_set, num_labels=3|5)`

Razones del cambio wMin/wMax:
- Rango [0,1] es **estándar en literatura** de optimización
- Menos confusión: 0 = explorador puro, 1 = explotador puro
- Da más **espacio al fuzzy** para variar (antes: solo 0.8 de rango)
- Comparativas más justas entre versiones

### 3. **Actualización `Solver/solverBEN.py` y `Solver/solverSCP.py`**

Cambio en inicialización de fuzzy controller:

**Antes:**
```python
from FUZZY.fuzzy_controller_w import FuzzyInertiaController
fcs = FuzzyInertiaController(w_set=w_set, wMin=0.1, wMax=0.9)
```

**Ahora:**
```python
from FUZZY.fuzzy_controller_w import get_fuzzy_controller
num_labels = int(extra_params.get('num_labels', 3)) if extra_params else 3
fcs = get_fuzzy_controller(w_set, num_labels=num_labels)
```

### 4. **Configuración: `experiments_config.json`**

**Antes** (4 variantes):
```json
"PSO_FCS": [
    {"w_set": "A"},
    {"w_set": "B"},
    {"w_set": "C"},
    {"w_set": "D"}
]
```

**Ahora** (8 variantes):
```json
"PSO_FCS": [
    {"w_set": "A", "num_labels": 3},
    {"w_set": "B", "num_labels": 3},
    {"w_set": "C", "num_labels": 3},
    {"w_set": "D", "num_labels": 3},
    {"w_set": "A", "num_labels": 5},
    {"w_set": "B", "num_labels": 5},
    {"w_set": "C", "num_labels": 5},
    {"w_set": "D", "num_labels": 5}
]
```

Sistema automático ya parsea estos parámetros → solvers.

### 5. **Script de Comparación: `compare_3vs5_labels.py`**

Genera:
1. Gráficos de funciones de membresía (3 vs 5 para cada set)
2. Tabla de respuestas en 9 puntos de prueba (d×t combinations)
3. Superficies 3D comparativas

## Experimento Resultante

### Funciones Benchmark (F1, F8, F9, F16)
- **PSO** (baseline): 1 variante
- **PSO_FCS (3 labels)**: 4 variantes (A, B, C, D)
- **PSO_FCS (5 labels)**: 4 variantes (A, B, C, D)

**Total**: 5 MH × 4 funciones × 31 runs = **620 nuevos registros**

### Cuestiones a Investigar

1. **¿Mejora la granularidad?** → 5 labels > 3 labels?
2. **¿Qué set es mejor?** → A vs B vs C vs D en ambas versiones
3. **¿Qué es más importante?** → Número de etiquetas vs semántica del set?
4. **¿Se aproxima PSO_FCS:5labels a PSO?** → Reducción de gap?

### Métricas de Interés

Para cada (función, MH, num_labels):
- **Mean fitness** (mejor = menor)
- **Std dev** (consistencia)
- **Gap a óptimo** (%)
- **Convergencia** (iteración a nivel de plateau)
- **Adaptabilidad de w** (rango usado, cambios por iter)

## Ejecución del Experimento

```bash
# 1. Generar gráficos comparativos
python compare_3vs5_labels.py

# 2. Reiniciar BD (borra resultados anteriores)
python reiniciarDB.py

# 3. Poblar con 8 variantes PSO_FCS
python poblarDB.py

# 4. Ejecutar todos los experimentos
python main.py

# 5. Analizar resultados
python analisis.py
```

## Diferencias Clave

| Aspecto | 3 Labels | 5 Labels |
|---------|----------|----------|
| Reglas | 9 (3×3) | 25 (5×5) |
| Granularidad w | Baja | Alta |
| Transiciones | Abruptas | Suaves |
| Complejidad | Baja | Media |
| Precisión | ±0.15 w | ±0.10 w |
| wMin | 0.0 | 0.0 |
| wMax | 1.0 | 1.0 |

## Esperado vs Resultado

**Hipótesis Optimista:**
> 5 labels → mejor granularidad → mejor adaptación → PSO_FCS(5) ≈ PSO en performance

**Hipótesis Realista:**
> 5 labels → más reglas pero mismo problema fundamental → pequeña mejora (5-15%)

**Hipótesis Conservadora:**
> Mayor complejidad sin cambio semántico → sin mejora significativa

---

**Próxima iteración:** Si 5 labels no mejora sustancialmente, pasamos a **fuzzy schemes** (discreto vs continuo) como planeado originalmente.
