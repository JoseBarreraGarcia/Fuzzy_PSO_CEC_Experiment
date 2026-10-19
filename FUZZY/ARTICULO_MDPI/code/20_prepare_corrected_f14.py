#!/usr/bin/env python
"""Prepare and validate an isolated corrected-F14 rerun; never launches it.

Run from any working directory. The execution itself uses the existing 2_main.py
from inside the selected output directory, whose SQLite database contains the
historical global experiment IDs. This preserves the original seed formula.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[3]
MDPI = ROOT / "FUZZY" / "ARTICULO_MDPI"
ARCHIVE_DB = ROOT / "BD" / "resultados.db"
CONFIG_PATH = ROOT / "config" / "experiments_mdpi_full.json"
LEVEL1_PARQUET = MDPI / "results" / "level1_raw" / "experiments_meta.parquet"
F14_SOURCE = ROOT / "Problem" / "Benchmark" / "Problem.py"
RUNNER_SOURCE = ROOT / "2_main.py"
OUTPUTS = {
    "validation": MDPI / "results" / "f14_validation_20261014",
    "full": MDPI / "results" / "f14_corrected_20261014",
}
EXPECTED_FULL_RUNS = 1_023
VALIDATION_CONFIGS = (
    "PSO",
    "PSO_FCS:O1:3:I1:R1",
    "PSO_FCS:O1:3:I1:R8",
    "PSO_FCS:O1:5:I1:R1",
    "PSO_FCS:O1:7:I1:R4",
    "PSO_FCS:O1:9:I1:R8",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def archive_connection() -> sqlite3.Connection:
    uri = f"file:{ARCHIVE_DB.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def expected_mh_names(config: dict) -> set[str]:
    names = {name for name in config["mhs"] if name != "PSO_FCS"}
    for params in config.get("mh_params", {}).get("PSO_FCS", []):
        suffix = ":".join(
            str(value) for key, value in params.items() if key not in {"wMin", "wMax"}
        )
        names.add(f"PSO_FCS:{suffix}")
    return names


def parse_param_mh(text: str) -> dict[str, str]:
    parsed = {}
    for field in text.split(","):
        key, value = field.split(":", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def configuration_id(mh: str) -> str:
    if mh == "PSO":
        return "PSO"
    fields = mh.split(":")
    if len(fields) != 5 or fields[0] != "PSO_FCS":
        raise ValueError(f"Unrecognized historical configuration: {mh}")
    return f"FCS-{fields[2]}-{fields[4]}"


def load_and_validate_archive() -> tuple[dict, list[dict], tuple]:
    for path in (ARCHIVE_DB, CONFIG_PATH, LEVEL1_PARQUET, F14_SOURCE, RUNNER_SOURCE):
        if not path.exists():
            raise FileNotFoundError(path)
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    ben = config["experimentos"]["BEN"]
    if (config.get("use_seed") is not True or int(config.get("seed", -1)) != 42
            or int(config.get("parallel_workers", -1)) != 6
            or int(ben["iteraciones"]) != 1000 or int(ben["poblacion"]) != 20
            or int(ben["num_experimentos"]) != 31
            or config["dimensiones"]["BEN"].get("F14") != [2]
            or "F14" not in config["instancias"]["BEN"]):
        raise ValueError("The approved full profile does not match the requested F14 protocol")

    connection = archive_connection()
    try:
        rows = connection.execute(
            """SELECT e.id_experimento, e.experimento, e.MH, e.binarizacion,
                      e.paramMH, e.ML, e.paramML, e.ML_FS, e.paramML_FS,
                      e.estado, e.fk_id_instancia, i.tipo_problema, i.nombre,
                      i.optimo, i.param, r.fitness, r.tiempoEjecucion
               FROM experimentos e
               JOIN instancias i ON i.id_instancia=e.fk_id_instancia
               LEFT JOIN resultados r ON r.fk_id_experimento=e.id_experimento
               WHERE i.nombre='F14' AND i.tipo_problema='BEN' AND e.experimento='F14 2'
               ORDER BY e.id_experimento"""
        ).fetchall()
        instances = connection.execute(
            "SELECT id_instancia,tipo_problema,nombre,optimo,param FROM instancias "
            "WHERE nombre='F14' AND tipo_problema='BEN'"
        ).fetchall()
        result_counts = connection.execute(
            """SELECT e.id_experimento,COUNT(r.id_resultado)
               FROM experimentos e JOIN instancias i ON i.id_instancia=e.fk_id_instancia
               LEFT JOIN resultados r ON r.fk_id_experimento=e.id_experimento
               WHERE i.nombre='F14' AND i.tipo_problema='BEN' AND e.experimento='F14 2'
               GROUP BY e.id_experimento"""
        ).fetchall()
    finally:
        connection.close()

    if len(instances) != 1:
        raise ValueError(f"Expected one historical F14 instance row; found {len(instances)}")
    if len(rows) != EXPECTED_FULL_RUNS:
        raise ValueError(f"Expected {EXPECTED_FULL_RUNS} historical F14 runs; found {len(rows)}")
    if len({row[0] for row in rows}) != EXPECTED_FULL_RUNS:
        raise ValueError("Historical F14 experiment IDs are missing or duplicated")
    if any(count != 1 for _, count in result_counts) or len(result_counts) != EXPECTED_FULL_RUNS:
        raise ValueError("A historical F14 experiment does not have exactly one result row")

    profile_names = expected_mh_names(config)
    groups: dict[str, list[tuple]] = defaultdict(list)
    for row in rows:
        exp_id, exp_name, mh, binarization, param_mh = row[:5]
        status, instance_id, problem, instance, optimum, instance_param = row[9:15]
        historical_fitness, historical_time = row[15:17]
        if (exp_name != "F14 2" or problem != "BEN" or instance != "F14"
                or not math.isclose(float(optimum), 1.0)
                or status != "terminado" or historical_fitness is None
                or historical_time is None):
            raise ValueError(f"Incomplete or inconsistent historical row: exp_id={exp_id}")
        params = parse_param_mh(param_mh)
        if params.get("iter") != "1000" or params.get("pop") != "20":
            raise ValueError(f"Wrong historical protocol at exp_id={exp_id}: {param_mh}")
        if mh == "PSO":
            if binarization != "N/A" or params != {"iter": "1000", "pop": "20"}:
                raise ValueError(f"PSO config mismatch at exp_id={exp_id}")
        else:
            if mh not in profile_names:
                raise ValueError(f"Unexpected configuration at exp_id={exp_id}: {mh}")
            match = next((p for p in config["mh_params"]["PSO_FCS"]
                          if mh == "PSO_FCS:" + ":".join(
                              str(v) for k, v in p.items() if k not in {"wMin", "wMax"}
                          )), None)
            if match is None:
                raise ValueError(f"No JSON configuration maps to {mh}")
            for key, value in match.items():
                if params.get(key) != str(value):
                    raise ValueError(f"Parameter mismatch at exp_id={exp_id}: {key}")
        groups[mh].append(row)

    if set(groups) != profile_names or len(profile_names) != 33:
        raise ValueError("Historical F14 configurations do not match the 33-profile configuration")
    if any(len(group) != 31 for group in groups.values()):
        raise ValueError("Every historical F14 configuration must have exactly 31 runs")

    exporter = pd.read_parquet(LEVEL1_PARQUET, columns=["id_exp", "function", "dim", "run_id"])
    exporter = exporter[(exporter["function"] == "F14") & (exporter["dim"] == 2)]
    exporter_map = dict(zip(exporter["id_exp"].astype(int), exporter["run_id"].astype(int)))
    if len(exporter_map) != EXPECTED_FULL_RUNS:
        raise ValueError("The level-1 export does not contain 1,023 unique F14 IDs")

    planned = []
    for mh, group in groups.items():
        for run_id, row in enumerate(sorted(group, key=lambda item: item[0]), start=1):
            exp_id = int(row[0])
            if exporter_map.get(exp_id) != run_id:
                raise ValueError(f"run_id mismatch between DB and level-1 export at exp_id={exp_id}")
            planned.append({
                "historical_exp_id": exp_id,
                "run_id": run_id,
                "actual_seed": int(config["seed"]) + exp_id,
                "configuration_id": configuration_id(row[2]),
                "mh": row[2],
                "experiment": row[1],
                "paramMH": row[4],
                "instance_id": int(row[10]),
                "instance_name": row[12],
                "problem_type": row[11],
                "dimension": 2,
                "optimum": float(row[13]),
                "instance_param": row[14],
                "historical_fitness": float(row[15]),
                "historical_seconds": float(row[16]),
                "historical_status": row[9],
                "max_iterations": int(ben["iteraciones"]),
                "population": int(ben["poblacion"]),
            })
    planned.sort(key=lambda item: item["historical_exp_id"])
    if len(planned) != EXPECTED_FULL_RUNS:
        raise ValueError("Planned manifest is not exactly 1,023 rows")
    return config, planned, instances[0]


def select_rows(planned: list[dict], dataset: str) -> list[dict]:
    if dataset == "full":
        return planned
    selected = [row for row in planned
                if row["run_id"] == 1 and row["mh"] in VALIDATION_CONFIGS]
    if len(selected) != len(VALIDATION_CONFIGS):
        raise ValueError("Could not select six distinct historical validation configurations")
    return selected


def create_isolated_database(db_path: Path, instance: tuple, runs: list[dict]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE instancias(
                id_instancia INTEGER PRIMARY KEY, tipo_problema TEXT, nombre TEXT,
                optimo REAL, param TEXT
            );
            CREATE TABLE experimentos(
                id_experimento INTEGER PRIMARY KEY, experimento TEXT, MH TEXT,
                binarizacion TEXT, paramMH TEXT, ML TEXT, paramML TEXT,
                ML_FS TEXT, paramML_FS TEXT, estado TEXT, fk_id_instancia INTEGER,
                FOREIGN KEY (fk_id_instancia) REFERENCES instancias(id_instancia)
            );
            CREATE TABLE resultados(
                id_resultado INTEGER PRIMARY KEY AUTOINCREMENT, fitness REAL,
                tiempoEjecucion REAL, solucion TEXT, fk_id_experimento INTEGER,
                FOREIGN KEY (fk_id_experimento) REFERENCES experimentos(id_experimento)
            );
            CREATE TABLE iteraciones(
                id_archivo INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT,
                archivo BLOB, fk_id_experimento INTEGER,
                FOREIGN KEY (fk_id_experimento) REFERENCES experimentos(id_experimento)
            );
            CREATE TABLE run_provenance(
                historical_exp_id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL,
                actual_seed INTEGER NOT NULL, configuration_id TEXT NOT NULL,
                mh TEXT NOT NULL, paramMH TEXT NOT NULL, instance_id INTEGER NOT NULL,
                instance_name TEXT NOT NULL, dimension INTEGER NOT NULL,
                historical_fitness REAL NOT NULL, historical_seconds REAL NOT NULL,
                config_sha256 TEXT NOT NULL, f14_source_sha256 TEXT NOT NULL,
                runner_sha256 TEXT NOT NULL
            );
        """)
        connection.execute("INSERT INTO instancias VALUES (?,?,?,?,?)", instance)
        config_hash, function_hash, runner_hash = map(sha256, (CONFIG_PATH, F14_SOURCE, RUNNER_SOURCE))
        for row in runs:
            connection.execute(
                "INSERT INTO experimentos VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (row["historical_exp_id"], row["experiment"], row["mh"], "N/A",
                 row["paramMH"], "", "", "", "", "pendiente", row["instance_id"]),
            )
            connection.execute(
                """INSERT INTO run_provenance VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (row["historical_exp_id"], row["run_id"], row["actual_seed"],
                 row["configuration_id"], row["mh"], row["paramMH"], row["instance_id"],
                 row["instance_name"], row["dimension"], row["historical_fitness"],
                 row["historical_seconds"], config_hash, function_hash, runner_hash),
            )
        connection.commit()
    finally:
        connection.close()


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError(f"Refusing to write empty manifest: {path}")
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def prepare(dataset: str) -> None:
    config, planned, instance = load_and_validate_archive()
    out = OUTPUTS[dataset]
    if out.exists():
        raise FileExistsError(f"Refusing to overwrite existing output: {out}")
    if dataset == "full":
        validation_report = OUTPUTS["validation"] / "validation_report.json"
        if not validation_report.exists():
            raise RuntimeError("Full F14 preparation blocked: validation run has not passed")
        report = json.loads(validation_report.read_text(encoding="utf-8"))
        if (report.get("passed") is not True
                or report.get("config_sha256") != sha256(CONFIG_PATH)
                or report.get("f14_source_sha256") != sha256(F14_SOURCE)
                or report.get("runner_sha256") != sha256(RUNNER_SOURCE)):
            raise RuntimeError("Full F14 preparation blocked: validation evidence is stale or failed")
    selected = select_rows(planned, dataset)
    source_hashes = {
        "config_sha256": sha256(CONFIG_PATH),
        "f14_source_sha256": sha256(F14_SOURCE),
        "runner_sha256": sha256(RUNNER_SOURCE),
    }
    selected = [{**row, **source_hashes} for row in selected]
    out.mkdir(parents=True)
    (out / "config_used.json").write_bytes(CONFIG_PATH.read_bytes())
    write_csv(out / "planned_run_manifest.csv", selected)
    create_isolated_database(out / "BD" / "resultados.db", instance, selected)
    summary = {
        "dataset": dataset,
        "planned_runs": len(selected),
        "expected_runs": EXPECTED_FULL_RUNS if dataset == "full" else len(VALIDATION_CONFIGS),
        "configurations": len({row["mh"] for row in selected}),
        "runs_per_configuration": {key: sum(row["mh"] == key for row in selected)
                                    for key in sorted({row["mh"] for row in selected})},
        "seed_formula": "42 + historical_exp_id",
        "seed_min": min(row["actual_seed"] for row in selected),
        "seed_max": max(row["actual_seed"] for row in selected),
        "workers": int(config["parallel_workers"]),
        "iterations": int(config["experimentos"]["BEN"]["iteraciones"]),
        "population": int(config["experimentos"]["BEN"]["poblacion"]),
        "config_sha256": sha256(CONFIG_PATH),
        "f14_source_sha256": sha256(F14_SOURCE),
        "runner_sha256": sha256(RUNNER_SOURCE),
        "historical_database": str(ARCHIVE_DB),
        "isolated_database": str(out / "BD" / "resultados.db"),
    }
    (out / "preflight.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Prepared only; no experiment was executed.")


def verify(dataset: str) -> None:
    out = OUTPUTS[dataset]
    manifest_path = out / "planned_run_manifest.csv"
    db_path = out / "BD" / "resultados.db"
    if not manifest_path.exists() or not db_path.exists():
        raise FileNotFoundError(f"Missing isolated {dataset} manifest or database")
    manifest = pd.read_csv(manifest_path)
    expected = EXPECTED_FULL_RUNS if dataset == "full" else len(VALIDATION_CONFIGS)
    if len(manifest) != expected or manifest["historical_exp_id"].duplicated().any():
        raise ValueError("Manifest count or historical-ID uniqueness check failed")
    if not np.array_equal(manifest["actual_seed"].to_numpy(), 42 + manifest["historical_exp_id"].to_numpy()):
        raise ValueError("Manifest seeds do not equal 42 + historical_exp_id")
    for path, column in ((CONFIG_PATH, "config_sha256"), (F14_SOURCE, "f14_source_sha256"),
                         (RUNNER_SOURCE, "runner_sha256")):
        expected_hash = str(manifest[column].iloc[0]) if column in manifest.columns else None
        if expected_hash and expected_hash != sha256(path):
            raise ValueError(f"Source changed after preparation: {path}")

    connection = sqlite3.connect(db_path)
    try:
        status = connection.execute(
            "SELECT id_experimento,estado FROM experimentos ORDER BY id_experimento"
        ).fetchall()
        results = connection.execute(
            """SELECT e.id_experimento,r.fitness,r.tiempoEjecucion
               FROM experimentos e LEFT JOIN resultados r
               ON r.fk_id_experimento=e.id_experimento ORDER BY e.id_experimento"""
        ).fetchall()
        iteration_rows = connection.execute(
            "SELECT fk_id_experimento,archivo FROM iteraciones ORDER BY fk_id_experimento"
        ).fetchall()
        provenance = connection.execute(
            "SELECT historical_exp_id,run_id,actual_seed,configuration_id,instance_id,instance_name,dimension "
            "FROM run_provenance ORDER BY historical_exp_id"
        ).fetchall()
    finally:
        connection.close()
    expected_ids = set(manifest["historical_exp_id"].astype(int))
    if len(status) != expected or {row[0] for row in status} != expected_ids:
        raise ValueError("Experiment row count or ID set does not match manifest")
    if any(row[1] != "terminado" for row in status):
        raise ValueError("One or more scheduled experiments did not finish")
    if len(results) != expected or any(row[1] is None or not math.isfinite(row[1])
                                      or row[2] is None or not math.isfinite(row[2]) for row in results):
        raise ValueError("Missing or non-finite corrected result")
    if len(iteration_rows) != expected or {row[0] for row in iteration_rows} != expected_ids:
        raise ValueError("Missing or duplicate iteration log blobs")
    if len(provenance) != expected:
        raise ValueError("Run-provenance row count mismatch")
    for exp_id, run_id, seed, cfg_id, inst_id, instance, dimension in provenance:
        planned_row = manifest[manifest["historical_exp_id"].eq(exp_id)].iloc[0]
        if (seed != 42 + exp_id or run_id != int(planned_row["run_id"])
                or cfg_id != planned_row["configuration_id"] or inst_id != int(planned_row["instance_id"])
                or instance != "F14" or dimension != 2):
            raise ValueError(f"Run provenance mismatch for historical exp_id={exp_id}")

    passed = {
        "passed": True,
        "dataset": dataset,
        "completed_runs": expected,
        "configurations": int(manifest["configuration_id"].nunique()),
        "run_ids_per_configuration": sorted(manifest.groupby("configuration_id")["run_id"].nunique().unique().tolist()),
        "unique_historical_ids": int(manifest["historical_exp_id"].nunique()),
        "unique_seeds": int(manifest["actual_seed"].nunique()),
        "corrected_source_hash_matches": sha256(F14_SOURCE) == str(manifest["f14_source_sha256"].iloc[0]),
        "config_sha256": sha256(CONFIG_PATH),
        "f14_source_sha256": sha256(F14_SOURCE),
        "runner_sha256": sha256(RUNNER_SOURCE),
    }
    report_path = out / "validation_report.json"
    if report_path.exists():
        raise FileExistsError(f"Refusing to overwrite validation evidence: {report_path}")
    report_path.write_text(json.dumps(passed, indent=2), encoding="utf-8")
    print(json.dumps(passed, indent=2))

    if dataset == "full":
        create_final_exports(out, manifest)


def create_final_exports(out: Path, manifest: pd.DataFrame) -> None:
    connection = sqlite3.connect(out / "BD" / "resultados.db")
    try:
        results = pd.read_sql_query(
             """SELECT p.historical_exp_id,r.fitness AS corrected_fitness,
                 r.tiempoEjecucion AS corrected_seconds,e.estado
             FROM run_provenance p
             JOIN experimentos e ON e.id_experimento=p.historical_exp_id
               JOIN resultados r ON r.fk_id_experimento=e.id_experimento
               ORDER BY p.historical_exp_id""", connection
        )
    finally:
        connection.close()
    joined = manifest.merge(results, on="historical_exp_id", validate="one_to_one")
    joined["gap_final"] = [max(0.0, (f - opt) / max(abs(opt), 1.0))
                           for f, opt in zip(joined["corrected_fitness"], joined["optimum"])]
    joined["id_exp"] = joined["historical_exp_id"]
    joined["function"] = "F14"
    joined["dim"] = 2
    joined["exp_name"] = "F14 2"
    joined["mh_family"] = np.where(joined["mh"].eq("PSO"), "PSO", "PSO_FCS")
    joined["output_set"] = np.where(joined["mh"].eq("PSO"), "-", "O1")
    joined["input_set"] = np.where(joined["mh"].eq("PSO"), "-", "I1")
    joined["n_labels"] = pd.to_numeric(joined["mh"].str.extract(r":(\d+):", expand=False), errors="coerce")
    joined["rule_set"] = joined["mh"].str.extract(r":(R\d+)$", expand=False).fillna("-")
    joined["mh_raw"] = np.where(
        joined["mh"].eq("PSO"), "PSO",
        "PSO_FCS:G" + joined["n_labels"].astype("Int64").astype(str)
        + ":I1:" + joined["rule_set"] + ":O1",
    )
    joined["fitness_best"] = joined["corrected_fitness"]
    joined["t_exec"] = joined["corrected_seconds"]
    joined["optimum"] = 1.0
    joined["seed"] = joined["actual_seed"]
    joined["estado"] = "terminado"

    level1_columns = [
        "id_exp", "mh_raw", "mh_family", "output_set", "n_labels", "input_set",
        "rule_set", "exp_name", "function", "dim", "optimum", "run_id", "seed",
        "fitness_best", "gap_final", "t_exec", "estado", "actual_seed",
        "configuration_id", "instance_id", "historical_exp_id", "f14_source_sha256",
    ]
    final_path = out / "corrected_f14_level1.csv"
    comparison_path = out / "historical_vs_corrected_by_config.csv"
    summary_path = out / "final_execution_summary.json"
    for path in (final_path, comparison_path, summary_path):
        if path.exists():
            raise FileExistsError(f"Refusing to overwrite result: {path}")
    joined[level1_columns].to_csv(final_path, index=False)

    comparison = joined.groupby("configuration_id").agg(
        n_runs=("historical_exp_id", "size"),
        historical_mean=("historical_fitness", "mean"),
        corrected_mean=("corrected_fitness", "mean"),
        historical_median=("historical_fitness", "median"),
        corrected_median=("corrected_fitness", "median"),
        historical_sd=("historical_fitness", "std"),
        corrected_sd=("corrected_fitness", "std"),
        historical_best=("historical_fitness", "min"),
        corrected_best=("corrected_fitness", "min"),
    ).reset_index()
    comparison["mean_delta_corrected_minus_historical"] = (
        comparison["corrected_mean"] - comparison["historical_mean"]
    )
    comparison_path.write_text(comparison.to_csv(index=False), encoding="utf-8")
    summary = {
        "completed_runs": len(joined),
        "configurations": int(joined["configuration_id"].nunique()),
        "runs_per_configuration": sorted(joined.groupby("configuration_id").size().unique().tolist()),
        "failures": int(joined["estado"].ne("terminado").sum()),
        "historical_id_min": int(joined["historical_exp_id"].min()),
        "historical_id_max": int(joined["historical_exp_id"].max()),
        "seed_formula": "42 + historical_exp_id",
        "seed_min": int(joined["actual_seed"].min()),
        "seed_max": int(joined["actual_seed"].max()),
        "database": str(out / "BD" / "resultados.db"),
        "level1_dataset": str(final_path),
        "comparison": str(comparison_path),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


def recover_interrupted_full_run() -> None:
    out = OUTPUTS["full"]
    db_path = out / "BD" / "resultados.db"
    manifest_path = out / "planned_run_manifest.csv"
    backup_path = out / "BD" / "resultados_pre_resume_20261014.db"
    partial_backup = out / "partial_attempt_1"
    recovery_report = out / "recovery_20261014.json"
    if any(not path.exists() for path in (db_path, manifest_path)):
        raise FileNotFoundError("Full isolated run is missing its database or manifest")
    if any(path.exists() for path in (backup_path, partial_backup, recovery_report)):
        raise FileExistsError("Recovery outputs already exist; refusing to overwrite")
    manifest = pd.read_csv(manifest_path).set_index("historical_exp_id")

    source = sqlite3.connect(db_path)
    try:
        stuck = source.execute(
            """SELECT e.id_experimento,e.MH,p.run_id,p.actual_seed,p.configuration_id
               FROM experimentos e JOIN run_provenance p
               ON p.historical_exp_id=e.id_experimento
               WHERE e.estado='ejecutando' ORDER BY e.id_experimento"""
        ).fetchall()
        partial_rows = source.execute(
            """SELECT e.id_experimento,COUNT(DISTINCT r.id_resultado),
                      COUNT(DISTINCT i.id_archivo)
               FROM experimentos e
               LEFT JOIN resultados r ON r.fk_id_experimento=e.id_experimento
               LEFT JOIN iteraciones i ON i.fk_id_experimento=e.id_experimento
               WHERE e.estado='ejecutando' GROUP BY e.id_experimento"""
        ).fetchall()
        states = dict(source.execute("SELECT estado,COUNT(*) FROM experimentos GROUP BY estado"))
        if (len(stuck) != 6 or len(partial_rows) != 6
                or any(result_count or iteration_count for _, result_count, iteration_count in partial_rows)):
            raise ValueError("Expected exactly six executing rows with no persisted result/blob")
        if states.get("terminado") != 690 or states.get("pendiente") != 327:
            raise ValueError(f"Unexpected recovery state distribution: {states}")
        for exp_id, mh, run_id, seed, cfg in stuck:
            row = manifest.loc[int(exp_id)]
            if (row["mh"] != mh or int(row["run_id"]) != run_id
                    or int(row["actual_seed"]) != seed
                    or row["configuration_id"] != cfg or seed != 42 + exp_id):
                raise ValueError(f"Interrupted row no longer matches manifest: {exp_id}")

        backup = sqlite3.connect(backup_path)
        try:
            source.backup(backup)
        finally:
            backup.close()
        source.execute("BEGIN IMMEDIATE")
        updated = source.executemany(
            "UPDATE experimentos SET estado='pendiente' WHERE id_experimento=? AND estado='ejecutando'",
            [(int(row[0]),) for row in stuck],
        )
        if updated.rowcount != 6:
            source.rollback()
            raise RuntimeError(f"Expected to requeue 6 rows, updated {updated.rowcount}")
        source.commit()
    finally:
        source.close()

    partial_backup.mkdir()
    archived_files = []
    transient = out / "Resultados" / "Transitorio"
    if transient.exists():
        for exp_id, mh, _, _, _ in stuck:
            names = (f"PSO_F14_{exp_id}.csv", f"PSO_F14_{exp_id}_divj.csv") if mh == "PSO" else (
                f"PSO_FCS_F14_{exp_id}.csv", f"PSO_FCS_F14_{exp_id}_divj.csv"
            )
            for name in names:
                candidate = transient / name
                if candidate.exists():
                    shutil.copy2(candidate, partial_backup / name)
                    archived_files.append(name)
    recovery_report.write_text(json.dumps({
        "recovered_at": "2026-10-14",
        "requeued_historical_ids": [int(row[0]) for row in stuck],
        "actual_seeds": [int(row[3]) for row in stuck],
        "rows_with_prior_result_or_blob": 0,
        "finished_rows_preserved": 690,
        "pending_rows_before_recovery": 327,
        "rows_requeued": 6,
        "pre_resume_database_backup": str(backup_path),
        "partial_transient_files_copied": archived_files,
        "partial_file_archive": str(partial_backup),
    }, indent=2), encoding="utf-8")
    print(recovery_report.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight", "prepare", "verify", "recover"))
    parser.add_argument("dataset", choices=("validation", "full"))
    args = parser.parse_args()
    if args.mode == "preflight":
        config, planned, _ = load_and_validate_archive()
        print(json.dumps({
            "passed": True,
            "historical_runs": len(planned),
            "configurations": len({row["mh"] for row in planned}),
            "runs_per_configuration": sorted(Counter(row["mh"] for row in planned).values()),
            "historical_ids_unique": len({row["historical_exp_id"] for row in planned}) == EXPECTED_FULL_RUNS,
            "seed_formula": "42 + historical_exp_id",
            "historical_seed_min": min(row["actual_seed"] for row in planned),
            "historical_seed_max": max(row["actual_seed"] for row in planned),
            "workers": config["parallel_workers"],
            "iterations": config["experimentos"]["BEN"]["iteraciones"],
            "population": config["experimentos"]["BEN"]["poblacion"],
            "config_sha256": sha256(CONFIG_PATH),
            "f14_source_sha256": sha256(F14_SOURCE),
            "runner_sha256": sha256(RUNNER_SOURCE),
        }, indent=2))
    elif args.mode == "prepare":
        prepare(args.dataset)
    elif args.mode == "recover":
        if args.dataset != "full":
            raise ValueError("Only the full F14 dataset supports interrupted-run recovery")
        recover_interrupted_full_run()
    else:
        verify(args.dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())