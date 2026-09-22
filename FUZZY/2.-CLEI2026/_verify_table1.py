"""Verify final-fitness means for F21-F23: PSO vs best FCS, to cross-check Table I."""
import sqlite3
import numpy as np
from pathlib import Path

con = sqlite3.connect(r'BD/resultados_clei2026_backup.db')
cur = con.cursor()

BEST = {'F21':'PSO_FCS:A:5:I2','F22':'PSO_FCS:A:3:I1','F23':'PSO_FCS:A:3:I2'}

for func in ['F21','F22','F23']:
    ins = cur.execute("SELECT id_instancia FROM instancias WHERE nombre=?", (func,)).fetchone()[0]
    print(f'\n=== {func} (instance {ins}) ===')
    for mh in ['PSO', BEST[func]]:
        exps = [r[0] for r in cur.execute(
            "SELECT id_experimento FROM experimentos WHERE fk_id_instancia=? AND MH=?", (ins, mh)).fetchall()]
        fits = []
        for e in exps:
            row = cur.execute("SELECT fitness FROM resultados WHERE fk_id_experimento=?", (e,)).fetchone()
            if row is not None:
                fits.append(float(row[0]))
        if fits:
            arr = np.array(fits)
            print(f'  {mh:25s}  n={len(arr):2d}  mean={arr.mean():+.4f}  std={arr.std():.4f}  min={arr.min():+.4f}  max={arr.max():+.4f}')
        else:
            print(f'  {mh:25s}  NO FITNESS in resultados')
