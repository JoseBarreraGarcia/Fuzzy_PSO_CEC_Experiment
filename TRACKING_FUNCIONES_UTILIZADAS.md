# TRACKING DE FUNCIONES BENCHMARK UTILIZADAS

## Funciones Configuradas

Según `Util/json/experiments_config.json` (línea 57):
```
"instancias": {
    "BEN": ["F1","F5","F11", "F21","F22", "F23"]
}
```

## UBICACIÓN EN EL CÓDIGO

Las funciones F1-F23 están definidas en **[BD/sqlite.py](BD/sqlite.py#L128)** línea 128:

```python
data = [
    'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10',
    'F11', 'F12', 'F13', 'F14', 'F15', 'F16', 'F17', 'F18', 'F19', 'F20',
    'F21', 'F22', 'F23',
    ...
]
```

## QUÉ FUNCIONES ESTÁS USANDO

| Código | Nombre Completo | Óptimo | Fuente |
|--------|-----------------|--------|--------|
| **F1** | **Sphere** | **0.0** | [Graficos_Benchmark/graficosBenchmark.py](Graficos_Benchmark/graficosBenchmark.py#L61) |
| **F5** | **Rosenbrock** | **0.0** | [Graficos_Benchmark/graficosBenchmark.py](Graficos_Benchmark/graficosBenchmark.py#L65) |
| **F11** | **Griewank** | **0.0** | [Graficos_Benchmark/graficosBenchmark.py](Graficos_Benchmark/graficosBenchmark.py#L72) |
| **F21** | **Shekel 5** | **-10.1532** | [BD/sqlite.py](BD/sqlite.py#L251) |
| **F22** | **Shekel 7** | **-10.4028** | [BD/sqlite.py](BD/sqlite.py#L255) |
| **F23** | **Shekel 10** | **-10.5363** | [BD/sqlite.py](BD/sqlite.py#L259) |

## RESOLUCIÓN DE LA CONFUSIÓN

**El problema:** Encontraste que `graficar_cec2017.py` define F1 como "Bent Cigar" que es INCORRECTO para tus experimentos.

**La realidad:** 
- **Tus funciones NO son CEC2017**
- Tus funciones son **funciones clásicas de benchmark** de la lista `data` en `BD/sqlite.py`
- El archivo `graficar_cec2017.py` está diseñado para funciones CEC2017 (con sufijo "CEC2017")
- El archivo correcto es **`Graficos_Benchmark/graficosBenchmark.py`** que define correctamente:
  - F1 = Sphere (óptimo = 0.0)
  - F5 = Rosenbrock (óptimo = 0.0)
  - F11 = Griewank (óptimo = 0.0)
  - F21 = Shekel 5 (óptimo = -10.1532)
  - F22 = Shekel 7 (óptimo = -10.4028)
  - F23 = Shekel 10 (óptimo = -10.5363)

## PARA REPORTAR EN TU PAPER/CONFE RENCIA

**Estás utilizando 6 funciones benchmark clásicas:**

1. **F1 - Sphere**: Función unimodal simple, óptimo en el origen (0,0,...,0)
2. **F5 - Rosenbrock**: Función unimodal compleja con valle estrecho
3. **F11 - Griewank**: Función multimodal con mínimos locales periódicos
4. **F21 - Shekel Foxholes (5 picos)**: Función de multimodalidad dura con 5 mínimos locales
5. **F22 - Shekel Foxholes (7 picos)**: Función de multimodalidad dura con 7 mínimos locales
6. **F23 - Shekel Foxholes (10 picos)**: Función de multimodalidad dura con 10 mínimos locales

**Rango de dificultad:** De unimodal simple (F1) a multimodal dura (F21-F23)

## ÓPTIMOS CORRECTOS A USAR

```
F1:  0.0
F5:  0.0
F11: 0.0
F21: -10.1532
F22: -10.4028
F23: -10.5363
```

Estos están correctamente definidos en [BD/sqlite.py](BD/sqlite.py#L240-L264) líneas 240-264.
