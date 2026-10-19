# Estado operativo de CEC 2017

Fecha de validaciÃ³n: 19 de octubre de 2026.

## Cambios aplicados

- F21-F30 normalizan los pesos de composiciÃ³n sin formar `inf/inf` en los
  centros de desplazamiento. Si coincidieran varios centros, el peso se reparte
  uniformemente entre ellos.
- F2 se conserva en el paquete original para trazabilidad, pero se excluye de
  bases nuevas y el despachador experimental la rechaza.
- El despachador acepta D10, D30, D50 y D100 y rechaza dimensiones, entradas o
  resultados no finitos con errores explÃ­citos.
- `tests/test_cec2017.py` cubre centros exactos, perturbaciones alrededor de los
  centros, finitud, determinismo y validaciÃ³n del despachador.

F9 no se modificÃ³: el valor distinto del bias al evaluar el vector de
desplazamiento es coherente con la formulaciÃ³n Levy del cÃ³digo CEC de
referencia, cuyo mÃ­nimo interno estÃ¡ en uno y no en cero.

## CampaÃ±a preparada

`config/experiments_cec2017.json` configura F1/F3-F30, D30 y D50, 31 rÃ©plicas,
PSO y PSO_FCS. El presupuesto configurado es de 500 iteraciones con 20
partÃ­culas: 10020 evaluaciones contando la poblaciÃ³n inicial. Esto usa las
funciones CEC 2017, pero no afirma reproducir el presupuesto oficial de la
competiciÃ³n.

```powershell
$env:PSO_EXPERIMENTS_CONFIG = "config/experiments_cec2017.json"
python 0_0_reiniciar.py
python 1_0_poblarDB.py
python -m unittest discover -s tests -v
python 2_main.py
```

La comparaciÃ³n directa con `opfunu` no sirve como orÃ¡culo punto a punto en este
repositorio: esa biblioteca usa otra numeraciÃ³n tras retirar F2 y archivos de
desplazamiento/rotaciÃ³n que no son idÃ©nticos. Antes de publicar resultados se
deben congelar los hashes de `data.pkl` y del cÃ³digo de esta carpeta.

SHA-256 de `data.pkl` validado en esta revisiÃ³n:
`5F978EC6620E659EA933E21C4C4398B47B811467D3EED3DCB204566C3965924B`.
