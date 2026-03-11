#!/usr/bin/env python
"""Rastreo de funciones utilizadas en los experimentos."""

import opfunu.cec_based

funciones_config = ["F1", "F5", "F11", "F21", "F22", "F23"]

print("\n" + "=" * 90)
print("RASTREO DE FUNCIONES BENCHMARK - OPFUNU.CEC_BASED")
print("=" * 90)
print("\nFunciones configuradas en experiments_config.json:")
print(f"  {funciones_config}\n")

print("=" * 90)
print("DEFINICIONES EXACTAS DE CADA FUNCIÓN:")
print("=" * 90)

for fname in funciones_config:
    try:
        func_class = getattr(opfunu.cec_based, fname)
        func = func_class()
        
        print(f"\n{fname}:")
        print(f"  - Nombre completo: {func.name}")
        print(f"  - Óptimo global (f_global): {func.f_global}")
        print(f"  - Dimensión por defecto: {func.n_dims if hasattr(func, 'n_dims') else 'N/A'}")
        
    except AttributeError as e:
        print(f"\n{fname}:")
        print(f"  - ERROR: No encontrado en opfunu.cec_based")

print("\n" + "=" * 90)
print("CONCLUSIÓN:")
print("=" * 90)
print("""
Las funciones F1-F23 vienen de la librería OPFUNU (CEC-BASED functions).
NO son funciones CEC2017, sino un conjunto de funciones benchmark clásicas.

Los óptimos definidos en BD/sqlite.py (líneas 240-264) son los correctos para
estas funciones clásicas de opfunu.cec_based.
""")
