"""Integridad Phase 4: counts, NaN/Inf, w range, cobertura por (instancia, MH)."""
import sqlite3
import io
import math
import csv
import random

con = sqlite3.connect('BD/resultados.db')
cur = con.cursor()

print('=' * 60)
print('Integridad batch Phase 4 (read-only)')
print('=' * 60)

# Counts
n_exp = cur.execute('SELECT COUNT(*) FROM experimentos').fetchone()[0]
n_res = cur.execute('SELECT COUNT(*) FROM resultados').fetchone()[0]
n_it  = cur.execute('SELECT COUNT(*) FROM iteraciones').fetchone()[0]
n_ins = cur.execute('SELECT COUNT(*) FROM instancias').fetchone()[0]
print(f'\nTablas:')
print(f'  instancias:   {n_ins}')
print(f'  experimentos: {n_exp}')
print(f'  resultados:   {n_res}   {"OK" if n_res == n_exp else "MISMATCH"}')
print(f'  iteraciones:  {n_it}   {"OK" if n_it == n_exp else "MISMATCH"}')

# NaN/Inf
nan_cnt = inf_cnt = 0
for (f,) in cur.execute('SELECT fitness FROM resultados'):
    if f is None or math.isnan(f):
        nan_cnt += 1
    elif math.isinf(f):
        inf_cnt += 1
print(f'\nFitness sanity:')
print(f'  NaN: {nan_cnt}    Inf: {inf_cnt}')

# Fitness stats overall
mn, mx, avg = cur.execute('SELECT MIN(fitness), MAX(fitness), AVG(fitness) FROM resultados').fetchone()
print(f'  min={mn:.4e}  max={mx:.4e}  avg={avg:.4e}')

# Distribucion por MH
print(f'\nExperimentos por MH:')
for mh, c in cur.execute('SELECT MH, COUNT(*) FROM experimentos GROUP BY MH ORDER BY MH'):
    print(f'  {mh:35s} {c}')

# Cobertura: cada (instancia, MH) deberia tener 31 runs
print(f'\nCobertura runs por (instancia, MH) (esperado=31):')
rows = cur.execute("""
    SELECT fk_id_instancia, MH, COUNT(*)
    FROM experimentos
    GROUP BY fk_id_instancia, MH
""").fetchall()
mismatches = [(inst, mh, c) for inst, mh, c in rows if c != 31]
print(f'  celdas totales:     {len(rows)}')
print(f'  celdas con !=31:    {len(mismatches)}')
if mismatches[:5]:
    for inst, mh, c in mismatches[:5]:
        print(f'    inst={inst} MH={mh} count={c}')

# w range: muestra 30 experimentos PSO_FCS al azar y verifica w in [0.1, 0.9]
print(f'\nMuestreo w range (30 PSO_FCS al azar):')
ids = [r[0] for r in cur.execute("SELECT id_experimento FROM experimentos WHERE MH LIKE 'PSO_FCS%'").fetchall()]
random.seed(0)
sample_ids = random.sample(ids, 30)
w_min = float('inf')
w_max = float('-inf')
n_iters_checked = 0
n_exp_ok = 0
n_exp_no_w = 0
for eid in sample_ids:
    row = cur.execute('SELECT archivo FROM iteraciones WHERE fk_id_experimento=?', (eid,)).fetchone()
    if not row:
        continue
    blob = row[0]
    text = blob.decode('utf-8') if isinstance(blob, (bytes, bytearray)) else blob
    reader = csv.DictReader(io.StringIO(text))
    if 'w' not in reader.fieldnames:
        n_exp_no_w += 1
        continue
    n_exp_ok += 1
    for r in reader:
        try:
            w = float(r['w'])
        except (ValueError, TypeError):
            continue
        if math.isnan(w) or math.isinf(w):
            continue
        w_min = min(w_min, w)
        w_max = max(w_max, w)
        n_iters_checked += 1
print(f'  exps con columna w: {n_exp_ok}/30    sin w: {n_exp_no_w}')
print(f'  iteraciones muestreadas: {n_iters_checked}')
print(f'  w range: [{w_min:.4f}, {w_max:.4f}]')
print(f'  w in [0.1, 0.9]? {0.1 <= w_min and w_max <= 0.9}')

con.close()
print('\n' + '=' * 60)
