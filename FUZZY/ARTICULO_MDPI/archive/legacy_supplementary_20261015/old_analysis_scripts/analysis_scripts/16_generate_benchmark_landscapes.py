#!/usr/bin/env python
"""Generate honest 2-D slices of the 23 MDPI benchmark functions.

Domains and reference optima are read from BD/resultados.db; dimensions are read
from config/experiments_mdpi_full.json. For d>2, x1 and x2 span the true bounds
and all remaining coordinates are fixed at the midpoint of their bounds. Thus,
each page is explicitly a two-dimensional slice, not a rendering of the full
high-dimensional landscape. F7 is plotted as its exact expected objective,
quartic(x) + E[U(0,1)] = quartic(x) + 0.5.

Elevation and colour show log10(1 + max(f(x)-f*, 0)), a monotone compression of
the nonnegative objective gap that keeps functions with different scales
visually inspectable. The absolute landscape values remain available in the
per-function CSV output.

Outputs:
    manuscript/figures/supplementary/benchmark_landscape_slices.pdf (23 pages)
    manuscript/figures/supplementary/landscape_F1_F23.csv
    manuscript/figures/supplementary/landscape_F*.png (preview pages)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))
DB_PATH = REPO_ROOT / "BD" / "resultados.db"
CONFIG_PATH = REPO_ROOT / "config" / "experiments_mdpi_full.json"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "manuscript" / "figures" / "supplementary"
BODY_FIGURES = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "manuscript" / "figures" / "landscapes_body"
BODY_TEX = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "manuscript" / "figures" / "landscape_figures.tex"
SI_FIGURES = (REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "manuscript" / "Supplementary"
              / "SupplementaryData" / "figures")
SI_LANDSCAPE_TEX = (REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "manuscript"
                    / "Supplementary" / "SupplementaryData" / "landscape_figures.tex")
RESOLUTION = 70

FUNCTION_NAMES = {
    "F1": "Sphere", "F2": "Schwefel 2.22", "F3": "Schwefel 1.2",
    "F4": "Schwefel 2.21", "F5": "Rosenbrock", "F6": "Shifted step",
    "F7": "Quartic with noise", "F8": "Schwefel 2.26", "F9": "Rastrigin",
    "F10": "Ackley", "F11": "Griewank", "F12": "Penalized 1",
    "F13": "Penalized 2", "F14": "Shekel foxholes", "F15": "Kowalik",
    "F16": "Six-hump camel", "F17": "Branin", "F18": "Goldstein-Price",
    "F19": "Hartmann 3-D", "F20": "Hartmann 6-D", "F21": "Shekel-5",
    "F22": "Shekel-7", "F23": "Shekel-10",
}
FIXED_DIM = {f"F{i}": d for i, d in
             [(14, 2), (15, 4), (16, 2), (17, 2), (18, 2), (19, 3),
              (20, 6), (21, 4), (22, 4), (23, 4)]}


def load_benchmark_parameters() -> tuple[dict, dict]:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Benchmark parameter database missing: {DB_PATH}")
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT nombre, optimo, param FROM instancias "
            "WHERE tipo_problema=? ORDER BY nombre", ("BEN",)
        ).fetchall()
    params = {}
    for name, optimum, param in rows:
        if not re.fullmatch(r"F(?:[1-9]|1[0-9]|2[0-3])", name):
            continue
        match = re.search(r"lb:([^,]+),ub:([^,]+)", param)
        if not match:
            raise ValueError(f"Cannot parse solver bounds for {name}: {param}")
        params[name] = {"lb": float(match.group(1)), "ub": float(match.group(2)),
                        "optimum": float(optimum)}
    if set(params) != {f"F{i}" for i in range(1, 24)}:
        raise ValueError(f"Expected F1-F23 in database; found {len(params)} functions")

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    dimensions = config["dimensiones"]["BEN"]
    dims = {f: int(dimensions[f][0]) if f in dimensions else FIXED_DIM[f]
            for f in params}
    return params, dims


def evaluate_grid(function: str, dim: int, lb: float, ub: float,
                  optimum: float, resolution: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Import lazily so the script can validate configuration/paths before solver imports.
    from Problem.Benchmark.Problem import fitness

    axis = np.linspace(lb, ub, resolution)
    xx, yy = np.meshgrid(axis, axis)
    base = np.full(dim, (lb + ub) / 2.0, dtype=float)
    raw = np.empty_like(xx)
    if function == "F7":
        # Exact expectation removes random noise while preserving its mean landscape.
        weights = np.arange(1, dim + 1, dtype=float)
        for row in range(resolution):
            for col in range(resolution):
                point = base.copy()
                point[0], point[1] = xx[row, col], yy[row, col]
                raw[row, col] = np.sum(weights * point ** 4) + 0.5
        optimum_visual = optimum + 0.5
    else:
        for row in range(resolution):
            for col in range(resolution):
                point = base.copy()
                point[0], point[1] = xx[row, col], yy[row, col]
                raw[row, col] = float(np.asarray(fitness(function, point)).reshape(-1)[0])
        optimum_visual = optimum * dim if function == "F8" else optimum
    normalized_excess = np.maximum(raw - optimum_visual, 0.0)
    elevation = np.log10(1.0 + normalized_excess)
    return xx, yy, raw


def render_function(function: str, dim: int, params: dict, resolution: int):
    bound = params[function]
    xx, yy, raw = evaluate_grid(function, dim, bound["lb"], bound["ub"],
                                bound["optimum"], resolution)
    ref = bound["optimum"] * dim if function == "F8" else bound["optimum"]
    if function == "F7":
        ref += 0.5
    gap = np.maximum(raw - ref, 0.0)
    z = np.log10(1.0 + gap)

    fig = plt.figure(figsize=(10.2, 4.5), constrained_layout=True)
    ax2d = fig.add_subplot(1, 2, 1)
    levels = np.linspace(float(np.nanmin(z)), float(np.nanmax(z)), 36)
    contour = ax2d.contourf(xx, yy, z, levels=levels, cmap="viridis")
    ax2d.contour(xx, yy, z, levels=12, colors="white", alpha=0.35, linewidths=0.45)
    ax2d.set_xlabel("$x_1$")
    ax2d.set_ylabel("$x_2$")
    ax2d.text(0.025, 0.96, "(a)", transform=ax2d.transAxes, va="top",
              fontsize=9, fontweight="bold",
              bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"})
    fig.colorbar(contour, ax=ax2d, label="$\\log_{10}(1+\\max(f(x)-f^*,0))$")

    ax3d = fig.add_subplot(1, 2, 2, projection="3d")
    ax3d.plot_surface(xx, yy, z, cmap="viridis", linewidth=0, antialiased=True,
                      rcount=min(resolution, 55), ccount=min(resolution, 55))
    ax3d.set_xlabel("$x_1$", labelpad=2)
    ax3d.set_ylabel("$x_2$", labelpad=2)
    ax3d.set_zlabel("log excess", labelpad=2)
    ax3d.text2D(0.025, 0.96, "(b)", transform=ax3d.transAxes, va="top",
                fontsize=9, fontweight="bold",
                bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"})
    ax3d.tick_params(labelsize=7, pad=0)

    return fig, xx, yy, raw, z


def _plot_slice_pair(ax_contour, ax_surface, xx, yy, z, panel_label):
    levels = np.linspace(float(np.nanmin(z)), float(np.nanmax(z)), 28)
    contour = ax_contour.contourf(xx, yy, z, levels=levels, cmap="viridis")
    ax_contour.contour(xx, yy, z, levels=10, colors="white", alpha=0.32, linewidths=0.35)
    ax_contour.set_xlabel("$x_1$", fontsize=7)
    ax_contour.set_ylabel("$x_2$", fontsize=7)
    ax_contour.tick_params(labelsize=6)
    ax_contour.text(0.025, 0.95, panel_label, transform=ax_contour.transAxes, va="top",
                    fontsize=8, fontweight="bold",
                    bbox={"facecolor": "white", "alpha": 0.75, "edgecolor": "none"})
    ax_surface.plot_surface(xx, yy, z, cmap="viridis", linewidth=0, antialiased=True,
                            rcount=min(len(xx), 45), ccount=min(len(xx), 45))
    ax_surface.set_xlabel("$x_1$", labelpad=0, fontsize=7)
    ax_surface.set_ylabel("$x_2$", labelpad=0, fontsize=7)
    ax_surface.set_zlabel("log excess", labelpad=0, fontsize=6)
    ax_surface.tick_params(labelsize=5, pad=0)


def generate_body_pages(functions, landscapes, dims, params):
    BODY_FIGURES.mkdir(parents=True, exist_ok=True)
    tex_lines = [
        "% Generated by code/16_generate_benchmark_landscapes.py; each caption identifies functions.",
        "% Two-dimensional functions show the full landscape; higher-dimensional functions show a slice.",
    ]
    groups = [functions[i:i + 3] for i in range(0, len(functions), 3)]
    for page_num, group in enumerate(groups, start=1):
        fig = plt.figure(figsize=(8.27, 11.69))
        grid = fig.add_gridspec(len(group), 2, left=0.08, right=0.96, top=0.98,
                                bottom=0.04, hspace=0.28, wspace=0.23)
        for row, function in enumerate(group):
            _, xx, yy, _, z = landscapes[function]
            ax_contour = fig.add_subplot(grid[row, 0])
            ax_surface = fig.add_subplot(grid[row, 1], projection="3d")
            panel_label = f"({chr(ord('a') + row)})"
            _plot_slice_pair(ax_contour, ax_surface, xx, yy, z, panel_label)

        stem = f"landscape_body_group_{page_num:02d}"
        fig.savefig(BODY_FIGURES / f"{stem}.pdf", bbox_inches="tight")
        fig.savefig(BODY_FIGURES / f"{stem}.png", dpi=180, bbox_inches="tight")
        plt.close(fig)
        def function_descriptor(f):
            reference = params[f]["optimum"] * dims[f] if f == "F8" else params[f]["optimum"]
            if f == "F7":
                reference += 0.5
            ref_note = " expected objective" if f == "F7" else ""
            return (f"{f} ({FUNCTION_NAMES[f]}, $d={dims[f]}$, bounds "
                    f"$[{params[f]['lb']:g},{params[f]['ub']:g}]$, reference $f^*={reference:g}${ref_note})")
        ids = "; ".join(
            f"({chr(ord('a') + row)}) {function_descriptor(function)}"
            for row, function in enumerate(group)
        )
        slice_note = ("Within each panel, the left view is a contour and the right view is a 3-D surface. "
                      "Colour/elevation show the log-compressed nonnegative objective excess; "
                      "scales are local to each function. For $d>2$, remaining coordinates are "
                      "fixed at the midpoint of the solver bounds.")
        if "F7" in group:
            slice_note += " F7 shows the exact expected objective, including its 0.5 uniform-noise expectation."
        tex_lines += [
            "\\begin{figure}[p]",
            "  \\begin{adjustwidth}{-\\extralength}{0cm}",
            "  \\centering",
            f"  \\includegraphics[width=\\fulllength,height=0.84\\textheight,keepaspectratio]{{figures/landscapes_body/{stem}.pdf}}",
            "  \\end{adjustwidth}",
            f"  \\caption{{Benchmark objective landscapes and two-dimensional slices: {ids}. {slice_note}}}",
            f"  \\label{{fig:landscape_body_{page_num:02d}}}",
            "\\end{figure}",
            "\\clearpage",
            "",
        ]
    BODY_TEX.parent.mkdir(parents=True, exist_ok=True)
    BODY_TEX.write_text("\n".join(tex_lines), encoding="utf-8")
    print(f"[16] wrote {len(groups)} title-free grouped body pages and {BODY_TEX}")


def generate_si_figures(functions, landscapes, dims, params):
    tex_lines = ["% Generated captions for the landscape panels in this SI."]
    for function in functions:
        dim = dims[function]
        bound = params[function]
        if dim > 2:
            slice_note = f"The remaining {dim - 2} coordinates are fixed at the midpoint of the solver bounds."
        else:
            slice_note = "Both coordinates span the full two-dimensional search domain."
        noise = " The plotted objective is the exact expectation over F7's uniform additive noise." if function == "F7" else ""
        reference = params[function]["optimum"] * dim if function == "F8" else params[function]["optimum"]
        if function == "F7":
            reference += 0.5
        tex_lines += [
            "\\begin{figure}[p]",
            "  \\centering",
            f"  \\includegraphics[width=0.96\\textwidth,height=0.56\\textheight,keepaspectratio]{{SupplementaryData/figures/landscape_{function}.png}}",
            f"  \\caption{{{function}, {FUNCTION_NAMES[function]} ({dim}D), solver bounds $[{bound['lb']:g},{bound['ub']:g}]$, reference optimum $f^*={reference:g}$. Panel (a) is the contour view and panel (b) is the 3-D surface of the same slice. {slice_note}{noise}}}",
            f"  \\label{{fig:si_landscape_{function}}}",
            "\\end{figure}",
            "\\clearpage",
            "",
        ]
    SI_LANDSCAPE_TEX.parent.mkdir(parents=True, exist_ok=True)
    SI_LANDSCAPE_TEX.write_text("\n".join(tex_lines), encoding="utf-8")
    print(f"[16] wrote SI landscape captions for {len(functions)} functions")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--functions", default="all",
                        help="Comma-separated function IDs for a smoke test, e.g. F1,F7,F14; default all.")
    parser.add_argument("--resolution", type=int, default=RESOLUTION)
    args = parser.parse_args()
    params, dims = load_benchmark_parameters()
    functions = (sorted(params, key=lambda name: int(name[1:])) if args.functions == "all"
                 else args.functions.split(","))
    unknown = set(functions) - set(params)
    if unknown:
        raise ValueError(f"Unknown functions: {sorted(unknown)}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Store values behind every rendered slice, including exact solver metadata.
    values = []
    landscapes = {}
    landscape_pdf_path = OUT_DIR / "benchmark_landscape_slices.pdf"
    with PdfPages(landscape_pdf_path) as landscape_pdf:
        for function in functions:
            dim = dims[function]
            fig, xx, yy, raw, z = render_function(function, dim, params, args.resolution)
            fig.savefig(OUT_DIR / f"landscape_{function}.png", dpi=180, bbox_inches="tight")
            landscape_pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)
            landscapes[function] = (None, xx, yy, raw, z)
            values.append(pd.DataFrame({
                "function": function, "dimension": dim,
                "lb": params[function]["lb"], "ub": params[function]["ub"],
                "x1": xx.ravel(), "x2": yy.ravel(), "fitness": raw.ravel(),
                "reference_optimum": (params[function]["optimum"] + (0.5 if function == "F7" else 0.0)) * dim
                    if function == "F8" else params[function]["optimum"] + (0.5 if function == "F7" else 0.0),
                "visualization": "expected objective" if function == "F7" else "solver objective",
                "slice_context": "all dimensions" if dim == 2 else "remaining coordinates at box midpoint",
            }))
            print(f"[16] rendered {function} ({dim}D landscape/slice)")
    values_path = OUT_DIR / "landscape_slices_values.csv"
    pd.concat(values, ignore_index=True).to_csv(values_path, index=False)
    SI_FIGURES.mkdir(parents=True, exist_ok=True)
    for function in functions:
        shutil.copy2(OUT_DIR / f"landscape_{function}.png", SI_FIGURES / f"landscape_{function}.png")
    shutil.copy2(landscape_pdf_path, SI_FIGURES / landscape_pdf_path.name)
    shutil.copy2(values_path, SI_FIGURES.parent / values_path.name)
    if args.functions == "all":
        generate_body_pages(functions, landscapes, dims, params)
        generate_si_figures(functions, landscapes, dims, params)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
