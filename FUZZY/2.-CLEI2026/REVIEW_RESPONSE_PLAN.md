# Plan de Mejoras — Camera-Ready CLEI 2026 (Paper #66)

**Título:** Impact of Input Membership Function Design on Fuzzy-Adaptive Particle Swarm Optimization: An Empirical Sensitivity Analysis
**Estado:** Aceptado como full paper (34% acceptance rate)
**Deadline camera-ready:** 21 de junio de 2026
**Restricción de formato:** IEEE Conference Proceedings, doble columna, **máximo 10 páginas** (incluye figuras, referencias y apéndices)

---

## 1. Resumen de Comentarios de Revisores

### Reviewer 1 (Overall: positivo, novedad moderada)

| # | Comentario | Impacto | Tipo |
|---|---|---|---|
| R1.0 | Secciones de metodología muy detalladas (tablas MF, configuraciones) | Medio | Redacción |
| R1.1 | No articula claramente la contribución científica ni su generalización | Alto | Contenido |
| R1.2 | Solo 6 benchmarks con dimensionalidad modesta | Alto | Experimental |
| R1.3 | Solo MFs triangulares (ya reconocido como limitación) | Medio | Limitación |
| R1.4 | Overhead reportado, pero no discute escalabilidad | Medio | Discusión |
| R1.5 | Mejoras en F22/F23 no son estadísticamente significativas → no sobrevender | Alto | Análisis |
| R1.6 | Solo $w$ adaptada — $c_1, c_2$ fijos | Bajo | Scope |
| R1.7 | Explicación 3L > 5L es especulativa — falta análisis de activación de reglas | Medio | Análisis |

### Reviewer 2 (Overall: tema interesante, varios puntos metodológicos)

| # | Comentario | Impacto | Tipo |
|---|---|---|---|
| R2.1 | Literatura desactualizada (solo 2 refs 2023-2026) | Alto | Referencias |
| R2.2 | Ec. 4 (defuzzification) — describir todos los elementos | Medio | Redacción |
| R2.3 | Figura 1 (arquitectura) → preferir pseudocódigo para reproducibilidad | Medio | Metodología |
| R2.4 | Faltan gráficas de convergencia (comportamiento online) | Alto | Experimental |
| R2.5 | Comparar contra state-of-the-art, no solo baseline | Alto | Experimental |
| R2.6 | Usar Wilcoxon **rank-sum**, no signed-rank | Alto | Estadístico |
| R2.7 | No se prueban diferentes dimensionalidades | Alto | Experimental |

---

## 2. Plan de Mejoras (Bloques A, B, C)

### Bloque A — Correcciones de texto (sin nuevos experimentos) ✅ COMPLETO

Cabe íntegramente en el límite de 10 páginas.

| ID | Acción | Sección afectada | Reviewer | Estado |
|---|---|---|---|---|
| **A1** | Justificación de Wilcoxon signed-rank por seeding pareado + reporte adicional de rank-sum en Tabla 1 | §IV-A, Tabla `tab:pso_vs_fcs` | R2.6 | ✅ Hecho. Tests recalculados con `BD/resultados_clei2026_backup.db` confirman valores. Hallazgo: en F21 y F22 los tests divergen, lo que se discute como información complementaria. |
| **A2** | Descripción completa de Ec. 4: variable $z \in Z=[0,1]$, $\mu_{\text{agg}}$ via max, mapeo afín | §III-B | R2.2 | ✅ Hecho |
| **A3** | Reformular contribución científica + generalización + guías prácticas | §I | R1.1 | ✅ Hecho |
| **A4** | Discutir cuidadosamente la no-significancia en F22/F23 | §IV-A | R1.5 | ✅ Cubierto por A1 (discusión multimodal reescrita) |
| **A5** | Añadir refs 2023-2026 sobre fuzzy-PSO | §II-A, bibliography | R2.1 | ✅ Hecho: morales2023stagnation, wang2023hierarchical, li2025rapso, derrac2011practical |
| **A6** | Fusionar Tablas 1-2 (parámetros MF 3L y 5L) en una sola | §III-C | R1.0 | ✅ Hecho |
| **A7** | Añadir párrafo sobre escalabilidad del overhead (O(1) por iter, independiente de $d$) | §IV-A | R1.4 | ✅ Hecho |
| **A8** | Reforzar limitación de adaptar solo $w$ en Conclusiones, con refs | §V | R1.6 | ✅ Hecho |

**Nota sobre páginas:** Compilación local da 11 páginas por figuras locales faltantes (carpeta `figures/` no presente). En Overleaf, con las figuras reales, el documento se mantiene en 10 páginas.

### Bloque B — Análisis adicional con datos existentes

Datos de iteraciones ya almacenados en la BD (tabla `iteraciones` con CSV de w, diversity, fitness). No requiere re-ejecutar experimentos.

| ID | Acción | Sección | Reviewer |
|---|---|---|---|
| **B1** | Análisis de frecuencia de activación de reglas (I1 vs I3, 3L vs 5L) | Nuevo §IV-D o anexo a §IV-C | R1.7 |
| **B2** | Curvas de convergencia (fitness vs. iteración) al menos para F21-F23 | Nueva figura en §IV-A | R2.4 |
| **B3** | Pseudocódigo del FCS-PSO (algorithm environment) | §III-B | R2.3 |

**Costo de páginas:** +1 a +1.5 página (1 figura nueva, 1 algoritmo, 1 subsección breve).

### Bloque C — Mejoras experimentales (requieren nuevos runs)

| ID | Acción | Esfuerzo | Reviewer |
|---|---|---|---|
| **C1** | Evaluar dimensionalidades adicionales (d=30, d=50) en F1, F5, F11 | ~2-3 días pipeline | R1.2, R2.7 |
| **C2** | Comparación contra SOTA (Nickabadi feedback PSO, JADE, o CMA-ES) | ~1 semana | R2.5 |

**Costo de páginas:** +0.5 a +1.5 página dependiendo del nivel de detalle.

---

## 3. Estrategia para Camera-Ready (3 semanas hasta 21 jun)

### Semana 1 — Bloque A completo
- **Días 1-2:** A1, A2, A4 (correcciones críticas)
- **Días 3-5:** A3, A5 (contribución + literatura)
- **Días 6-7:** A6, A7, A8 (ajustes finales de texto)

### Semana 2 — Bloque B
- **Días 8-9:** B3 (pseudocódigo)
- **Días 10-12:** B2 (curvas de convergencia con datos existentes)
- **Días 13-14:** B1 (análisis de activación de reglas)

### Semana 3 — Bloque C (parcial) + revisión final
- **Días 15-17:** C1 si el espacio lo permite (d=30 y d=50)
- **Días 18-19:** Compilación, control de páginas, revisión de figuras
- **Días 20-21:** Lectura final, submission

### Decisiones a tomar
- **C2 (SOTA):** Probablemente diferir como future work si el espacio se ajusta. Justificar en §V que el scope del paper es sensibilidad a MF design, no comparación de algoritmos.
- **B1 vs C1:** Si hay que elegir, B1 (activación de reglas) refuerza la narrativa principal del paper; C1 amplía el alcance pero compite por páginas.

---

## 4. Gestión del Límite de 10 Páginas

### Estado actual estimado
El manuscrito actual ocupa probablemente ~9-10 páginas. Cualquier adición requiere compensación.

### Tácticas para liberar espacio
1. **A6:** Fusionar Tablas 1 y 2 (parámetros 3L y 5L) en una sola tabla con bloques separados → libera ~0.5 pág.
2. Reducir Tabla 3 (`tab:algorithm_configs`) — es redundante con el texto.
3. Consolidar las dos figuras de boxplot/scatter (`fig:pso_vs_fcs_boxplot` y `fig:scatter_fitness_std`) si transmiten información solapada.
4. Comprimir §III-D y §III-E (output set, rule base) — el rule base puede mostrarse solo para 3L en la versión final, con 5L en anexo o en repositorio.
5. Acortar Acknowledgments y descripciones de autores.

### Tácticas si falta espacio para B y C
- B1 y B2 pueden integrarse como subsección compacta sin nueva sección principal.
- C1 puede reportarse en una tabla resumen sin nuevas figuras.

---

## 5. Próximos Pasos Inmediatos

1. **Iniciar Bloque A** comenzando por A1 (decisión sobre test estadístico) y A2 (Ec. 4).
2. Verificar páginas actuales del PDF compilado antes de añadir contenido.
3. Buscar referencias 2023-2026 para A5.

---

*Documento generado el 31 de mayo de 2026 para apoyar la preparación de la versión camera-ready de CLEI 2026.*
