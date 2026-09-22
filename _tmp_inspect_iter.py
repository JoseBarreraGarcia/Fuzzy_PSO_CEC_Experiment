import sqlite3, io
con = sqlite3.connect('BD/resultados_clei2026_backup.db')
cur = con.cursor()
print("TABLES:")
for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'"):
    print(" ", r)
print("\nIteraciones schema:")
for r in cur.execute('PRAGMA table_info(iteraciones)'):
    print(" ", r)
print("\nExperimentos schema:")
for r in cur.execute('PRAGMA table_info(experimentos)'):
    print(" ", r)
print("\nSample iteraciones (no BLOB):")
for r in cur.execute('SELECT id_archivo, nombre, fk_id_experimento FROM iteraciones LIMIT 5'):
    print(" ", r)
print("\nSample experimentos:")
for r in cur.execute('SELECT id_experimento, experimento, MH, paramMH FROM experimentos LIMIT 5'):
    print(" ", r)
print("\nDistinct MH:")
for r in cur.execute('SELECT DISTINCT MH FROM experimentos'):
    print(" ", r)
print("\nFirst BLOB head:")
row = cur.execute('SELECT archivo FROM iteraciones LIMIT 1').fetchone()
if row:
    blob = row[0]
    print(" size:", len(blob))
    # try decode
    try:
        text = blob.decode('utf-8', errors='replace')[:600]
        print(" head:\n", text)
    except Exception as e:
        print(" err:", e)
