# Manuscript — MDPI Biomimetics

Modular LaTeX sources for the paper *"Joint Sensitivity of Fuzzy-PSO Inertia Control to Linguistic Granularity and Rule-Base Structure: A Factorial Study on F1--F23"*.

## Layout

- `main.tex` — compilation entry point. Preamble + `\input{sections/*.tex}`.
- `sections/` — one `.tex` per section (Introduction, Related Work, Framework, Experimental Design, Results, Discussion, Conclusion).
- `figures/` — PNG/PDF/EPS figures referenced with `\includegraphics{figures/<name>}`.
- `tables/` — standalone `.tex` fragments included with `\input{tables/<name>.tex}`.
- `refs.bib` — BibTeX bibliography (cited from `main.tex` via `\bibliography{refs}`).
- `Definitions/` — MDPI class file (`mdpi.cls`), bibliography styles, logos. Do not edit.
- `template.tex` — pristine MDPI reference template; kept for lookup only.

## Build

From this directory:

```powershell
pdflatex main
bibtex   main
pdflatex main
pdflatex main
```

Or with `latexmk -pdf main.tex`.
