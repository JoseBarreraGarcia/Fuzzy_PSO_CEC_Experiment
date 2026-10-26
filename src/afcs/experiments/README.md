# Experimentos

Este módulo coordina la ejecución sin incorporar fórmulas de optimización,
control difuso ni acceso SQL dentro de los algoritmos.

`CampaignPlanner` recibe definiciones tipadas ya resueltas, comprueba conflictos
y expande cada tratamiento al número solicitado de réplicas. La persistencia es
atómica: o se guarda la campaña completa o no se guarda ninguna de sus filas.
Esto reemplaza la lógica dispersa de expansión, no los archivos de `config/`
que constituyen la interfaz humana mediante el esquema de campañas v1.

## Estado operativo

`ExperimentRunExecutor` conecta una réplica ya planificada con un optimizador
ya configurado:

1. crea un intento auditable y cambia la réplica de `planned` a `running`;
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
- El planificador asigna `base_seed + replica_index`; el constructor del
  optimizador recibe `ReplicaRandomStreams` creado desde esa semilla.
- El runner contrasta semilla y motor RNG con SQLite antes de ejecutar.
- No reconstruye trazas ni métricas que no fueron observadas durante la corrida.
- La versión del optimizador se persiste y valida antes de cada ejecución.
- El orquestador ejecuta campañas secuenciales o en procesos aislados y reanuda
  filas `planned`. Cada trabajador reconstruye la réplica desde SQLite.
- Las interrupciones en `running` requieren `recover` explícito, que conserva
  intentos auditables y reencola la misma réplica.
- El lector estricto transforma campañas JSON válidas en definiciones tipadas.
- El número de trabajadores no interviene en la derivación de semillas. La
  equivalencia de resultados y trazas con uno y dos procesos está probada.
- Las fábricas o ejecutores personalizados inyectados se limitan al modo
  secuencial hasta definir un contrato explícito de construcción por proceso.

`runtime_total_seconds` mide el intervalo monotónico inclusivo ocupado por
`optimizer.run()`. El perfil `timing` añade tiempos separados para evaluación
del problema, métricas, controlador, persistencia y pared total. Los componentes
incluidos no se suman entre sí; NFE sigue siendo el eje principal para comparar
calidad de búsqueda y los tiempos caracterizan costo computacional.
