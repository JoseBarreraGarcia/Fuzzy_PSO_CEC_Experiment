#!/usr/bin/env python
"""
14_analyze_controller_dynamics.py — Section 5.7 (dynamic behaviour of the controller).

Connects the final-quality results of Sections 5.1-5.6 with what the controller
actually does during the run: the inertia-weight trajectory it produces, the
exploration level it sustains, and the convergence profile that follows.

The per-iteration store is large (63.5 M rows, 2.4 GB), so it is consumed as a
stream: trajectories are accumulated as running sums per (configuration, iteration)
and only the few experiments needed for the convergence panels are materialized.

Available per-iteration columns: iter, nfe, best_fitness, mean_fitness, std_fitness,
time, XPL, XPT, DIV, GAP, RDP, ENT, Divj_mean, Divj_min, Divj_max, w.
DIV is unnormalized and therefore not comparable across functions; RDP is identically
zero in this batch. XPL (percentage of exploration, 100*DIV/maxDIV) is the normalized
diversity signal the controller consumes and is used instead.

Inputs:
    results/level1_raw/iterations.parquet
    results/level1_raw/experiments_meta.csv
    results/level3_rankings/function_level_per_function.csv

Outputs:
    results/level3_rankings/w_trajectory_by_config.csv
    results/level3_rankings/w_trajectory_summary.csv
    manuscript/figures/fig_w_trajectories.{png,pdf}
    manuscript/figures/fig_convergence_representative.{png,pdf}
    results/figures_all/ (same two figures)
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _naming import short_name

REPO_ROOT = Path(__file__).resolve().parents[3]
MDPI = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI"
ITERATIONS = MDPI / "results" / "level1_raw" / "iterations.parquet"
META = MDPI / "results" / "level1_raw" / "experiments_meta.csv"
PER_FUNCTION = MDPI / "results" / "level3_rankings" / "function_level_per_function.csv"
OUT_L3 = MDPI / "results" / "level3_rankings"
OUT_FIG = MDPI / "results" / "figures_all"
MS_FIGURES = MDPI / "manuscript" / "figures"

BATCH_ROWS = 2_000_000
MAX_ITER = 1000
N_ITERS = MAX_ITER + 1
GRANULARITIES = [3, 5, 7, 9]
RULES = [f"R{i}" for i in range(1, 9)]

# Progress direction of each rule pattern, used only for colouring.
PROGRESS = {"R1": "decreasing", "R2": "increasing", "R3": "agnostic", "R4": "agnostic",
            "R5": "decreasing", "R6": "decreasing", "R7": "increasing", "R8": "increasing"}
STYLE = {"decreasing": ("tab:green", "-"),
         "agnostic": ("tab:orange", "--"),
         "increasing": ("tab:red", ":")}

# One instance per landscape regime, chosen from the function-level results.
CONVERGENCE_CASES = [
    ("F1", 30, "Unimodal (F1, $d=30$)"),
    ("F9", 30, "Scalable multimodal (F9, $d=30$)"),
    ("F14", 2, "Fixed-dimensional, fuzzy control ahead (F14)"),
    ("F23", 4, "Fixed-dimensional, baseline ahead (F23)"),
]
WEAK_CONFIG = "FCS-9-R2"  # worst configuration of the global ranking


def load_meta() -> pd.DataFrame:
    meta = pd.read_csv(META, usecols=["id_exp", "mh_raw", "mh_family", "n_labels",
                                      "rule_set", "function", "dim", "run_id"])
    meta["config"] = meta["mh_raw"].map(short_name)
    meta["instance"] = meta["function"] + "_D" + meta["dim"].astype(int).astype(str)
    return meta


def select_convergence_ids(meta: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    per_function = pd.read_csv(PER_FUNCTION).set_index("function")
    wanted = {}
    for function, dim, _ in CONVERGENCE_CASES:
        best = per_function.loc[function, "best_fcs"]
        configs = ["PSO", "FCS-3-R1"]
        if isinstance(best, str) and best not in configs and best != "--":
            configs.append(best)
        configs.append(WEAK_CONFIG)
        wanted[(function, dim)] = configs
    mask = np.zeros(len(meta), dtype=bool)
    for (function, dim), configs in wanted.items():
        mask |= ((meta["function"] == function) & (meta["dim"] == dim)
                 & meta["config"].isin(configs)).to_numpy()
    return meta[mask], wanted


def stream(meta: pd.DataFrame, convergence_ids: set[int]):
    """Single pass: running sums of w and XPL per (config, iter) plus convergence rows."""
    configs = sorted(meta["config"].unique())
    config_index = {c: i for i, c in enumerate(configs)}
    lookup = np.full(int(meta["id_exp"].max()) + 1, -1, dtype=np.int32)
    lookup[meta["id_exp"].to_numpy()] = meta["config"].map(config_index).to_numpy()

    cells = len(configs) * N_ITERS
    w_sum = np.zeros(cells)
    xpl_sum = np.zeros(cells)
    counts = np.zeros(cells)
    convergence_chunks = []

    reader = pq.ParquetFile(ITERATIONS)
    processed = 0
    for batch in reader.iter_batches(batch_size=BATCH_ROWS,
                                     columns=["id_exp", "iter", "w", "XPL", "best_fitness"]):
        ids = batch.column("id_exp").to_numpy()
        iters = batch.column("iter").to_numpy()
        cfg = lookup[ids]
        valid = (cfg >= 0) & (iters >= 0) & (iters <= MAX_ITER)
        flat = cfg[valid].astype(np.int64) * N_ITERS + iters[valid]
        w = batch.column("w").to_numpy()[valid]
        xpl = batch.column("XPL").to_numpy()[valid]
        w_sum += np.bincount(flat, weights=w, minlength=cells)
        xpl_sum += np.bincount(flat, weights=xpl, minlength=cells)
        counts += np.bincount(flat, minlength=cells)

        wanted = np.isin(ids, list(convergence_ids))
        if wanted.any():
            convergence_chunks.append(pd.DataFrame({
                "id_exp": ids[wanted], "iter": iters[wanted],
                "best_fitness": batch.column("best_fitness").to_numpy()[wanted],
            }))
        processed += len(ids)
        print(f"\r[14] streamed {processed/1e6:6.1f} M rows", end="", flush=True)
    print()

    with np.errstate(invalid="ignore", divide="ignore"):
        w_mean = np.where(counts > 0, w_sum / counts, np.nan).reshape(len(configs), N_ITERS)
        xpl_mean = np.where(counts > 0, xpl_sum / counts, np.nan).reshape(len(configs), N_ITERS)
    trajectories = pd.DataFrame({
        "config": np.repeat(configs, N_ITERS),
        "iter": np.tile(np.arange(N_ITERS), len(configs)),
        "w_mean": w_mean.ravel(),
        "xpl_mean": xpl_mean.ravel(),
        "n_runs": counts.reshape(len(configs), N_ITERS).ravel(),
    })
    convergence = pd.concat(convergence_chunks, ignore_index=True) if convergence_chunks \
        else pd.DataFrame(columns=["id_exp", "iter", "best_fitness"])
    return trajectories, convergence


def plot_w_trajectories(traj: pd.DataFrame) -> None:
    pivot_w = traj.pivot(index="iter", columns="config", values="w_mean")
    pivot_x = traj.pivot(index="iter", columns="config", values="xpl_mean")

    fig, axes = plt.subplots(2, 4, figsize=(10.5, 5.2), sharex=True, sharey="row")
    for col, n in enumerate(GRANULARITIES):
        ax = axes[0, col]
        for rule in RULES:
            name = f"FCS-{n}-{rule}"
            if name not in pivot_w:
                continue
            color, ls = STYLE[PROGRESS[rule]]
            ax.plot(pivot_w.index, pivot_w[name], color=color, linestyle=ls, linewidth=1.1)
            ax.annotate(rule, (MAX_ITER, pivot_w[name].iloc[-1]), fontsize=6, color=color,
                        xytext=(3, -2), textcoords="offset points")
        ax.plot(pivot_w.index, pivot_w["PSO"], color="black", linestyle="-", linewidth=1.6)
        ax.set_title(f"$n = {n}$", fontsize=10)
        ax.set_ylim(0.05, 0.95)
        ax.set_xlim(0, MAX_ITER * 1.09)
        ax.grid(alpha=0.3)
        if col == 0:
            ax.set_ylabel("Mean inertia weight $w$")

        ax = axes[1, col]
        for rule in RULES:
            name = f"FCS-{n}-{rule}"
            if name not in pivot_x:
                continue
            color, ls = STYLE[PROGRESS[rule]]
            ax.plot(pivot_x.index, pivot_x[name], color=color, linestyle=ls, linewidth=1.1)
        ax.plot(pivot_x.index, pivot_x["PSO"], color="black", linestyle="-", linewidth=1.6)
        ax.set_xlabel("Iteration")
        ax.set_yscale("log")
        ax.grid(alpha=0.3)
        if col == 0:
            ax.set_ylabel("Mean exploration XPL (%)")

    handles = [plt.Line2D([], [], color=c, linestyle=l, label=lab)
               for lab, (c, l) in (("progress decreasing (R1, R5, R6)", STYLE["decreasing"]),
                                   ("progress neutral (R3, R4)", STYLE["agnostic"]),
                                   ("progress increasing (R2, R7, R8)", STYLE["increasing"]))]
    handles.append(plt.Line2D([], [], color="black", linestyle="-", label="PSO (linear schedule)"))
    fig.legend(handles=handles, fontsize=8, ncol=4, loc="lower center",
               bbox_to_anchor=(0.5, -0.03), frameon=False)
    fig.tight_layout()
    _save(fig, "fig_w_trajectories")


def plot_convergence(convergence: pd.DataFrame, meta: pd.DataFrame, wanted: dict) -> None:
    merged = convergence.merge(meta[["id_exp", "config", "function", "dim"]], on="id_exp")
    fig, axes = plt.subplots(2, 2, figsize=(9.0, 6.2))
    palette = {"PSO": "black", "FCS-3-R1": "tab:green", WEAK_CONFIG: "tab:red"}

    for ax, (function, dim, title) in zip(axes.ravel(), CONVERGENCE_CASES):
        block = merged[(merged["function"] == function) & (merged["dim"] == dim)]
        for i, config in enumerate(wanted[(function, dim)]):
            sub = block[block["config"] == config]
            if sub.empty:
                continue
            grouped = sub.groupby("iter")["best_fitness"]
            median = grouped.median()
            q1, q3 = grouped.quantile(0.25), grouped.quantile(0.75)
            color = palette.get(config, "tab:blue")
            ax.plot(median.index, median.to_numpy(), color=color, linewidth=1.4, label=config)
            ax.fill_between(median.index, q1.to_numpy(), q3.to_numpy(), color=color, alpha=0.15)
        ax.set_title(title, fontsize=9.5)
        ax.set_xlabel("Iteration")
        ax.set_ylabel("Best fitness (median, IQR band)")
        ax.set_yscale("symlog", linthresh=1e-12)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7.5, loc="upper right")
    fig.tight_layout()
    _save(fig, "fig_convergence_representative")


def _save(fig, stem: str) -> None:
    for directory in (MS_FIGURES, OUT_FIG):
        directory.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "pdf"):
            fig.savefig(directory / f"{stem}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"[14] wrote {stem}.{{png,pdf}}")


def summarize(traj: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for config, block in traj.groupby("config"):
        block = block.sort_values("iter")
        w = block["w_mean"].to_numpy()
        early = np.nanmean(w[:100])
        late = np.nanmean(w[-100:])
        rows.append({
            "config": config,
            "rule_set": config.split("-")[-1] if config != "PSO" else "--",
            "w_mean_overall": float(np.nanmean(w)),
            "w_early_first100": float(early),
            "w_late_last100": float(late),
            "w_drop": float(early - late),
            "xpl_late_last100": float(np.nanmean(block["xpl_mean"].to_numpy()[-100:])),
        })
    return pd.DataFrame(rows).sort_values("w_drop", ascending=False)


def main() -> int:
    replot = "--replot" in sys.argv
    for path in (ITERATIONS, META, PER_FUNCTION):
        if not path.exists() and not (replot and path == ITERATIONS):
            raise FileNotFoundError(f"missing input: {path}")

    meta = load_meta()
    convergence_meta, wanted = select_convergence_ids(meta)
    print(f"[14] convergence subset: {len(convergence_meta)} experiments")
    for key, configs in wanted.items():
        print(f"     {key}: {configs}")

    traj_path = OUT_L3 / "w_trajectory_by_config.csv"
    conv_path = OUT_L3 / "convergence_representative.csv"
    if replot and traj_path.exists() and conv_path.exists():
        # Re-plot from cache: the per-iteration store is 2.4 GB and does not need a second scan.
        traj = pd.read_csv(traj_path)
        convergence = pd.read_csv(conv_path)
        print("[14] replotting from cached CSV")
    else:
        traj, convergence = stream(meta, set(convergence_meta["id_exp"].tolist()))
        OUT_L3.mkdir(parents=True, exist_ok=True)
        traj.to_csv(traj_path, index=False)
        convergence.to_csv(conv_path, index=False)

    summary = summarize(traj)
    summary.to_csv(OUT_L3 / "w_trajectory_summary.csv", index=False)

    plot_w_trajectories(traj)
    plot_convergence(convergence, meta, wanted)

    print("\n[14] inertia-weight trajectory summary (sorted by early-to-late drop):")
    print(summary.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
