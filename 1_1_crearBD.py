import os
import sqlite3

from BD.sqlite import BD

bd = BD()


def _instancias_vacias_o_inexistentes():
    """Verifica si la base está creada pero sin instancias (o con tabla faltante)."""

    try:
        bd.conectar()
        cursor = bd.getCursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instancias'")

        if cursor.fetchone() is None:
            return True

        cursor.execute("SELECT COUNT(*) FROM instancias")
        count = cursor.fetchone()[0]

        return count == 0
    except sqlite3.Error:
        # Si hay cualquier problema leyendo, forzar reconstrucción para garantizar consistencia.
        return True
    finally:
        try:
            bd.desconectar()
        except Exception:
            pass


def crear_BD():
    db_path = './BD/resultados.db'

    if not os.path.exists(db_path):
        print("La base de datos no existe, se procederá a crearla.")
        bd.construirTablas()
        print("Base de datos creada y poblada exitosamente.")
        return

    if _instancias_vacias_o_inexistentes():
        print("La base de datos existe pero no tiene instancias; se recrearán las tablas base.")
        bd.construirTablas()
        print("Base de datos poblada exitosamente.")


if __name__ == '__main__':
    crear_BD()