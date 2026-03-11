import pandas as pd
from analysis_modules.level2_aggregated import plot_evolution_by_variable

print("Generando gráficos de w...")
try:
    plot_evolution_by_variable('w', verbose=True)
    print("✓ Completado")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
