#!/usr/bin/env python
"""
05_run_pareto_problemtype.py — H2 (rules x problem class) and H5 (subgroup transferability).

Implements H2 and H5 per FUZZY/ARTICULO_MDPI/04_hipotesis_metricas_analisis.md:
    - H2: rule ranking depends on problem class (unimodal / multimodal / composed).
    - H5: no static (n*, R*) dominates both subgroups S1 (F1-F13) and S2 (F14-F23).

Outputs (results/tests/h5_pareto_problemtype/):
    problem_class_assignment.csv        mapping function -> class
    ranking_by_class.{csv,parquet}      mh ranked inside each problem class
    winners_by_class.{csv,parquet}      argmin config per class
    kendall_tau_matrix.{csv,parquet}    pairwise Kendall tau between class rankings
    argmin_transferability.{csv,parquet}  best config global vs per subgroup
    pareto_front.{csv,parquet}          non-dominated in (rank_S1, rank_S2) space
    summary.json
"""
from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import kendalltau

REPO_ROOT = Path(__file__).resolve().parents[3]
L2_PATH = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level2_aggregated" / "stats_by_config_instance.parquet"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "tests" / "h5_pareto_problemtype"

# Problem class mapping (Classical Benchmark Suite, Abualigah et al. 2021).
CLASS_MAP = {
    "F1":  "unimodal",  "F2":  "unimodal",  "F3":  "unimodal",  "F4":  "unimodal",  "F5":  "unimodal",
    "F6":  "unimodal",  "F7":  "unimodal",
    "F8":  "multimodal", "F9":  "multimodal", "F10": "multimodal", "F11": "multimodal", "F12": "multimodal",
    "F13": "multimodal",
    "F14": "composed",  "F15": "composed",  "F16": "composed",  "F17": "composed",  "F18": "composed",
    "F19": "composed",  "F20": "composed",  "F21": "composed",  "F22": "composed",  "F23": "composed",
}
SUBGROUP = {f: ("S1" if int(f[1:]) <= 13 else "S2") for f in CLASS_MAP}


def rank_by(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    df = df.copy()
    df["rank"] = df[metric].rank(method="min", ascending=True)
    return df.sort_values("rank").reset_index(drop=True)


def kendall_matrix(rankings: dict[str, pd.Series]) -> tuple[pd.DataFrame, pd.DataFrame]:
    labels = list(rankings.keys())
    n = len(labels)
    tau = np.eye(n)
    p = np.zeros((n, n))
    # Align on the union of mh_raw keys so kendalltau receives paired values.
    aligned = pd.DataFrame({k: v for k, v in rankings.items()}).sort_index()
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a = aligned[labels[i]].to_numpy()
            b = aligned[labels[j]].to_numpy()
            t, pv = kendalltau(a, b)
            tau[i, j] = t
            p[i, j] = pv
    return (
        pd.DataFrame(tau, index=labels, columns=labels),
        pd.DataFrame(p, index=labels, columns=labels),
    )


def pareto_front(df: pd.DataFrame, xcol: str, ycol: str) -> pd.DataFrame:
    pts = df[[xcol, ycol]].to_numpy()
    idx = np.argsort(pts[:, 0])
    kept: list[int] = []
    best_y = np.inf
    for k in idx:
        if pts[k, 1] < best_y:
            kept.append(k)
            best_y = pts[k, 1]
    return df.iloc[sorted(kept)].reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metric", choices=["gap_median", "gap_mean"], default="gap_median")
    args = parser.parse_args()

    if not L2_PATH.exists():
        raise FileNotFoundError(f"missing input: {L2_PATH}. Run script 01 first.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[05] source     : {L2_PATH}")
    print(f"[05] output dir : {OUT_DIR}")
    print(f"[05] metric     : {args.metric}")

    df = pd.read_parquet(L2_PATH)
    df["problem_class"] = df["function"].map(CLASS_MAP)
    df["subgroup"] = df["function"].map(SUBGROUP)
    print(f"[05] input rows : {len(df):,}  classes: {sorted(df['problem_class'].unique())}")

    pd.DataFrame({"function": list(CLASS_MAP.keys()),
                  "problem_class": list(CLASS_MAP.values()),
                  "subgroup": [SUBGROUP[f] for f in CLASS_MAP]}
                 ).to_csv(OUT_DIR / "problem_class_assignment.csv", index=False)

    # Ranking per problem class (mean gap over instances of that class per mh).
    per_class = (
        df.groupby(["mh_raw", "mh_family", "n_labels", "rule_set", "problem_class"], dropna=False)[args.metric]
          .mean().reset_index()
    )
    ranks_by_class = []
    for cls, sub in per_class.groupby("problem_class"):
        r = rank_by(sub, args.metric)
        r["problem_class"] = cls
        ranks_by_class.append(r)
    ranks_class_df = pd.concat(ranks_by_class, ignore_index=True)
    ranks_class_df.to_parquet(OUT_DIR / "ranking_by_class.parquet", index=False)
    ranks_class_df.to_csv(OUT_DIR / "ranking_by_class.csv", index=False)
    print(f"[05] wrote ranking_by_class : {len(ranks_class_df)} rows")

    winners_class = ranks_class_df[ranks_class_df["rank"] == 1]
    winners_class.to_parquet(OUT_DIR / "winners_by_class.parquet", index=False)
    winners_class.to_csv(OUT_DIR / "winners_by_class.csv", index=False)
    print(f"[05] wrote winners_by_class : {len(winners_class)} rows")

    # Kendall tau between rankings (indexed by mh_raw).
    class_rankings = {
        cls: sub.set_index("mh_raw")["rank"]
        for cls, sub in ranks_class_df.groupby("problem_class")
    }
    tau_df, tau_p = kendall_matrix(class_rankings)
    tau_df.to_csv(OUT_DIR / "kendall_tau_by_class.csv")
    tau_p.to_csv(OUT_DIR / "kendall_p_by_class.csv")
    print(f"[05] wrote kendall_tau_by_class")

    # Rankings by subgroup S1/S2 (this is the H5 test).
    per_sub = (
        df.groupby(["mh_raw", "mh_family", "n_labels", "rule_set", "subgroup"], dropna=False)[args.metric]
          .mean().reset_index()
    )
    ranks_by_sub = []
    for sg, sub in per_sub.groupby("subgroup"):
        r = rank_by(sub, args.metric)
        r["subgroup"] = sg
        ranks_by_sub.append(r)
    ranks_sub_df = pd.concat(ranks_by_sub, ignore_index=True)
    ranks_sub_df.to_csv(OUT_DIR / "ranking_by_subgroup.csv", index=False)

    sub_rankings = {sg: s.set_index("mh_raw")["rank"] for sg, s in ranks_sub_df.groupby("subgroup")}
    aligned_sub = pd.DataFrame({k: v for k, v in sub_rankings.items()}).sort_index()
    tau_S1_S2, p_S1_S2 = kendalltau(aligned_sub["S1"].to_numpy(), aligned_sub["S2"].to_numpy())

    # Argmin per subgroup vs global.
    per_global = (
        df.groupby(["mh_raw", "mh_family", "n_labels", "rule_set"], dropna=False)[args.metric]
          .mean().reset_index().sort_values(args.metric).reset_index(drop=True)
    )
    best_global = per_global.iloc[0][["mh_raw", args.metric]].to_dict()
    best_by_sub = {
        sg: sub.sort_values(args.metric).iloc[0][["mh_raw", args.metric]].to_dict()
        for sg, sub in per_sub.groupby("subgroup")
    }
    transfer_rows = [
        {"scope": "global", "best_mh": best_global["mh_raw"], "metric_value": best_global[args.metric]},
    ]
    for sg, info in best_by_sub.items():
        transfer_rows.append({"scope": sg, "best_mh": info["mh_raw"], "metric_value": info[args.metric]})
    transfer_df = pd.DataFrame(transfer_rows)
    transfer_df.to_csv(OUT_DIR / "argmin_transferability.csv", index=False)
    transfer_df.to_parquet(OUT_DIR / "argmin_transferability.parquet", index=False)

    # Pareto front in (rank_S1, rank_S2).
    piv = ranks_sub_df.pivot(index="mh_raw", columns="subgroup", values="rank").reset_index()
    piv = piv.merge(
        per_global[["mh_raw", "mh_family", "n_labels", "rule_set"]], on="mh_raw", how="left"
    )
    pareto = pareto_front(piv.sort_values("S1"), "S1", "S2")
    pareto.to_csv(OUT_DIR / "pareto_front.csv", index=False)
    pareto.to_parquet(OUT_DIR / "pareto_front.parquet", index=False)
    print(f"[05] wrote pareto_front : {len(pareto)} points (of {len(piv)} configs)")

    # H5 verdict.
    h5_supported = (
        best_by_sub["S1"]["mh_raw"] != best_by_sub["S2"]["mh_raw"]
    ) and (tau_S1_S2 < 0.7)

    summary = {
        "metric": args.metric,
        "n_configs": int(per_global["mh_raw"].nunique()),
        "kendall_tau_S1_vs_S2": float(tau_S1_S2),
        "kendall_p_S1_vs_S2": float(p_S1_S2),
        "kendall_by_class": tau_df.to_dict(),
        "best_global": best_global,
        "best_by_subgroup": best_by_sub,
        "H5_supported": bool(h5_supported),
        "H5_criteria": {
            "argmin_S1_differs_from_S2": bool(best_by_sub["S1"]["mh_raw"] != best_by_sub["S2"]["mh_raw"]),
            "tau_S1_S2_below_0.7": bool(tau_S1_S2 < 0.7),
        },
        "winners_by_class": winners_class[["problem_class", "mh_raw", "rule_set", "n_labels", args.metric]].to_dict(orient="records"),
        "pareto_front_configs": pareto.to_dict(orient="records"),
    }
    with (OUT_DIR / "summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, default=str)
    print(f"[05] wrote summary : summary.json\n")
    print("[05] === SUMMARY ===")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
