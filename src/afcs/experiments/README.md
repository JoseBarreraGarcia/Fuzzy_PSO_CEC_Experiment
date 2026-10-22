# Experimentos

Este módulo coordina la ejecución sin incorporar fórmulas de optimización,
control difuso ni acceso SQL dentro de los algoritmos.

`CampaignPlanner` recibe definiciones tipadas ya resueltas, comprueba conflictos
y expande cada tratamiento al número solicitado de réplicas. La persistencia es
atómica: o se guarda la campaña completa o no se guarda ninguna de sus filas.
Esto reemplaza la lógica dispersa de expansión, no los archivos de `config/`
que seguirán siendo la interfaz humana cuando exista su esquema v2.

## Estado operativo

`ExperimentRunExecutor` conecta una réplica ya planificada con un optimizador
ya configurado:

1. cambia la réplica de `planned` a `running`;
2. antes del cambio de estado, compara el ejecutable con el plan persistido;
3. ejecuta `optimizer.run()`;
4. valida objetivo, NFE y solución final;
5. persiste el resultado y marca la réplica como `completed`;
6. ante una excepción, guarda tipo y mensaje, marca `failed` y vuelve a lanzar
   la excepción para que no pase inadvertida.

La validación previa exige coincidencia de algoritmo, familia e identidad del
problema, dimensión, dirección, óptimo conocido, parámetros, hash de datos,
población y presupuestos declarados. Una discrepancia produce `RunBindingError`
y deja la réplica en `planned`, pues todavía no comenzó una ejecución válida.

El contrato `RunnableOptimizer` es neutral respecto de la metaheurística. El
PSO v2 ya lo satisface estructuralmente; GA y otras MH podrán hacerlo sin que el
runner conozca sus operadores internos.

## Límites deliberados

- El runner no construye el optimizador ni genera aleatoriedad.
- No crea, deriva ni asigna semillas. Recibe un optimizador cuyo RNG ya fue
  proporcionado por el nivel de planificación.
- No reconstruye trazas ni métricas que no fueron observadas durante la corrida.
- La versión del optimizador está presente en sus metadatos, pero el esquema
  SQLite v1 todavía no tiene una columna dedicada para validarla y persistirla.
- Todavía no ejecuta campañas completas ni aplica reanudación o paralelismo.
- Todavía no existe el lector que transforme `config/*.json` en las definiciones
  tipadas del planificador.

`runtime_total_seconds` mide provisionalmente el intervalo monotónico ocupado
por `optimizer.run()`. Las escrituras SQLite quedan fuera de ese intervalo para
no mezclar rendimiento algorítmico con I/O. Antes de campañas definitivas se
deberán añadir tiempos separados para evaluación, optimizador, métricas,
controlador, persistencia y tiempo de pared completo, según la arquitectura
aprobada.
