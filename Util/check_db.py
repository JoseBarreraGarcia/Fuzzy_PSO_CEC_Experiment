import sqlite3
import os

db_path = 'BD/base_datos.db'
if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f'DB exists, size: {size} bytes')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in c.fetchall()]
    print(f'Tables: {tables}')
    if 'experimentos' in tables:
        c.execute('SELECT COUNT(*) FROM experimentos')
        count = c.fetchone()[0]
        print(f'Experimentos count: {count}')
        c.execute('SELECT id, nombre_mh, runs FROM experimentos LIMIT 5')
        for row in c.fetchall():
            print(f'  {row}')
    conn.close()
else:
    print('DB does not exist')
