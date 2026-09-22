# Consideraciones Técnicas Pendientes

## 1. Rescalado de Centroides: Dominio Normalizado vs. Rango Efectivo de w

### El problema de la compresión del centroide

En un FIS Mamdani con defuzzificación por centroide (COG), el centroide **nunca alcanza los extremos del universo de discurso** [0, 1]. Esto ocurre porque:

- Las MFs de salida tienen área distribuida → el centroide queda "adentro" del soporte
- Incluso con shoulder MFs (hombros en 0 y 1), los centroides extremos son:
  - **3L (O1):** c_min = 0.1667, c_max = 0.8333
  - **5L (O1):** c_min = 0.1100, c_max = 0.8900

Sin corrección, si configuras `wMin=0.1, wMax=0.9`, el w efectivo sería:
- 3L: [0.23, 0.77] — **no alcanza los extremos declarados**
- 5L: [0.19, 0.81] — **tampoco**

### La solución: rescalado interno del centroide

En `compute_w()` de ambos controllers (3L y 5L), después de la defuzzificación se aplica:

```python
# 1. Centroide crudo (comprimido)
w_norm = centroide_defuzzificado   # ∈ [c_min, c_max], nunca [0, 1]

# 2. Rescalar a [0, 1] real
w_norm = (w_norm - c_min) / (c_max - c_min)   # ahora sí ∈ [0, 1]

# 3. Escalar al rango configurado
w = wMin + w_norm * (wMax - wMin)              # ∈ [wMin, wMax] exacto
```

Las cotas `c_min` y `c_max` se precomputan en `_compute_centroid_bounds()` a partir de las MFs de salida reales → se adaptan automáticamente si se cambia el `w_set`.

### Verificación empírica (sweep 50×50 sobre todo el dominio de entrada)

| Controller | wMin | wMax | w sweep min | w sweep max |
|---|---|---|---|---|
| 3L (O1) | 0.1 | 0.9 | 0.1005 | 0.8995 |
| 5L (O1) | 0.1 | 0.9 | 0.1000 | 0.9000 |

La diferencia de 0.0005 en 3L es por la discretización del grid (501 puntos), irrelevante en la práctica.

### IMPORTANTE: Consistencia entre plots y valores reportados

Los gráficos de funciones de membresía de salida (`FUZZY/plots/03_fuzzy_output_w_set_*.png`) muestran el **dominio normalizado [0, 1]**. Esto es correcto porque:

1. Las MFs de salida están **definidas** en el universo normalizado [0, 1]
2. El rescalado ocurre **después** de la defuzzificación, no cambia la forma de las MFs
3. Los gráficos muestran la **definición del FIS**, no el resultado escalado

Sin embargo, en el paper se reporta `w ∈ [0.1, 0.9]`. Para evitar confusión entre el eje X de los plots (0–1) y el rango reportado (0.1–0.9), el paper debe incluir una nota explicativa:

> *"Output membership functions are defined on a normalized universe [0, 1]. The defuzzified centroid is linearly rescaled to the effective range [wMin, wMax] = [0.1, 0.9] after inference. This rescaling compensates for centroid compression (the inherent property of COG defuzzification that prevents the output from reaching universe extremes), ensuring that the configured wMin and wMax are achieved exactly."*

### Diagrama del flujo de datos

```
Entradas (d, t)
    ↓
Fuzzificación (MFs de entrada en [0, 1])
    ↓
Inferencia Mamdani (min-firing, max-aggregation)
    ↓
Defuzzificación COG → w_norm ∈ [c_min, c_max] ⊂ [0, 1]
    ↓                                                        ← los plots muestran hasta aquí
Rescalado: w_norm → [0, 1] → [wMin, wMax]
    ↓                                                        ← el paper reporta desde aquí
w efectivo ∈ [0.1, 0.9]
```

---

## 2. Tipos de Funciones de Membresía

| Tipo de MF | Cambios necesarios |
|---|---|
| **Triangular** `tri(a, b, c)` | Ninguno (implementación actual) |
| **Trapezoidal** `trap(a, b, c, d)` | Cambiar `self.w_mf[label]` de 3 a 4 parámetros. Adaptar `_compute_centroid_bounds()` y el loop de inferencia en `compute_w()` para usar una función `trap()` |
| **Gaussiana** `gauss(center, sigma)` | Cambiar `self.w_mf[label]` a 2 parámetros. Crear función `gauss()`. Adaptar `_compute_centroid_bounds()` y `compute_w()` |
| **Sigmoidal** | Similar a gaussiana, pero con función `sigmoid()` |

### Puntos específicos a modificar por archivo

```
_compute_centroid_bounds():
    for label, (a, b, c) in self.w_mf.items():          # ← desempaqueta 3 params
        mf_vals = np.array([tri(val, a, b, c) ...)       # ← usa tri()

compute_w():
    for (d_lab, t_lab), out_lab in self.rules.items():
        a, b, c = self.w_mf[out_lab]                     # ← desempaqueta 3 params
        mf_out = np.array([tri(val, a, b, c) ...)        # ← usa tri()
```

### Recomendación para implementación futura
Abstraer la evaluación de MF en un método genérico:
```python
def _eval_mf(self, mf_params, x):
    """Evalúa MF según tipo. Adaptar cuando se agreguen gaussianas/trapezoidales."""
    if len(mf_params) == 3:
        return tri(x, *mf_params)
    elif len(mf_params) == 4:
        return trap(x, *mf_params)
    elif len(mf_params) == 2:
        return gauss(x, *mf_params)
```
Esto centralizaría el cambio en un solo lugar en vez de modificar `_compute_centroid_bounds()` y `compute_w()` por separado.

## 2. Discretización del grid de salida

El `n_grid=501` puntos en `self.y = np.linspace(0, 1, 501)` causa una diferencia de ~0.0005 en el rescalado de 3L (sweep min=0.1005 vs exacto 0.1). Aumentar a `n_grid=1001` reduciría el error a ~0.0001 si se necesita mayor precisión, pero no es relevante para la práctica experimental.
