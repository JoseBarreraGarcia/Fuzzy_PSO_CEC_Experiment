# Manuscript — MDPI Mathematics

Modular LaTeX sources for the paper *"Joint Sensitivity of Fuzzy-PSO Inertia Control to Linguistic Granularity and Rule-Base Structure: A Factorial Study on F1--F23"*.

## Layout

- `main.tex` — compilation entry point. Preamble + `\input{sections/*.tex}`.
- `sections/` — one `.tex` per section (Introduction, Related Work, Framework, Experimental Design, Results, Discussion, Conclusion).
- `figures/` — PNG/PDF/EPS figures referenced with `\includegraphics{figures/<name>}`.
- `tables/` — standalone `.tex` fragments included with `\input{tables/<name>.tex}`.
- `refs.bib` — BibTeX bibliography (cited from `main.tex` via `\bibliography{refs}`).
- `Definitions/` — MDPI class file (`mdpi.cls`), bibliography styles, logos. Do not edit.
- [Archived MDPI template](../archive/editorial_material_sources_20261015/template.tex) — reference material only, not a compilation input. `template_MDPI.tex` remains in this directory as a separate reference copy.

## Build

From this directory:

```powershell
pdflatex main
bibtex   main
pdflatex main
pdflatex main
```

Or with `latexmk -pdf main.tex`.

## Editorial guidance

The single source of editorial and scientific-writing standards is [EDITORIAL_BEST_PRACTICES.md](../EDITORIAL_BEST_PRACTICES.md). Use it for future drafting and revisions; this README is limited to manuscript layout and build instructions.

Superseded plans, proposed prose and editorial task briefs are preserved in the
[historical source archive](../archive/editorial_material_sources_20261015/README.md).
They are not additional active editing instructions. Technical incident states
are maintained in [Errores_de_implementacion.md](../Errores_de_implementacion.md).

