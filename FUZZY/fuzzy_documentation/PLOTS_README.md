# Fuzzy Set Visualization Plots

## Overview

Los gráficos en esta carpeta visualizan los **fuzzy sets** (conjuntos borrosos) del sistema de control de inertia weight (w) de PSO. Estos gráficos son útiles para documentación, papers y reportes.

## Generar los Gráficos

```bash
python generate_fuzzy_plots.py
```

Se guardan automáticamente en `FUZZY/plots/`

---

## Gráficos Generados

### 1. `01_fuzzy_input_diversity.png`
**Conjuntos borrosos para la entrada: Diversity Ratio**

- **Variables lingüísticas**: Low, Medium, High
- **Rango**: [0, 1]
  - 0 = población convergida (sin diversidad)
  - 1 = población exploratoria (máxima diversidad)
- **Funciones de membresía**: Triangulares
  - Low: (0.0, 0.2, 0.4)
  - Medium: (0.3, 0.5, 0.7)
  - High: (0.6, 0.8, 1.0)

**Uso**: Muestra cómo se interpreta el nivel de diversidad en el algoritmo

---

### 2. `02_fuzzy_input_progress.png`
**Conjuntos borrosos para la entrada: Iteration Progress**

- **Variables lingüísticas**: Early, Mid, Late
- **Rango**: [0, 1]
  - 0 = inicio del algoritmo
  - 1 = fin del algoritmo
- **Funciones de membresía**: Triangulares
  - Early: (0.0, 0.2, 0.4)
  - Mid: (0.3, 0.5, 0.7)
  - Late: (0.6, 0.8, 1.0)

**Uso**: Muestra cómo avanza el algoritmo en el tiempo

---

### 3. `03_fuzzy_output_w_set_A.png`, `B.png`, `C.png`, `D.png`
**Conjuntos borrosos para la salida: Inertia Weight w (Por cada Set)**

- **Variables lingüísticas**: Low, Medium, High
- **Rango**: [wMin, wMax] = [0.1, 0.9]
- **Función de membresía**: Depende del w_set

**Set A**:
- Low: (0.1, 0.1, 0.45)
- Medium: (0.35, 0.5, 0.65)
- High: (0.55, 0.9, 0.9)
→ Favors exploitation (baja inertia)

**Set B**:
- Low: (0.0, 0.1, 0.4)
- Medium: (0.35, 0.5, 0.65)
- High: (0.6, 0.9, 1.0)
→ Balanced approach

**Set C**:
- Low: (0.0, 0.25, 0.5)
- Medium: (0.25, 0.5, 0.75)
- High: (0.50, 0.75, 1.0)
→ Symmetric distribution

**Set D**:
- Low: (0.0, 0.15, 0.3)
- Medium: (0.20, 0.5, 0.6)
- High: (0.50, 0.75, 0.75)
→ Favors exploitation (lower values)

**Uso**: Muestra cómo cada w_set interpreta los niveles de inertia weight

---

### 4. `04_fuzzy_rules_heatmap.png`
**Mapa de Calor: Base de Reglas Fuzzy**

Visualiza las **reglas Mamdani 3×3**:
- **Filas**: Diversity (Low, Medium, High)
- **Columnas**: Progress (Early, Mid, Late)
- **Celdas**: Salida de la regla (Low w, Med w, High w)

**Lectura de ejemplo**:
- (Low Diversity, Early Progress) → Med w (exploración equilibrada)
- (High Diversity, Late Progress) → Low w (explotación en final)
- (Low Diversity, Late Progress) → Low w (convergencia final)

**Base de reglas completa**:
```
             Early     Mid       Late
Low      → Med w   Low w     Low w
Medium   → High w  Med w     Low w
High     → High w  High w    Low w
```

**Interpretación**:
- Al principio (Early): Priorizar exploración (w más alto)
- En el medio (Mid): Según diversidad
- Al final (Late): Priorizar explotación (w bajo)

---

### 5. `05_fuzzy_w_sets_comparison.png`
**Comparación de Todos los w_sets (A, B, C, D) Lado a Lado**

Muestra las **diferencias entre los 4 w_sets** de inertia weight:
- **Set A**: Más hacia explotación (Low tiene más peso)
- **Set B**: Más balanceado
- **Set C**: Simétrico
- **Set D**: Más hacia explotación que A

**Uso**: Entender qué hace diferente a cada variant (PSO_FCS:A vs :B vs :C vs :D)

---

## Cómo Usar Estos Gráficos

### En Papers/Reportes

```markdown
## Methodology

### 2.1 Fuzzy Inertia Weight Controller

The inertia weight w is controlled using a Mamdani Fuzzy Inference System 
with two inputs and one output:

[Figura: 01_fuzzy_input_diversity.png - Entrada Diversity]
[Figura: 02_fuzzy_input_progress.png - Entrada Progress]
[Figura: 03_fuzzy_output_w_set_A.png - Salida w]

### 2.2 Fuzzy Rules

The control rules are shown in Figure X:

[Figura: 04_fuzzy_rules_heatmap.png]

As can be seen, early iterations favor exploration (higher w values),
while late iterations favor exploitation (lower w values), with a 
transition based on population diversity.

### 2.3 Alternative w_sets

We also tested alternative fuzzy sets:

[Figura: 05_fuzzy_w_sets_comparison.png]

Set A favors exploitation, while Set B is more balanced...
```

### En Documentación

```markdown
# PSO_FCS Variants Configuration

## Set A
- Characteristic: Exploitation-favored
- Best for: Fine-tuning phase
- Configuration plots: [Enlace a 03_fuzzy_output_w_set_A.png]

## Set B
- Characteristic: Balanced
- Best for: General-purpose optimization
- Configuration plots: [Enlace a 03_fuzzy_output_w_set_B.png]
```

---

## Especificaciones Técnicas

- **Formato**: PNG, 300 DPI (publicación)
- **Estilo**: LNCS (Times New Roman, 10pt)
- **Tamaño**: ~100-150 KB por gráfico
- **Resolución**: 1200×700 píxeles (típico)

---

## Regenerar Gráficos

Si modificas los fuzzy sets en `fuzzy_controller_w.py`, simplemente:

```bash
python generate_fuzzy_plots.py
```

Los gráficos se actualizarán automáticamente.

---

## Modificación de Fuzzy Sets

Si quieres agregar nuevos w_sets o modificar los existentes:

1. Edita `FUZZY/fuzzy_controller_w.py` en el método `_build_w_mfs()`
2. Agrega/modifica el diccionario W_SETS
3. Ejecuta `python generate_fuzzy_plots.py`
4. Los nuevos gráficos se generarán automáticamente

**Ejemplo**: Agregar Set E
```python
"E": {
    "high":   (0.65, 0.85, 0.95),
    "medium": (0.40, 0.55, 0.70),
    "low":    (0.05, 0.20, 0.35),
},
```

---

## Referencias en Código

Para usar estos gráficos en tu código:

```python
from FUZZY.fuzzy_plots import generate_all_fuzzy_plots

# Generar todos los gráficos
plots = generate_all_fuzzy_plots(verbose=True)

# Gráfico específico
from FUZZY.fuzzy_plots import plot_fuzzy_output_w_set
path = plot_fuzzy_output_w_set('A')
```

---

## Interpretación Avanzada

### Overlapping (Solapamiento)

El solapamiento entre fuzzy sets determina la suavidad de las transiciones:
- **Alto solapamiento**: Transiciones suaves
- **Bajo solapamiento**: Transiciones abruptas

Nuestro diseño usa **30% solapamiento** (~0.2 de ancho) para balance.

### Forma Triangular

Las funciones de membresía triangulares son eficientes computacionalmente y se interpretan bien lingüísticamente.

### Defuzzificación

Usamos **centroide** para convertir salidas fuzzy a valores crisp de w:

```
w = Σ(μ(w) * w) / Σ(μ(w))
```

---

## Contacto/Reportes

Para incluir estos gráficos en reportes:
- Usa el script `python generate_fuzzy_plots.py` para asegurar versión actual
- Los 8 gráficos se guardan en `FUZZY/plots/`
- Son publication-ready (300 DPI, formato vectorial compatible)
