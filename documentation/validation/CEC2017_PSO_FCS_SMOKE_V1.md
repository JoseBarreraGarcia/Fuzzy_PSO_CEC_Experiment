# Validación técnica CEC2017–PSO–FCS v1

**Fecha:** 2026-10-23

**Configuración:** `config/campaigns/cec2017_pso_fcs_validation_smoke.json`

**Base regenerable:** `Resultados/transitorio/cec2017_pso_fcs_validation_smoke_v1.db`

**Procedencia registrada:** `8b1c62763460+dirty-fcs-validation`

## Alcance

Esta ejecución comprueba integración y persistencia. No es un piloto, no estima
desempeño y sus resultados no deben incorporarse al artículo. Se ejecutaron:

- CEC2017 F1 y F21, dimensión 10;
- tres réplicas pareadas, semillas 42, 43 y 44;
- PSO fijo `w=0.7` como control técnico;
- PSO-FCS triangular R1, granularidad 3 y overlap 0/50/100 %;
- inferencia `dense_v1` y `sparse_v1`;
- población 10, 20 iteraciones y 210 evaluaciones por corrida.

Total: 42 corridas y 8.820 evaluaciones de función objetivo.

## Resultado observado

- 42 corridas completadas; cero fallidas, pendientes o `running`;
- cada corrida terminó con exactamente 210 evaluaciones;
- cada semilla aparece 14 veces, una por cada par problema–tratamiento;
- 882 checkpoints y 20.946 valores de traza persistidos;
- 252 métricas de réplica persistidas;
- 18 pares dense/sparse completos y cero diferencias exactas en objetivo final
  o solución final bajo idéntica función, réplica y overlap;
- 24 eventos de frontera, cero fallbacks y cero inferencias sin activación.

Los conteos acumulados confirmaron la separación esperada: cada tratamiento
denso evaluó 1.080 reglas y omitió cero; los tratamientos dispersos omitieron
960 reglas con overlap 0 %, 817 con 50 % y 636 con 100 %. Estos valores solo
describen esta validación pequeña y no prueban una ventaja temporal.

## Conclusión y límites

El recorrido completo `configuración → planificación → PSO/FCS → trazas →
SQLite` quedó operativo para los casos probados. La igualdad exacta observada
entre dense/sparse concuerda con las regresiones unitarias, pero no reemplaza el
microbenchmark con repeticiones y entorno controlado.

La base se encuentra bajo `Resultados/`, está ignorada por Git y puede
regenerarse desde la configuración. Como el árbol contenía cambios sin commit,
la procedencia se marcó deliberadamente como `+dirty`; una campaña científica
debe ejecutarse desde un commit limpio e identificado.
