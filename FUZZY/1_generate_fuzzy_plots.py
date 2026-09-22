"""
Generate Fuzzy Set Visualization Plots

Crea gráficos de los fuzzy sets de entrada y salida para documentación.
Se guardan en FUZZY/plots/

Configuración: config/fuzzy_plots.json

Uso:
  python 1_generate_fuzzy_plots.py
"""

from fuzzy_plots import generate_all_fuzzy_plots

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("FUZZY SET VISUALIZATION GENERATOR")
    print("  Config: config/fuzzy_plots.json")
    print("=" * 70)
    
    plots = generate_all_fuzzy_plots(verbose=True)
    
    print(f"\n[OK] Generated {len(plots)} plots")
    print("\nOutput files:")
    for plot in sorted(plots):
        print(f"  - {plot}")
    
    print("\nUsage: Include these plots in documentation and reports")
    print("=" * 70 + "\n")
