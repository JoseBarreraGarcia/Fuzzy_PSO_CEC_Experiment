"""
Block B1 (CLEI2026): Rule activation frequency analysis.

For each (input_set, granularity) configuration, replays the actual (diversity,
progress) trajectories logged in BD/resultados_clei2026_backup.db and computes,
for each Mamdani rule, the mean (normalized) firing strength. Also reports the
effective number of active rules per sample (exp of Shannon entropy of firing
distribution), which quantifies how blurred the control signal is.

Input MFs and rules are inlined to match exactly the parameters reported in the
manuscript (Table tab:input_sets_3L and Tables tab:rules3 / tab:rules5).
"""
import io
import os
import sqlite3

import numpy as np
import pandas as pd

DB = "BD/resultados_clei2026_backup.db"
OUT_DIR = "Resultados/clei2026_b1"
os.makedirs(OUT_DIR, exist_ok=True)


def tri(x, a, b, c):
    x = float(x)
    if a == b and x <= b:
        return 1.0
    if b == c and x >= b:
        return 1.0
    if x <= a or x >= c:
        return 0.0
    if a < x < b:
        return (x - a) / (b - a + 1e-12)
    if b < x < c:
        return (c - x) / (c - b + 1e-12)
    return 1.0 if x == b else 0.0


INPUT_MFS_3L = {
    "I1": {"low": (0.0, 0.2, 0.4), "medium": (0.3, 0.5, 0.7), "high": (0.6, 0.8, 1.0)},
    "I2": {"low": (0.0, 0.16, 0.33), "medium": (0.33, 0.5, 0.66), "high": (0.66, 0.84, 1.0)},
    "I3": {"low": (0.0, 0.25, 0.5), "medium": (0.25, 0.5, 0.75), "high": (0.5, 0.75, 1.0)},
    "I4": {"low": (0.0, 0.0, 0.35), "medium": (0.2, 0.5, 0.8), "high": (0.65, 1.0, 1.0)},
}
DIV_LABELS_3L = ["low", "medium", "high"]
PROGRESS_LABELS_3L = ["early", "mid", "late"]

INPUT_MFS_5L = {
    "I1": {"very_low": (0.0, 0.15, 0.3), "low": (0.2, 0.35, 0.5),
           "medium": (0.35, 0.5, 0.65), "high": (0.5, 0.65, 0.8),
           "very_high": (0.7, 0.85, 1.0)},
    "I2": {"very_low": (0.0, 0.1, 0.2), "low": (0.2, 0.3, 0.4),
           "medium": (0.4, 0.5, 0.6), "high": (0.6, 0.7, 0.8),
           "very_high": (0.8, 0.9, 1.0)},
    "I3": {"very_low": (0.0, 0.15, 0.35), "low": (0.15, 0.3, 0.5),
           "medium": (0.3, 0.5, 0.7), "high": (0.5, 0.7, 0.85),
           "very_high": (0.65, 0.85, 1.0)},
    "I4": {"very_low": (0.0, 0.0, 0.25), "low": (0.15, 0.3, 0.45),
           "medium": (0.35, 0.5, 0.65), "high": (0.55, 0.7, 0.85),
           "very_high": (0.75, 1.0, 1.0)},
}
DIV_LABELS_5L = ["very_low", "low", "medium", "high", "very_high"]
PROGRESS_LABELS_5L = ["very_early", "early", "mid", "late", "very_late"]


def aggregate(con, mh_name, num_labels, input_set):
    if num_labels == 3:
        div_mfs = INPUT_MFS_3L[input_set]
        prog_mfs = {p: div_mfs[d] for p, d in zip(PROGRESS_LABELS_3L, DIV_LABELS_3L)}
        prog_labels, div_labels = PROGRESS_LABELS_3L, DIV_LABELS_3L
    else:
        div_mfs = INPUT_MFS_5L[input_set]
        prog_mfs = {p: div_mfs[d] for p, d in zip(PROGRESS_LABELS_5L, DIV_LABELS_5L)}
        prog_labels, div_labels = PROGRESS_LABELS_5L, DIV_LABELS_5L

    rules = [(p, d) for p in prog_labels for d in div_labels]
    n_rules = len(rules)
    sum_firing = np.zeros(n_rules)
    n_samples = 0
    entropies = []

    cur = con.cursor()
    blobs = cur.execute(
        """SELECT i.archivo FROM iteraciones i
           JOIN experimentos e ON i.fk_id_experimento = e.id_experimento
           WHERE e.MH = ?""",
        (mh_name,),
    ).fetchall()

    eps = 1e-12
    for (blob,) in blobs:
        df = pd.read_csv(io.BytesIO(blob))
        T_max = int(df["iter"].max()) + 1
        iters = df["iter"].to_numpy()
        divs = df["DIV"].to_numpy() / 100.0
        t_arr = iters / float(T_max)
        for t, d in zip(t_arr, divs):
            d_c = float(np.clip(d, eps, 1.0 - eps))
            t_c = float(np.clip(t, eps, 1.0 - eps))
            mu_p = {p: tri(t_c, *prog_mfs[p]) for p in prog_labels}
            mu_d = {dl: tri(d_c, *div_mfs[dl]) for dl in div_labels}
            arr = np.array([min(mu_p[p], mu_d[dl]) for (p, dl) in rules], dtype=float)
            s = arr.sum()
            if s <= 1e-12:
                continue
            pv = arr / s
            sum_firing += pv
            nz = pv[pv > 0]
            entropies.append(-float(np.sum(nz * np.log(nz))))
            n_samples += 1

    mean_firing = sum_firing / max(n_samples, 1)
    H_mean = float(np.mean(entropies)) if entropies else 0.0
    H_std = float(np.std(entropies)) if entropies else 0.0
    ENR = float(np.exp(H_mean))
    return rules, mean_firing, H_mean, H_std, ENR, n_samples


def main():
    con = sqlite3.connect(DB)
    summary_rows, per_rule_3L, per_rule_5L = [], [], []

    for num_labels in [3, 5]:
        for inp in ["I1", "I2", "I3", "I4"]:
            mh = f"PSO_FCS:A:{num_labels}:{inp}"
            print(f"Processing {mh} ...", flush=True)
            rules, mean_firing, H, Hsd, ENR, N = aggregate(con, mh, num_labels, inp)
            summary_rows.append(dict(
                granularity=f"{num_labels}L",
                input_set=inp,
                n_samples=N,
                n_rules=len(rules),
                H_mean=H,
                H_std=Hsd,
                effective_active_rules=ENR,
                H_normalized=H / np.log(len(rules)),
            ))
            target = per_rule_3L if num_labels == 3 else per_rule_5L
            for (p, d), v in zip(rules, mean_firing):
                target.append(dict(
                    granularity=f"{num_labels}L",
                    input_set=inp,
                    progress=p,
                    diversity=d,
                    mean_firing=float(v),
                ))

    pd.DataFrame(summary_rows).to_csv(
        os.path.join(OUT_DIR, "rule_activation_summary.csv"), index=False)
    pd.DataFrame(per_rule_3L).to_csv(
        os.path.join(OUT_DIR, "rule_activation_3L_per_rule.csv"), index=False)
    pd.DataFrame(per_rule_5L).to_csv(
        os.path.join(OUT_DIR, "rule_activation_5L_per_rule.csv"), index=False)
    print("\n=== SUMMARY ===")
    print(pd.DataFrame(summary_rows).to_string(index=False))


if __name__ == "__main__":
    main()
