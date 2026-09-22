"""
Limpia el contenido del directorio FUZZY/plots/

Elimina todos los archivos PNG generados por 1_generate_fuzzy_plots.py
sin eliminar el directorio en sí.

Uso:
  python 0_limpiar_fuzzy_plots.py
"""

import os
import glob

def limpiar_plots():
    plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plots')
    
    if not os.path.exists(plots_dir):
        print(f"[OK] Directory does not exist: {plots_dir}")
        return 0
    
    files = glob.glob(os.path.join(plots_dir, '*'))
    count = 0
    for f in files:
        if os.path.isfile(f):
            os.remove(f)
            count += 1
    
    print(f"[OK] Deleted {count} files from {plots_dir}")
    return count


if __name__ == '__main__':
    limpiar_plots()
