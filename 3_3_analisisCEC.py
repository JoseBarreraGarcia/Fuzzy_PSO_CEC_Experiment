#!/usr/bin/env python
"""
Quick-Start Script for CEC Analysis Pipeline

Ejecuta la pipeline completa de análisis CEC2017 con opciones interactivas.

Uso:
    python run_cec_analysis.py              # Pipeline completa interactiva
    python run_cec_analysis.py --help       # Ver todas las opciones
    python run_cec_analysis.py --full       # Pipeline sin preguntas
    python run_cec_analysis.py --convergence-only  # Solo convergence
    python run_cec_analysis.py --diversity-only    # Solo diversity
"""

import argparse
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analysis_modules_cec import (
    level1_raw_data_cec,
    level2_aggregated_cec,
    convergence_analysis_cec,
    diversity_analysis_cec
)


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def check_prerequisites():
    """Verificar que existen los archivos necesarios."""
    required_file = 'Resultados/resumen/level1_raw_cec/ben_experiments_all_runs.csv'
    
    if not os.path.exists(required_file):
        print(f"[WARN] Archivo requerido no encontrado: {required_file}")
        print("[INFO] Se ejecutará Level 1 para generar datos necesarios\n")
        return False
    
    return True


def run_level1():
    """Ejecutar Level 1: Raw Data Extraction."""
    print_header("LEVEL 1: RAW DATA EXTRACTION")
    try:
        level1_raw_data_cec.main()
        return True
    except Exception as e:
        print(f"[ERROR] Level 1 falló: {e}")
        return False


def run_level2():
    """Ejecutar Level 2: Aggregated Statistics."""
    print_header("LEVEL 2: AGGREGATED STATISTICS & PLOTS")
    try:
        level2_aggregated_cec.main()
        return True
    except Exception as e:
        print(f"[ERROR] Level 2 falló: {e}")
        return False


def run_convergence():
    """Ejecutar Convergence Analysis."""
    print_header("STEP 3: CONVERGENCE ANALYSIS")
    try:
        convergence_analysis_cec.main()
        return True
    except Exception as e:
        print(f"[WARN] Convergence analysis falló: {e}")
        return False


def run_diversity():
    """Ejecutar Diversity Analysis."""
    print_header("STEP 4: DIVERSITY ANALYSIS")
    try:
        diversity_analysis_cec.main()
        return True
    except Exception as e:
        print(f"[WARN] Diversity analysis falló: {e}")
        return False


def interactive_menu():
    """Menú interactivo para seleccionar análisis."""
    
    print_header("CEC2017 ANALYSIS PIPELINE - INTERACTIVE MENU")
    
    print("Selecciona qué análisis ejecutar:\n")
    print("  1. Pipeline COMPLETA (1 → 2 → 3 → 4)")
    print("  2. Solo Level 1 (Raw Data)")
    print("  3. Solo Level 2 (Aggregated)")
    print("  4. Solo Convergence Analysis")
    print("  5. Solo Diversity Analysis")
    print("  6. Levels 1 + 2 (sin análisis especializados)")
    print("  7. Convergence + Diversity (sin levels 1-2)")
    print("  0. Salir")
    print()
    
    choice = input("Ingresa tu selección (0-7): ").strip()
    
    return choice


def main():
    """Main function with argument parsing."""
    
    parser = argparse.ArgumentParser(
        description='CEC2017 Analysis Pipeline Executor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run_cec_analysis.py                # Menú interactivo
  python run_cec_analysis.py --full         # Pipeline completa (sin preguntas)
  python run_cec_analysis.py --convergence-only   # Solo convergence
  python run_cec_analysis.py --diversity-only     # Solo diversity
  python run_cec_analysis.py --skip-level1 --full # Pipeline completa sin Level 1
        """)
    
    parser.add_argument('--full', action='store_true',
                       help='Ejecutar pipeline completa sin preguntas')
    parser.add_argument('--convergence-only', action='store_true',
                       help='Ejecutar solo Convergence Analysis')
    parser.add_argument('--diversity-only', action='store_true',
                       help='Ejecutar solo Diversity Analysis')
    parser.add_argument('--level1-only', action='store_true',
                       help='Ejecutar solo Level 1 (Raw Data)')
    parser.add_argument('--level2-only', action='store_true',
                       help='Ejecutar solo Level 2 (Aggregated)')
    parser.add_argument('--skip-level1', action='store_true',
                       help='Saltar Level 1 (asumir datos ya existen)')
    parser.add_argument('--skip-level2', action='store_true',
                       help='Saltar Level 2')
    
    args = parser.parse_args()
    
    # Lógica de ejecución basada en argumentos
    if args.convergence_only:
        run_convergence()
        return
    
    if args.diversity_only:
        run_diversity()
        return
    
    if args.level1_only:
        run_level1()
        return
    
    if args.level2_only:
        # Requiere Level 1 primero
        if not check_prerequisites():
            print("[ERROR] Level 2 requiere datos de Level 1")
            print("[INFO] Ejecutar primero: python run_cec_analysis.py --level1-only")
            return
        run_level2()
        return
    
    if args.full:
        # Pipeline completa
        print_header("CEC2017 ANALYSIS PIPELINE - FULL EXECUTION")
        
        if not args.skip_level1:
            if not run_level1():
                return
        
        if not args.skip_level2:
            if not run_level2():
                return
        
        run_convergence()
        run_diversity()
        
        print_header("PIPELINE COMPLETADA")
        print("[OK] Todos los análisis se ejecutaron exitosamente\n")
        return
    
    # Menú interactivo (default)
    choice = interactive_menu()
    
    if choice == '1':
        # Pipeline completa
        if not run_level1():
            return
        if not run_level2():
            return
        run_convergence()
        run_diversity()
        print_header("PIPELINE COMPLETADA")
        
    elif choice == '2':
        run_level1()
        
    elif choice == '3':
        if not check_prerequisites():
            print("[ERROR] Level 2 requiere datos de Level 1")
            return
        run_level2()
        
    elif choice == '4':
        if not check_prerequisites():
            print("[ERROR] Convergence Analysis requiere datos de Level 1")
            return
        run_convergence()
        
    elif choice == '5':
        if not check_prerequisites():
            print("[ERROR] Diversity Analysis requiere datos de Level 1")
            return
        run_diversity()
        
    elif choice == '6':
        if not run_level1():
            return
        run_level2()
        
    elif choice == '7':
        if not check_prerequisites():
            print("[ERROR] Análisis especializados requieren datos de Level 1")
            return
        run_convergence()
        run_diversity()
        
    elif choice == '0':
        print("\n[INFO] Saliendo...\n")
        return
        
    else:
        print(f"\n[ERROR] Opción inválida: {choice}\n")
        return
    
    print_header("EJECUCIÓN COMPLETADA")
    print("\nOutputs generados en: Resultados/resumen/level2_aggregated_cec/")
    print("\nDirectorios:")
    print("  ✓ convergence/")
    print("  ✓ diversity/")
    print("  ✓ comparison/\n")


if __name__ == '__main__':
    main()
