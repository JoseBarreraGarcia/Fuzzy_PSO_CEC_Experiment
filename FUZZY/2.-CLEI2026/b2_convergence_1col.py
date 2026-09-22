"""Generate a single-column (3-row) version of the B2 convergence figure.

Output: FUZZY/2.-CLEI2026/figures/b2_convergence_multimodal_1col.pdf
"""
import sqlite3, io
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

DB = Path('BD/resultados_clei2026_backup.db')
OUT = Path('FUZZY/2.-CLEI2026/figures/b2_convergence_multimodal_1col.pdf')

BEST_PER_FUNC = {
    'F21': 'PSO_FCS:A:5:I2',
    'F22': 'PSO_FCS:A:3:I1',
    'F23': 'PSO_FCS:A:3:I2',
}
LABEL = {
    'F21': r'F21 (Shekel $m{=}5$)',
    'F22': r'F22 (Shekel $m{=}7$)',
    'F23': r'F23 (Shekel $m{=}10$)',
}
FCS_LABEL = {
    'F21': 'FCS--A--5L--I2',
    'F22': 'FCS--A--3L--I1',
    'F23': 'FCS--A--3L--I2',
}
OPTIMUM = {'F21': -10.1532, 'F22': -10.4029, 'F23': -10.5363}


def load_traces(con, fname, mh):
    cur = con.cursor()
    ins_id = cur.execute("SELECT id_instancia FROM instancias WHERE nombre=?", (fname,)).fetchone()[0]
    rows = cur.execute(
        "SELECT id_experimento FROM experimentos WHERE fk_id_instancia=? AND MH=?",
        (ins_id, mh)).fetchall()
    traces = []
    for (exp_id,) in rows:
        blob = cur.execute(
            "SELECT archivo FROM iteraciones WHERE fk_id_experimento=? LIMIT 1",
            (exp_id,)).fetchone()
        if blob is None:
            continue
        raw = blob[0]
        txt = raw.decode('utf-8', errors='replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
        df = pd.read_csv(io.StringIO(txt))
        traces.append(df['best_fitness'].to_numpy())
    if not traces:
        return None
    L = min(len(t) for t in traces)
    return np.vstack([t[:L] for t in traces])


def main():
    con = sqlite3.connect(DB)
    plt.rcParams.update({
        'font.family': 'serif',
        'font.size': 9,
        'axes.titlesize': 9,
        'axes.labelsize': 9,
        'legend.fontsize': 8,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
    })

    fig, axes = plt.subplots(3, 1, figsize=(3.5, 6.5), sharey=False)

    for ax, func in zip(axes, ['F21', 'F22', 'F23']):
        pso = load_traces(con, func, 'PSO')
        fcs = load_traces(con, func, BEST_PER_FUNC[func])
        if pso is None or fcs is None:
            ax.text(0.5, 0.5, 'no data', ha='center', va='center', transform=ax.transAxes)
            continue

        iters = np.arange(pso.shape[1])
        for data, color, label in [
            (pso, '#1f77b4', 'PSO'),
            (fcs, '#d62728', FCS_LABEL[func]),
        ]:
            mean = data.mean(axis=0)
            sd = data.std(axis=0)
            ax.plot(iters, mean, color=color, linewidth=1.3, label=label)
            ax.fill_between(iters, mean - sd, mean + sd, color=color, alpha=0.18, linewidth=0)

        ax.axhline(OPTIMUM[func], color='gray', linestyle=':', linewidth=0.8, label='Global opt.')
        ax.set_title(LABEL[func])
        ax.set_ylabel('Best fitness\n(mean $\\pm$ std)')
        ax.grid(True, alpha=0.3, linewidth=0.4)
        ax.legend(loc='lower right', frameon=False, handlelength=1.6)

    axes[-1].set_xlabel('Iteration')
    fig.tight_layout()
    fig.savefig(OUT, dpi=300, bbox_inches='tight')
    print('Saved', OUT)


if __name__ == '__main__':
    main()
