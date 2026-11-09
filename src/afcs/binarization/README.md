# Binarization

Transformación de representaciones continuas a discretas: funciones de
transferencia, reglas de discretización y mecanismos de reparación. Debe ser un
factor experimental explícito para no confundir su efecto con el del selector
semántico.

Estado: fuera del alcance activo v2; no hay una API operativa de binarización.
La fuente histórica de transferencias y reglas está como referencia pasiva en
[ARCHIVE](../../../ARCHIVE/binarization/README.md), no como módulo importable.
`Discretization/`, el solver/población SCP antiguos y el runner `2_main.py`
se retiraron coordinadamente. La reparación de problemas combinatorios se
conserva en las fuentes pasivas SCP/USCP
[archivadas con sus instancias](../../../ARCHIVE/problems/set_cover/README.md).
La base antigua y sus consumidores se retiraron antes del traslado;
`Problem/` ya no existe y no se añadieron imports desde ARCHIVE.

Una integración futura requerirá reabrir el alcance discreto y validar
fórmulas, RNG explícito y contratos propios; no restaurar esos conectores.
