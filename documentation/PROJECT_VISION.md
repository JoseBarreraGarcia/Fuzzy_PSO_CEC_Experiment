# Visión científica y técnica del proyecto AFCS

## Propósito

La versión 2 debe convertirse en la plataforma experimental de la tesis
doctoral *An Adaptive Fuzzy Control System for Metaheuristic Configuration
through Dynamic Selection of Fuzzy Schemes*.

El objetivo científico no es únicamente adaptar numéricamente un parámetro de
PSO. El sistema propuesto tiene dos niveles:

1. **Adaptación de parámetros:** un FIS Mamdani produce un parámetro operativo,
   inicialmente el peso de inercia `w` en PSO y posteriormente la tasa de
   mutación en GA.
2. **Adaptación semántica:** un selector de nivel superior escoge durante la
   ejecución un esquema difuso completo que modifica la interpretación de las
   métricas de búsqueda.

La secuencia causal que debe preservar el software es:

```text
estado observable
  → métricas online
  → selección de esquema
  → fuzzificación e inferencia Mamdani
  → mapeo del parámetro
  → paso de la metaheurística
  → evaluación
  → nuevo estado y registro
```

No se puede utilizar información futura para seleccionar el esquema del paso
actual.

## Principios de arquitectura

- Cada responsabilidad tiene una ubicación única y reconocible.
- Problemas, optimizadores, métricas, lógica difusa, selectores y persistencia
  son módulos intercambiables.
- El controlador se integra en la etapa de adaptación de parámetros sin
  reescribir los operadores internos del optimizador.
- Las configuraciones científicas se versionan y se identifican mediante hash.
- Las métricas observadas, reconstruidas y esperadas nunca se confunden.
- El presupuesto principal se expresa mediante evaluaciones, aunque también se
  registran iteraciones y tiempo.
- Los cambios metodológicos se documentan y se consultan antes de codificarse.
- Las extensiones discretas deben separar el efecto del selector semántico del
  efecto de binarización, reparación y representación.

## Capacidades científicas previstas

### Métricas online del proceso

La propuesta doctoral identifica inicialmente:

- diversidad;
- velocidad de convergencia;
- tasa de mejora;
- estancamiento;
- progreso o índice de iteración.

No se asume que todas deban entrar simultáneamente al primer controlador. La
selección de entradas es parte del diseño experimental y de sus ablaciones.

### Esquemas difusos

La biblioteca deberá representar explícitamente:

- tipo y parámetros de funciones de pertenencia;
- cardinalidad o granularidad;
- cobertura, normalidad, orden y solapamiento;
- etiquetas semánticas;
- compatibilidad con la base de reglas;
- versión, procedencia y hash.

Cambiar de tres a cinco etiquetas no permite reutilizar silenciosamente una
matriz de reglas incompatible.

### Selectores semánticos

Se contemplan módulos separados para:

- esquema fijo;
- switching determinista basado en reglas;
- selección estocástica;
- Q-learning;
- hiperheurísticas.

Los métodos aprendidos deberán separar entrenamiento, validación y prueba, y
evitar cualquier fuga desde el conjunto final de evaluación.

### Optimizadores y problemas

El desarrollo comienza con PSO continuo y FIS estático reproducible. Después
se incorporarán selección semántica, GA y dominios discretos. Los problemas
previstos incluyen CEC, benchmarks clásicos, SCP, USCP, KP y selección de
características.

El control de parámetros es opcional. La plataforma debe ejecutar tanto
metaheurísticas sin control externo como tratamientos con parámetros fijos,
calendarios, adaptación basada en estado, control difuso o variantes
adaptativas completas. Configuración inicial y adaptación dinámica se modelan
y registran por separado.

La especificación se mantiene en
`documentation/architecture/OPTIMIZER_PARAMETER_CONTROL.md`.

## Métricas futuras que deben tener un hogar definido

Además de las métricas ya registradas, la arquitectura reserva responsabilidades
para:

- mejora absoluta y relativa;
- contador y razón de estancamiento;
- velocidad de convergencia por ventana;
- éxito y NFE hasta objetivo con censura explícita;
- coste del evaluador, optimizador, controlador y selector;
- esquema activo, evento de cambio y razón de selección;
- permanencia, ocupación y matriz de transiciones de esquemas;
- entropía de uso de esquemas;
- recompensa y versión de estado del selector;
- métricas de validez e interpretabilidad de particiones difusas;
- factibilidad, violación y efecto de reparación;
- estabilidad, dispersión, IQR y tamaños de efecto.

Las fórmulas que todavía están abiertas no se implementarán como definitivas.

## Orden de implementación

1. Núcleo experimental, PSO continuo, NFE y persistencia reproducible.
2. FIS Mamdani estático validado.
3. Biblioteca versionada de esquemas semánticos.
4. Selectores fijo, determinista y estocástico.
5. Q-learning e hiperheurística con protocolo train/test.
6. GA.
7. SCP, USCP, KP y selección de características con ablaciones discretas.
8. Evaluación estadística y publicación de artefactos sellados.

## Autoridad de las decisiones

En caso de discrepancia se aplicará este orden:

1. propuesta doctoral explícita;
2. implementación o publicación confirmada que se desea reproducir;
3. decisión aprobada por el investigador;
4. especificación técnica documentada;
5. propuesta provisional de implementación.

Fuentes incorporadas al repositorio:

- `Tesis/CONTEXTO_TESIS_DOCTORAL_CODEX.md`;
- `Tesis/Informe_Proyecto_de_Tesis.pdf`.
