import importlib

reiniciarDB_mod = importlib.import_module('0_1_reiniciarDB')
limpiarEntorno_mod = importlib.import_module('0_2_limpiarEntorno')

reiniciarDB = reiniciarDB_mod.reiniciarDB
limpiarEntorno = limpiarEntorno_mod.limpiarEntorno

reiniciarDB()
limpiarEntorno()