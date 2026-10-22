# Experimentos

Este módulo coordina la ejecución sin incorporar fórmulas de optimización,
control difuso ni acceso SQL dentro de los algoritmos.

## Estado operativo

`ExperimentRunExecutor` conecta una réplica ya planificada con un optimizador
ya configurado:

1. cambia la réplica de `planned` a `running`;
2. ejecuta `optimizer.run()`;
3. valida objetivo, NFE y solución final;
4. persiste el resultado y marca la réplica como `completed`;
5. ante una excepción, guarda tipo y mensaje, marca `failed` y vuelve a lanzar
   la excepción para que no pase inadvertida.

El contrato `RunnableOptimizer` es neutral respecto de la metaheurística. El
PSO v2 ya lo satisface estructuralmente; GA y otras MH podrán hacerlo sin que el
runner conozca sus operadores internos.

## Límites deliberados

- El runner no construye el optimizador ni genera aleatoriedad.
- No crea, deriva ni asigna semillas. Recibe un optimizador cuyo RNG ya fue
  proporcionado por el nivel de planificación.
- No reconstruye trazas ni métricas que no fueron observadas durante la corrida.
- Todavía no valida automáticamente que problema, algoritmo y presupuesto del
  objeto coincidan con los registros planificados; esa vinculación pertenecerá
  al futuro constructor validado de planes de ejecución.
- Todavía no ejecuta campañas completas ni aplica reanudación o paralelismo.

`runtime_total_seconds` mide provisionalmente el intervalo monotónico ocupado
por `optimizer.run()`. Las escrituras SQLite quedan fuera de ese intervalo para
no mezclar rendimiento algorítmico con I/O. Antes de campañas definitivas se
deberán añadir tiempos separados para evaluación, optimizador, métricas,
controlador, persistencia y tiempo de pared completo, según la arquitectura
aprobada.
