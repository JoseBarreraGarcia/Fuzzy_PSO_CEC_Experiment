import sqlite3

conn = sqlite3.connect('BD/resultados.db')
cursor = conn.cursor()

# Consultar experimentos a eliminar
cursor.execute("SELECT COUNT(*) FROM experimentos WHERE id_experimento >= 869 AND estado='terminado'")
count = cursor.fetchone()[0]

if count > 0:
    print(f"Se van a eliminar {count} experimentos con id >= 869 en estado 'terminado'")
    confirm = input("¿Confirmas? (s/n): ")
    
    if confirm.lower() == 's':
        cursor.execute("DELETE FROM experimentos WHERE id_experimento >= 869 AND estado='terminado'")
        conn.commit()
        print(f"✓ {count} experimentos eliminados")
    else:
        print("Operación cancelada")
else:
    print("No hay experimentos pendientes con id >= 869")

conn.close()