# Estado y pendientes — Artículo MDPI Mathematics

**Estado al 15 de octubre de 2026:** análisis y manuscrito finalizados para revisión de autor. El checklist detallado de fases y cambios está preservado en `archive/project_status_history_20261015/01_task_list_pre_final_20261015.md`; este archivo es la lista operativa vigente.

## Estado cerrado

- [x] Diseño ejecutado: PSO clásico + 32 configuraciones FCS, 62 instancias, 31 corridas por grupo y 63 426 registros.
- [x] F14 usa la función de Shekel Foxholes con pesos canónicos $1,\ldots,25$; el dataset consolidado contiene 1 023 resultados corregidos de F14.
- [x] Semillas únicas y presentes para las 63 426 corridas: `seed = 42 + historical_exp_id`. No se usan `run_id` como bloques comunes entre configuraciones.
- [x] RQ1–RQ5 reconciliadas con el dataset final. RQ3 se informa descriptivamente y no estima una interacción factorial.
- [x] RQ4: Mann–Whitney bilateral sobre muestras independientes, Bonferroni sobre 1 984 pruebas.
- [x] Tabla 11: Mann–Whitney bilateral independiente, Holm sobre una familia separada de 1 984 pruebas.
- [x] Runtime estimado con cocientes de medianas de grupos independientes, sin emparejar por `run_id`.
- [x] Manuscrito principal compilado a 62 páginas; Supplementary Information compilado a 43 páginas.
- [x] Paquete de entrega validado: `manuscript/Supplementary_Information_20261015.zip` contiene el run-level data, tablas y figuras finales.
- [x] Guía editorial canónica: `EDITORIAL_BEST_PRACTICES.md`. Fuentes previas archivadas en `archive/editorial_guidance_sources_20261015/`.
- [x] Materiales suplementarios obsoletos y assets no incluidos en el PDF archivados fuera de `manuscript`; las fuentes requeridas para compilar siguen activas.

## Pendientes de los autores

- [ ] Aprobar las asignaciones CRediT por autor.
- [ ] Decidir si se hará un depósito público independiente con DOI. El ZIP suplementario se entrega con el artículo, pero no constituye un repositorio público.
- [ ] Completar metadatos editoriales finales que requiera el envío.

## Restricciones de cierre

- No reejecutar PSO ni modificar la base de datos para la preparación editorial.
- No añadir un test de interacción a RQ3 ni presentar resultados de `run_id` como inferencia por semillas compartidas.
- Preservar la interpretación matemática de la Proposición 1 y la Sección 6.4, salvo solicitud/autorización explícita del autor.
- Para futuras ediciones, seguir `EDITORIAL_BEST_PRACTICES.md` y contrastar cada cifra con el paquete final.
