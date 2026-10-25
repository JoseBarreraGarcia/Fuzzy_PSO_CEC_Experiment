# Fuzzy

Lógica difusa pura: funciones de pertenencia, particiones, esquemas versionados,
bases de reglas, fuzzificación, inferencia Mamdani, agregación y
defuzzificación. No selecciona esquemas ni actualiza directamente una
metaheurística.

Debe validar cobertura, dominios, orden semántico, compatibilidad entre
granularidad y reglas, y política explícita cuando ninguna regla se activa.

Estado v2: `membership.py` implementa `triangular_v1` y `gaussian_v1`;
`mamdani.py` implementa las reglas R1-R8 y la inferencia min-max-centroide.
Ofrece `dense_v1`, que inspecciona las `G²` reglas, y `sparse_v1`, que recorre
solo combinaciones de antecedentes con membresía positiva. Ambas rutas informan
reglas evaluadas y omitidas y están cubiertas por regresiones de equivalencia
numérica; la comparación de rendimiento se reserva al microbenchmark.
El factorial principal aprobado utiliza triangulares con overlap compartido
0/50/100 %. Las gaussianas usan la convención geométrica ±2σ y quedan
disponibles para estudios posteriores. La adaptación de `w` pertenece a
`afcs.optimizers.pso.FuzzyInertiaPolicy`, no a este módulo matemático.
