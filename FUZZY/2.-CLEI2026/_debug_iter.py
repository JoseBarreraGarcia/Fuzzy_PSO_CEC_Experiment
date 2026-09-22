"""Debug: count runs per (func, MH) in iteraciones and replicate final stats."""
import sqlite3, io
import numpy as np
import pandas as pd

con = sqlite3.connect(r'BD/resultados_clei2026_backup.db')
cur = con.cursor()
BEST = {'F21':'PSO_FCS:A:5:I2','F22':'PSO_FCS:A:3:I1','F23':'PSO_FCS:A:3:I2'}

for func in ['F21','F22','F23']:
    ins = cur.execute("SELECT id_instancia FROM instancias WHERE nombre=?", (func,)).fetchone()[0]
    print(f'\n=== {func} ===')
    for mh in ['PSO', BEST[func]]:
        exps = [r[0] for r in cur.execute(
            "SELECT id_experimento FROM experimentos WHERE fk_id_instancia=? AND MH=?", (ins, mh)).fetchall()]
        finals_iter = []
        n_with_iter = 0
        for e in exps:
            blob = cur.execute("SELECT archivo FROM iteraciones WHERE fk_id_experimento=? LIMIT 1", (e,)).fetchone()
            if blob is None:
                continue
            n_with_iter += 1
            raw = blob[0]
            txt = raw.decode('utf-8', 'replace') if isinstance(raw, (bytes, bytearray)) else str(raw)
            df = pd.read_csv(io.StringIO(txt))
            finals_iter.append(df['best_fitness'].iloc[-1])
        arr = np.array(finals_iter)
        print(f'  {mh:25s}  n_exp={len(exps)}  with_iter={n_with_iter}  '
              f'final.mean={arr.mean():+.4f}  final.median={np.median(arr):+.4f}  '
              f'std={arr.std():.4f}  min={arr.min():+.4f}  max={arr.max():+.4f}')
