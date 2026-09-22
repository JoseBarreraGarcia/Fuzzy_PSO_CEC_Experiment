import sqlite3, io
con = sqlite3.connect(r'BD/resultados_clei2026_backup.db')
cur = con.cursor()
print('TABLES:', cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall())
print('iter cols:', cur.execute('PRAGMA table_info(iteraciones)').fetchall())
print('exp cols:', cur.execute('PRAGMA table_info(experimentos)').fetchall())
print('ins F2x:')
for r in cur.execute("SELECT id_instancia,tipo_problema,nombre FROM instancias WHERE nombre LIKE 'F2%'").fetchall():
    print(' ', r)
print('exp MH distinct:')
for r in cur.execute("SELECT DISTINCT MH FROM experimentos").fetchall():
    print(' ', r)
print('exp paramMH samples for one F21 PSO_FCS:')
ins = cur.execute("SELECT id_instancia FROM instancias WHERE nombre='F21' LIMIT 1").fetchone()
if ins:
    rows = cur.execute("SELECT id_experimento,MH,paramMH FROM experimentos WHERE fk_id_instancia=? LIMIT 5", (ins[0],)).fetchall()
    for r in rows: print(' ', r)
    # check one CSV
    one = cur.execute("SELECT id_experimento FROM experimentos WHERE fk_id_instancia=? AND MH='PSO' LIMIT 1", (ins[0],)).fetchone()
    if one:
        blob = cur.execute("SELECT nombre, length(archivo) FROM iteraciones WHERE fk_id_experimento=? LIMIT 1", (one[0],)).fetchone()
        print('one iter blob:', blob)
        raw = cur.execute("SELECT archivo FROM iteraciones WHERE fk_id_experimento=? LIMIT 1", (one[0],)).fetchone()
        if raw:
            txt = raw[0].decode('utf-8', errors='replace') if isinstance(raw[0], bytes) else str(raw[0])
            print('--- first 600 chars of CSV ---')
            print(txt[:600])
