"""Chequeo rapido: cobertura por (funcion, dim) y muestreo w range (3 exps)."""
import sqlite3
import io
import math
import csv

con = sqlite3.connect('BD/resultados.db')
cur = con.cursor()

# Estructura tabla instancias
print('Instancias BEN unicas (nombre, param):')
rows = cur.execute("""
    SELECT nombre, param, COUNT(e.id_experimento) AS n
    FROM instancias i
    LEFT JOIN experimentos e ON e.fk_id_instancia = i.id_instancia
    WHERE i.tipo_problema='BEN'
    GROUP BY i.id_instancia
    ORDER BY i.nombre, i.param
""").fetchall()
print(f'  {len(rows)} instancias BEN con experimentos')
# Cobertura por (nombre, dim) sobre 33 MHs x 31 runs = 1023 esperados
n_ok = sum(1 for _, _, n in rows if n == 1023)
n_bad = [(nm, pr, n) for nm, pr, n in rows if n != 1023]
print(f'  con count = 33 MHs x 31 runs = 1023: {n_ok}/{len(rows)}')
if n_bad:
    print(f'  ANOMALIAS:')
    for nm, pr, n in n_bad[:20]:
        print(f'    {nm:10s} param={pr!s:20s} count={n}')

# Sub-total por dim
print(f'\nExperimentos por dim (BEN):')
for dim, c in cur.execute("""
    SELECT i.param, COUNT(e.id_experimento)
    FROM experimentos e
    JOIN instancias i ON e.fk_id_instancia = i.id_instancia
    WHERE i.tipo_problema='BEN'
    GROUP BY i.param
    ORDER BY CAST(i.param AS INTEGER)
"""):
    print(f'  dim={dim:>4}: {c}')

# Total BEN
tot_ben = cur.execute("""
    SELECT COUNT(e.id_experimento)
    FROM experimentos e
    JOIN instancias i ON e.fk_id_instancia = i.id_instancia
    WHERE i.tipo_problema='BEN'
""").fetchone()[0]
print(f'\nTotal BEN: {tot_ben}')

# Muestreo w range (solo 3 experimentos para no colgar)
print(f'\nMuestreo w range (3 exps PSO_FCS al azar, 3 MHs distintos):')
sample_mhs = ['PSO_FCS:O1:3:I1:R1', 'PSO_FCS:O1:5:I1:R5', 'PSO_FCS:O1:9:I1:R8']
for mh in sample_mhs:
    eid = cur.execute(
        "SELECT id_experimento FROM experimentos WHERE MH=? ORDER BY RANDOM() LIMIT 1",
        (mh,)
    ).fetchone()[0]
    blob = cur.execute('SELECT archivo FROM iteraciones WHERE fk_id_experimento=?', (eid,)).fetchone()[0]
    text = blob.decode('utf-8') if isinstance(blob, (bytes, bytearray)) else blob
    reader = csv.DictReader(io.StringIO(text))
    if 'w' not in reader.fieldnames:
        print(f'  {mh}: sin columna w!')
        continue
    ws = []
    for r in reader:
        try:
            w = float(r['w'])
            if not (math.isnan(w) or math.isinf(w)):
                ws.append(w)
        except (ValueError, TypeError):
            pass
    print(f'  {mh:25s} exp={eid}  iters={len(ws)}  w=[{min(ws):.4f}, {max(ws):.4f}]  ok={0.1 <= min(ws) and max(ws) <= 0.9}')

con.close()
