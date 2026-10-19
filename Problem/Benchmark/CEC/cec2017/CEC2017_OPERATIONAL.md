# Estado operativo de CEC 2017

Fecha de validación: 19 de octubre de 2026.

## Ubicación autoritativa

La implementación ejecutable v2 se encuentra en:

`src/afcs/problems/benchmarks/cec2017/`

Esta carpeta histórica conserva el diagnóstico, un ejemplo y material de
trazabilidad de la transición MDPI → v2. Los consumidores internos ya importan
desde `afcs.problems.benchmarks.cec2017`.

## Condiciones operativas validadas

- F21–F30 normalizan los pesos de composición sin formar `inf/inf` en los
  centros de desplazamiento. Si coinciden varios centros, el peso se reparte
  uniformemente entre ellos.
- F2 se conserva dentro del código fuente original por trazabilidad, pero está
  excluida del catálogo experimental y el adaptador v2 la rechaza.
- Se admiten D10, D30, D50 y D100 para campañas.
- Dimensiones incorrectas, entradas no finitas y resultados no finitos producen
  errores explícitos.
- El adaptador `CEC2017Problem` declara identidad, dominio, dirección de
  optimización, óptimo conocido y procedencia del dataset.
- Las pruebas cubren centros exactos, perturbaciones cercanas, finitud,
  determinismo y equivalencia entre el adaptador y las funciones vectorizadas.

F9 no fue modificada: el valor distinto del bias al evaluar directamente el
vector de desplazamiento es coherente con la formulación Levy del código de
referencia, cuyo mínimo interno está en uno y no en cero.

## Dataset funcional

El archivo requerido está empaquetado en:

`src/afcs/problems/benchmarks/cec2017/data.pkl`

SHA-256 validado:

`5F978EC6620E659EA933E21C4C4398B47B811467D3EED3DCB204566C3965924B`

El wheel de `afcs` incluye tanto `data.pkl` como `LICENSE.txt`.

## Configuración histórica preparada

`config/experiments_cec2017.json` configura F1/F3–F30, D30 y D50, 31
réplicas, PSO y PSO_FCS. El presupuesto configurado es de 500 iteraciones con
20 partículas: 10020 evaluaciones contando la población inicial. Esto utiliza
las funciones CEC 2017, pero no afirma reproducir el presupuesto oficial de la
competición.

La comparación directa con `opfunu` no constituye un oráculo punto a punto
para esta implementación: dicha biblioteca usa otra numeración tras retirar F2
y otros archivos de desplazamiento y rotación.
