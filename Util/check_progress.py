"""Progreso del batch Phase 4: cuenta estados, calcula ETA y rate."""
import sqlite3
import os
import time
from datetime import datetime, timedelta

PID_FILE = 'Resultados/full_run.pid'
LOG_FILE = 'Resultados/full_run.log'
DB_FILE = 'BD/resultados.db'

# Start time from PID file mtime (cuando se lanzo)
if os.path.exists(PID_FILE):
    start_ts = os.path.getmtime(PID_FILE)
    start_dt = datetime.fromtimestamp(start_ts)
else:
    start_dt = None

now = datetime.now()

con = sqlite3.connect(DB_FILE)
cur = con.cursor()

total = cur.execute('SELECT COUNT(*) FROM experimentos').fetchone()[0]
by_state = dict(cur.execute('SELECT estado, COUNT(*) FROM experimentos GROUP BY estado').fetchall())

done = by_state.get('terminado', 0)
running = by_state.get('ejecutando', 0)
pending = by_state.get('pendiente', 0)
errored = by_state.get('error', 0)

# Tiempo de ejecucion total por experimento -> sumar tiempo real reportado
# Esto evita contar tiempos de espera entre workers.
sum_time = cur.execute('SELECT COALESCE(SUM(tiempoEjecucion), 0) FROM resultados').fetchone()[0]

con.close()

print('=' * 60)
print(f'Batch Phase 4 progress @ {now.strftime("%Y-%m-%d %H:%M:%S")}')
print('=' * 60)
print(f'Total experimentos:  {total}')
print(f'  terminado:         {done:>6}  ({100*done/total:5.2f}%)')
print(f'  ejecutando:        {running:>6}')
print(f'  pendiente:         {pending:>6}')
print(f'  error:             {errored:>6}')
print()

if start_dt:
    elapsed = now - start_dt
    elapsed_s = elapsed.total_seconds()
    print(f'Iniciado:           {start_dt.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'Transcurrido:       {str(elapsed).split(".")[0]}  ({elapsed_s/3600:.2f} h)')

    if done > 0:
        # Rate basado en wall-clock vs experimentos terminados
        rate_wall = done / elapsed_s  # exps/s (paralelo)
        remaining = total - done
        eta_s = remaining / rate_wall if rate_wall > 0 else 0
        eta_dt = now + timedelta(seconds=eta_s)
        print(f'Rate (wall, par):   {rate_wall*3600:.1f} exp/h  ({rate_wall*60:.2f} exp/min)')
        print(f'Restantes:          {remaining}')
        print(f'ETA wall:           {timedelta(seconds=int(eta_s))}  -> {eta_dt.strftime("%Y-%m-%d %H:%M:%S")}')
        # Tiempo promedio por exp (CPU acumulado de los solvers)
        avg_solver = sum_time / done
        print(f'Avg solver time/exp:{avg_solver:.2f} s (CPU por exp; total acumulado: {sum_time/3600:.2f} h)')

# Log tail
print()
print('--- Log tail (10 lines) ---')
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    for ln in lines[-10:]:
        print(ln.rstrip())
