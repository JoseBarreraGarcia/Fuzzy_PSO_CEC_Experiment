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

Las propiedades del verificador histórico se prueban ahora en
[test_fuzzy_v2.py](../../../tests/test_fuzzy_v2.py): geometría, cobertura,
semántica/reflexión de R1-R8 y superficies triangulares deterministas/acotadas
para granularidades 3/5/7/9 y overlap 0/50/100 %. No se asume que toda base de
reglas alcance los extremos ni se valida el controlador antiguo por esas
pruebas. Los seis scripts numerados de limpieza, lookup y diagnósticos
retirados no son herramientas v2.

La presentación vive fuera de este módulo matemático:
[afcs.analysis.write_fuzzy_diagnostics](../analysis/README.md) genera
membresías, matriz de reglas y respuesta normalizada con sus datos y hashes.
Usa este controlador canónico, no los generadores ni el JSON históricos.
