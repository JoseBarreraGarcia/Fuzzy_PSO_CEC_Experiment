# Selectors

Nivel superior de adaptación semántica. Selecciona un esquema a partir de
métricas, historial, esquema anterior, estado interno y RNG.

Familias previstas: fijo, reglas deterministas, estocástico, Q-learning e
hiperheurística. Toda decisión debe registrar esquema, razón, versión de
política, probabilidad/puntuación cuando aplique y evento de cambio.

Estado: planificado; no hay selector dinámico autoritativo todavía.
