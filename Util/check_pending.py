from BD.sqlite import BD

bd = BD()
bd.conectar()
cursor = bd.getCursor()

# Contar experimentos por estado
cursor.execute('SELECT estado, COUNT(*) as cnt FROM experimentos GROUP BY estado')
print('Experimentos por estado:')
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]}')

# Contar experimentos completados por función y MH
print('\nExperimentos completados por función y MH:')
cursor.execute('''
SELECT inst.nombre, exp.MH, COUNT(*) as cnt
FROM experimentos exp
JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
WHERE (exp.estado = 'terminado' OR exp.estado = 'completado' OR exp.estado = 'completada')
AND inst.tipo_problema = 'BEN'
GROUP BY inst.nombre, exp.MH
ORDER BY inst.nombre, exp.MH
''')
for row in cursor.fetchall():
    print(f'  {row[0]} - {row[1]}: {row[2]} runs')

# Mostrar experimentos pendientes
print('\nExperimentos pendientes:')
cursor.execute('''
SELECT inst.nombre, exp.MH, COUNT(*) as cnt
FROM experimentos exp
JOIN instancias inst ON exp.fk_id_instancia = inst.id_instancia
WHERE exp.estado = 'pendiente'
AND inst.tipo_problema = 'BEN'
GROUP BY inst.nombre, exp.MH
ORDER BY inst.nombre, exp.MH
''')
pending = cursor.fetchall()
if pending:
    for row in pending:
        print(f'  {row[0]} - {row[1]}: {row[2]} pendiente(s)')
else:
    print('  Ninguno')

bd.desconectar()
