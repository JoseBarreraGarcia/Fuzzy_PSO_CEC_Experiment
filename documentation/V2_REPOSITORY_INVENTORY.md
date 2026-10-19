# Inventario inicial del repositorio para v2

**Fecha:** 19 de octubre de 2026  
**Rama:** `Solver_CEC_Fuzzy_PSO_v2`  
**Base:** `f8649134362f9a7b5e04f2f2bf032eb4b5938172`

## 1. Línea base

| Métrica | Valor |
|---|---:|
| Archivos versionados | 1.379 |
| Tamaño aproximado versionado | 662,64 MB |
| Entradas ignoradas detectadas | 197 |
| Pruebas descubiertas | 12 |
| Pruebas aprobadas | 12 |
| Pruebas fallidas | 0 |

Comando usado para la línea base:

```powershell
python -m unittest discover -s tests -v
```

Advertencias observadas, sin fallo de pruebas:

- `opfunu` utiliza `pkg_resources`, API marcada como obsoleta.
- La función clásica F14 todavía usa `numpy.matrix`, clase pendiente de
  deprecación.

## 2. Distribución de archivos versionados

| Área | Archivos |
|---|---:|
| `FUZZY/` | 968 |
| `Problem/` | 159 |
| `Graficos_Benchmark/` | 109 |
| `Metaheuristics/` | 42 |
| `analysis_modules_cec/` | 16 |
| `documentation/` | 14 antes de este inventario |
| `config/` | 10 |
| `Util/` | 10 |
| `Diversity/` | 9 |
| `analysis_modules/` | 7 |
| Resto | 35 |

La concentración en `FUZZY/` no representa solamente código: incluye material
del artículo, archivos históricos, figuras, resultados y literatura.

## 3. Archivos versionados mayores de 10 MB

| Tamaño | Archivo o grupo |
|---:|---|
| 35,49 MB | Archivo ZIP suplementario histórico |
| 25,59 MB | Segundo ZIP suplementario histórico |
| 23,47 MB | `Problem/Benchmark/CEC/cec2017/data.pkl` |
| 16,99 MB | `consolidated_level1.csv`, repetido en varios intentos |
| 14,16 MB | `landscape_slices_values.csv`, repetido en cuatro ubicaciones |
| 13,62 MB | Dataset parcial del primer intento |
| 11,31–11,32 MB | Dos versiones PDF del manuscrito |
| 10,77 MB | PDF suplementario retirado |

`data.pkl` es un dato funcional de CEC2017 y debe conservarse mientras no exista
un mecanismo alternativo validado. Los restantes elementos son candidatos a
permanecer exclusivamente en la rama MDPI o en almacenamiento de artefactos.

## 4. Duplicados grandes confirmados por SHA-256

### Grupo A — 56,64 MB totales

Cuatro copias idénticas de `landscape_slices_values.csv`, 14,16 MB cada una:

- exportación histórica;
- dos paquetes suplementarios archivados;
- suplemento actual del manuscrito.

SHA-256:
`066B05FAFA36161F178C1D6C998B1D878D9FD756832AB751A94E6A3682130981`

### Grupo B — 16,72 MB totales

Dos copias idénticas de `convergence_representative.csv`, 8,36 MB cada una.

SHA-256:
`A2303249ACBEAD2856D932152DC2BEC2C1B7246332858722DE06FEB82F8FE728`

### Grupo C — 84,95 MB totales

Cinco copias idénticas de `consolidated_level1.csv`, 16,99 MB cada una, entre el
dataset final y los intentos parciales 2–5.

SHA-256:
`418FBDE637F223CAAAFCD426D31948AB098FFE4163ED455C9EC5D2C0BAAC806B`

Solo estos tres grupos representan aproximadamente 158 MB de duplicación
versionada. No se ha realizado todavía una búsqueda exhaustiva de duplicados
pequeños.

## 5. Clasificación preliminar

### Núcleo candidato

- `Problem/Benchmark/CEC/cec2017/`
- partes activas de `Problem/Benchmark/Problem.py`
- `Solver/`
- PSO y PSO_FCS dentro de `Metaheuristics/`
- controladores difusos activos dentro de `FUZZY/`
- dependencias de diversidad utilizadas por el solver
- `tests/`

### Análisis potencialmente reutilizable

- `analysis_modules/`
- `analysis_modules_cec/`
- scripts finales y no duplicados de análisis del artículo
- utilidades de nombres, tablas, estadísticas y gráficos que no dependan de
  rutas fijas del manuscrito

Cada script deberá demostrar que acepta entradas configurables y que produce
salidas fuera del árbol fuente antes de formar parte del núcleo v2.

### Específico del artículo

- `FUZZY/ARTICULO_MDPI/manuscript/`
- `FUZZY/ARTICULO_MDPI/archive/`
- `FUZZY/ARTICULO_MDPI/results/`
- versiones y suplementos fechados
- archivos editoriales y literatura en PDF

### Temporales o sospechosos

- `_tmp_inspect_iter.py`
- `tmp_verify_rules.py`
- `_fix_plot10.py`
- `_fix_plots_08_10.py`
- `tmp_plots_output.txt`
- `FUZZY/plots/tmp_plots_output.txt`
- `.vscode/settings.json`
- directorios `attempt*_partial`

No se eliminarán hasta verificar si contienen lógica que no fue integrada.

## 6. Riesgos detectados

1. Imports y rutas dependen de la disposición actual y del directorio de
   ejecución.
2. Código, resultados y manuscrito están mezclados.
3. Existen múltiples versiones de scripts de análisis sin una autoridad clara.
4. Los datasets parciales pueden confundirse con el dataset definitivo.
5. El repositorio tiene cientos de MB de artefactos históricos.
6. La configuración experimental utiliza cadenas y convenciones implícitas.
7. El sistema actual de semillas depende del ID del experimento.
8. La cobertura automática actual se concentra en CEC2017 y F14; no cubre el
   runner completo, SQLite, paralelismo ni PSO_FCS.

## 7. Propuesta inicial de limpieza, aún no ejecutada

1. Crear un README histórico en lugar de copiar el árbol MDPI a v2.
2. Retirar `archive/`, resultados parciales, PDFs y suplementos de la rama v2.
3. Conservar fixtures pequeños y hashes que permitan verificar análisis.
4. Revisar scripts temporales y absorber solamente lógica no integrada.
5. Consolidar scripts de análisis autorizados bajo una única ruta.
6. Reforzar `.gitignore` para resultados, figuras, bases y temporales.
7. Ejecutar pruebas después de cada grupo de eliminaciones.

## 8. Evidencia de recuperación

Todo el contenido de este inventario permanece disponible en:

- rama `Solver_CEC_Fuzzy_PSO_ARTICULO_MDPI`;
- commit `f8649134362f9a7b5e04f2f2bf032eb4b5938172`.

La limpieza de v2 no debe modificar ni forzar el historial de esa rama.
