#!/usr/bin/env python
"""
00_generate_level1_raw_data.py — Extract raw run-level data from BD/resultados.db.

Extracts the MDPI batch (33 configs x 62 instances x 31 runs = 63,426 experiments)
into two analysis-ready Parquet files plus a metadata CSV for Excel/R.

Outputs (results/level1_raw/):
    experiments_meta.parquet   one row per experiment
    experiments_meta.csv       same, human-readable
    iterations.parquet         one row per (experiment, iteration)
    summary.json               counts and verification checks

Usage:
    python 00_generate_level1_raw_data.py                # full extract
    python 00_generate_level1_raw_data.py --limit 100    # sanity check
    python 00_generate_level1_raw_data.py --meta-only    # skip iterations blob
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

# Paths anchored to repo root regardless of CWD.
REPO_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = REPO_ROOT / "BD" / "resultados.db"
OUT_DIR = REPO_ROOT / "FUZZY" / "ARTICULO_MDPI" / "results" / "level1_raw"

MH_FCS_RE = re.compile(r"^PSO_FCS:(O\d+):(\d+):(I\d+):R(\d+)$")
EXP_RE = re.compile(r"^(F\d+)\s+(\d+)$")

# F8 stores per-dim optimum (-418.9829); actual optimum = value * dim.
F8_PER_DIM_OPTIMUM = -418.9829


@dataclass
class ParsedMH:
    family: str          # "PSO" or "PSO_FCS"
    output_set: str      # "-" or "O1"
    n_labels: int | None
    input_set: str       # "-" or "I1"
    rule_set: str        # "-" or "R1".."R8"


def parse_mh(mh: str) -> ParsedMH:
    if mh == "PSO":
        return ParsedMH("PSO", "-", None, "-", "-")
    m = MH_FCS_RE.match(mh)
    if not m:
        raise ValueError(f"Unrecognized MH string: {mh!r}")
    return ParsedMH("PSO_FCS", m.group(1), int(m.group(2)), m.group(3), f"R{m.group(4)}")


def parse_experimento(exp: str) -> tuple[str, int]:
    m = EXP_RE.match(exp)
    if not m:
        raise ValueError(f"Unrecognized experimento string: {exp!r}")
    return m.group(1), int(m.group(2))


def real_optimum(func: str, dim: int, stored_opt: float) -> float:
    if func == "F8":
        return F8_PER_DIM_OPTIMUM * dim
    return stored_opt


def relative_gap(fitness_best: float, opt: float) -> float:
    # gap = (best - optimum) / max(|optimum|, 1), clipped >= 0.
    # 1 is the safe floor when optimum == 0 to avoid explosion.
    denom = max(abs(opt), 1.0)
    return max(0.0, (fitness_best - opt) / denom)


def query_batch(conn: sqlite3.Connection, limit: int | None) -> pd.DataFrame:
    """Return one row per experiment restricted to the 33 MH strings of the MDPI batch.

    Iterations table is intentionally excluded (LENGTH(archivo) forces reading every blob).
    """
    # Pin the 33 MDPI configs into a temp table once; avoids repeated GROUP BY scans.
    conn.execute("DROP TABLE IF EXISTS temp.mdpi_mh")
    conn.execute(
        "CREATE TEMP TABLE mdpi_mh AS "
        "SELECT MH FROM experimentos GROUP BY MH HAVING COUNT(*) = 1922"
    )
    sql = """
        SELECT
            ex.id_experimento AS id_exp,
            ex.MH AS mh_raw,
            ex.paramMH AS param_mh,
            ex.experimento AS exp_name,
            ex.estado AS estado,
            ins.nombre AS instancia,
            ins.optimo AS optimum_raw,
            res.fitness AS fitness_best,
            res.tiempoEjecucion AS t_exec
        FROM experimentos ex
        JOIN instancias ins ON ex.fk_id_instancia = ins.id_instancia
        LEFT JOIN resultados res ON res.fk_id_experimento = ex.id_experimento
        WHERE ex.MH IN (SELECT MH FROM mdpi_mh)
        ORDER BY ex.MH, ex.experimento, ex.id_experimento
    """
    if limit is not None:
        sql += f"\nLIMIT {int(limit)}"
    return pd.read_sql_query(sql, conn)


def enrich_meta(df: pd.DataFrame) -> pd.DataFrame:
    parsed = [parse_mh(mh) for mh in df["mh_raw"]]
    df["mh_family"] = [p.family for p in parsed]
    df["output_set"] = [p.output_set for p in parsed]
    df["n_labels"] = pd.array([p.n_labels for p in parsed], dtype="Int64")
    df["input_set"] = [p.input_set for p in parsed]
    df["rule_set"] = [p.rule_set for p in parsed]

    fun_dim = [parse_experimento(e) for e in df["exp_name"]]
    df["function"] = [fd[0] for fd in fun_dim]
    df["dim"] = [fd[1] for fd in fun_dim]

    df["optimum"] = [real_optimum(f, d, o) for f, d, o in zip(df["function"], df["dim"], df["optimum_raw"])]
    df["gap_final"] = [relative_gap(b, o) for b, o in zip(df["fitness_best"], df["optimum"])]

    df["run_id"] = df.groupby(["mh_raw", "exp_name"]).cumcount() + 1
    df["seed"] = 42 * df["run_id"]  # matches the seed contract in 02_setup_experimental.md
    return df


ITER_FLOAT_COLS = (
    "best_fitness", "mean_fitness", "std_fitness", "time",
    "XPL", "XPT", "DIV", "GAP", "RDP", "ENT",
    "Divj_mean", "Divj_min", "Divj_max", "w",
)


def parse_blob(blob: bytes) -> pd.DataFrame:
    text = blob.decode("utf-8")
    df = pd.read_csv(io.StringIO(text))
    # Some rows contain magnitudes that pandas infers as object in a chunk; force floats.
    for col in ITER_FLOAT_COLS:
        if col in df.columns and df[col].dtype == "object":
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def write_iterations(meta: pd.DataFrame, conn: sqlite3.Connection, out_path: Path, chunk_size: int = 500) -> tuple[int, int]:
    """Stream iteration blobs into a single Parquet file; return (rows_total, exps_written)."""
    if out_path.exists():
        out_path.unlink()
    writer: pq.ParquetWriter | None = None
    rows_total = 0
    exps_written = 0

    ids = meta["id_exp"].tolist()
    with tqdm(total=len(ids), desc="iterations", unit="exp") as pbar:
        for start in range(0, len(ids), chunk_size):
            chunk_ids = ids[start : start + chunk_size]
            placeholders = ",".join("?" * len(chunk_ids))
            rows = conn.execute(
                f"SELECT fk_id_experimento, archivo FROM iteraciones WHERE fk_id_experimento IN ({placeholders})",
                chunk_ids,
            ).fetchall()
            dfs = []
            for id_exp, blob in rows:
                if blob is None:
                    continue
                df_it = parse_blob(blob)
                df_it.insert(0, "id_exp", id_exp)
                dfs.append(df_it)
            if not dfs:
                pbar.update(len(chunk_ids))
                continue
            batch = pd.concat(dfs, ignore_index=True)
            # Post-concat coercion: mixed dtypes across blobs may leave object columns.
            for col in ITER_FLOAT_COLS:
                if col in batch.columns and batch[col].dtype == "object":
                    batch[col] = pd.to_numeric(batch[col], errors="coerce")
            table = pa.Table.from_pandas(batch, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema, compression="snappy")
            writer.write_table(table)
            rows_total += len(batch)
            exps_written += len(dfs)
            pbar.update(len(chunk_ids))
    if writer is not None:
        writer.close()
    return rows_total, exps_written


def build_summary(meta: pd.DataFrame, iter_rows: int, iter_exps: int) -> dict:
    return {
        "n_experiments": int(len(meta)),
        "n_functions": int(meta["function"].nunique()),
        "n_instances": int(meta[["function", "dim"]].drop_duplicates().shape[0]),
        "n_configs": int(meta["mh_raw"].nunique()),
        "runs_per_config_instance_min": int(meta.groupby(["mh_raw", "exp_name"]).size().min()),
        "runs_per_config_instance_max": int(meta.groupby(["mh_raw", "exp_name"]).size().max()),
        "estados": meta["estado"].value_counts().to_dict(),
        "families": meta["mh_family"].value_counts().to_dict(),
        "n_labels_distinct": sorted(meta["n_labels"].dropna().unique().astype(int).tolist()),
        "rule_sets_distinct": sorted(x for x in meta["rule_set"].unique() if x != "-"),
        "dims_distinct": sorted(meta["dim"].unique().astype(int).tolist()),
        "gap_final_stats": {
            "min": float(meta["gap_final"].min()),
            "median": float(meta["gap_final"].median()),
            "max": float(meta["gap_final"].max()),
        },
        "fitness_best_nan_count": int(meta["fitness_best"].isna().sum()),
        "iterations_rows_total": int(iter_rows),
        "iterations_experiments_written": int(iter_exps),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None, help="only process first N experiments (sanity)")
    ap.add_argument("--meta-only", action="store_true", help="skip iterations Parquet (fast)")
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"[ERR] DB not found: {DB_PATH}", file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    meta_parquet = OUT_DIR / "experiments_meta.parquet"
    meta_csv = OUT_DIR / "experiments_meta.csv"
    iter_parquet = OUT_DIR / "iterations.parquet"
    summary_json = OUT_DIR / "summary.json"

    print(f"[00] source     : {DB_PATH}")
    print(f"[00] output dir : {OUT_DIR}")
    print(f"[00] limit      : {args.limit}")
    print(f"[00] meta-only  : {args.meta_only}")

    conn = sqlite3.connect(str(DB_PATH))
    try:
        meta = query_batch(conn, args.limit)
        print(f"[00] rows fetched from DB : {len(meta):,}")
        meta = enrich_meta(meta)

        cols_meta = [
            "id_exp", "mh_raw", "mh_family", "output_set", "n_labels", "input_set", "rule_set",
            "exp_name", "function", "dim", "optimum",
            "run_id", "seed", "fitness_best", "gap_final", "t_exec", "estado",
        ]
        meta_out = meta[cols_meta].copy()
        meta_out.to_parquet(meta_parquet, index=False, compression="snappy")
        meta_out.to_csv(meta_csv, index=False)
        print(f"[00] wrote meta : {meta_parquet.name} ({meta_parquet.stat().st_size/1024:,.0f} KB)")
        print(f"[00] wrote meta : {meta_csv.name}     ({meta_csv.stat().st_size/1024:,.0f} KB)")

        rows_total, exps_written = 0, 0
        if not args.meta_only:
            rows_total, exps_written = write_iterations(meta_out, conn, iter_parquet)
            size_mb = iter_parquet.stat().st_size / (1024 * 1024)
            print(f"[00] wrote iter : {iter_parquet.name} ({size_mb:,.1f} MB, {rows_total:,} rows, {exps_written:,} exps)")

        summary = build_summary(meta_out, rows_total, exps_written)
        summary_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
        print(f"[00] wrote summary : {summary_json.name}")

        print("\n[00] === SUMMARY ===")
        print(json.dumps(summary, indent=2, sort_keys=True))
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
