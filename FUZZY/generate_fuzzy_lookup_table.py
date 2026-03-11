#!/usr/bin/env python3
"""
Generate Fuzzy Logic Lookup Table (CSV)

Crea una tabla CSV con valores de entrada (diversidad, progreso) y salidas fuzzy (w para cada set)
más las reglas activadas.

Output: FUZZY/fuzzy_lookup_table.csv
"""

import os
import csv
import numpy as np
from fuzzy_controller_w import FuzzyInertiaController, tri


# ============================================================================
# CONFIGURACIÓN: Incremento de valores para la tabla
# ============================================================================
# Cambia este valor para controlar la granularidad de la tabla:
#   0.01 = cada 1% (101 valores: 0.00, 0.01, 0.02, ..., 1.00)
#   0.02 = cada 2% (51 valores: 0.00, 0.02, 0.04, ..., 1.00)
#   0.05 = cada 5% (21 valores: 0.00, 0.05, 0.10, ..., 1.00)
#   0.10 = cada 10% (11 valores: 0.0, 0.1, 0.2, ..., 1.0)
LOOKUP_TABLE_STEP = 0.02
# ============================================================================


def tri_extended(x, a, b, c):
    """
    Versión mejorada de tri() que maneja correctamente los casos extremos.
    Arregla el problema donde x=0.0 y a=0.0 causaba que tri() retorne 0.0
    cuando debería considerar que x está dentro del soporte del triángulo.
    
    Triangular fuzzy membership: (a, b, c)
    - a, c: límites del soporte
    - b: pico (máximo)
    """
    x = float(x)
    a, b, c = float(a), float(b), float(c)
    
    # Fuera del rango [a, c]
    if x < a or x > c:
        return 0.0
    
    # En el pico
    if x == b:
        return 1.0
    
    # Rampa izquierda: [a, b)
    if a < x < b:
        return (x - a) / (b - a)
    
    # Rampa derecha: (b, c]
    if b < x < c:
        return (c - x) / (c - b)
    
    # En los puntos límite (a o c): retorna pequeño valor para mantener continuidad
    # Esto es clave: no retorna 0.0 en los extremos, sino un valor pequeño positivo
    if x == a or x == c:
        return 0.001  # Pequeño valor para que se considere "dentro" del triángulo
    
    return 0.0


def get_activated_rules(controller, diversity, progress):
    """
    Determina qué reglas fuzzy se activan para una combinación de entrada.
    Usa tri_extended para manejar correctamente los valores extremos.
    
    Returns: lista de reglas activadas con su grado de disparo
    """
    d = float(diversity)
    t = float(progress)
    
    # Fuzzificación con tri_extended (maneja extremos correctamente)
    mu_d = {k: tri_extended(d, *abc) for k, abc in controller.div_mf.items()}
    mu_t = {k: tri_extended(t, *abc) for k, abc in controller.it_mf.items()}
    
    # Obtener reglas activadas - mostrar TODAS con firing > 0.0001
    # Threshold bajo porque tri_extended puede retornar valores muy pequenos en limites
    activated = []
    for (d_lab, t_lab), out_lab in controller.rules.items():
        firing = min(mu_d[d_lab], mu_t[t_lab])
        if firing > 0.0001:  # Mostrar TODA regla con activación significativa
            activated.append(f"{d_lab} AND {t_lab} -> {out_lab} ({firing:.3f})")
    
    # Ordenar por firing decreciente para claridad
    activated.sort(key=lambda x: float(x.split('(')[1].split(')')[0]), reverse=True)
    
    return " | ".join(activated) if activated else "none"


def generate_lookup_table(output_dir="./FUZZY", step=0.02):
    """
    Genera tabla de búsqueda del controlador fuzzy.
    
    Args:
        output_dir: Directorio donde guardar el CSV
        step: Incremento entre valores (default 0.02 = cada 2 centésimas)
              Ejemplos: 0.01=cada 1%, 0.02=cada 2%, 0.05=cada 5%, 0.1=cada 10%
    """
    
    # Crear directorio si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Definir espacios de entrada basados en el incremento
    # Usamos arange con un pequeño margen para asegurar que 1.0 se incluya
    diversity_values = np.arange(0.0, 1.0 + step/2, step)
    progress_values = np.arange(0.0, 1.0 + step/2, step)
    w_sets = ['A', 'B', 'C', 'D']
    
    # Crear controladores para cada w_set
    controllers = {}
    for w_set in w_sets:
        try:
            controllers[w_set] = FuzzyInertiaController(w_set)
        except ValueError as e:
            print(f"[WARN] No se pudo crear controlador para {w_set}: {e}")
    
    # Preparar datos para la tabla
    rows = []
    header = ['Diversity', 'Progress']
    
    # Agregar columnas de salida para cada w_set
    for w_set in w_sets:
        if w_set in controllers:
            header.append(f'w_set_{w_set}')
    
    header.append('Activated_Rules')
    
    print(f"\n[*] Generando tabla de búsqueda fuzzy")
    print(f"    Muestras: {len(diversity_values)} × {len(progress_values)} = {len(diversity_values) * len(progress_values)} combinaciones")
    
    # Generar filas
    count = 0
    for div in diversity_values:
        for prog in progress_values:
            row = [
                f"{div:.2f}",
                f"{prog:.2f}",
            ]
            
            # Calcular w para cada set
            for w_set in w_sets:
                if w_set in controllers:
                    try:
                        w = controllers[w_set].compute_w(div, prog)
                        row.append(f"{w:.4f}")
                    except Exception as e:
                        row.append("ERROR")
                        print(f"[ERROR] Cálculo de w para {w_set} falló: {e}")
            
            # Reglas activadas (usar el primer controller disponible como referencia)
            if controllers:
                ref_controller = list(controllers.values())[0]
                rules = get_activated_rules(ref_controller, div, prog)
                row.append(rules)
            else:
                row.append("N/A")
            
            rows.append(row)
            count += 1
    
    # Guardar CSV
    output_path = os.path.join(output_dir, 'fuzzy_lookup_table.csv')
    
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(rows)
        
        print(f"[OK] Tabla generada: {output_path}")
        print(f"     {count} filas de datos")
        print(f"     {len(header)} columnas")
        
        # Mostrar preview
        print(f"\n[INFO] Preview de primeras 5 filas:")
        print(f"     Header: {', '.join(header)}")
        for i, row in enumerate(rows[:5]):
            print(f"     Fila {i+1}: {', '.join(row)}")
        
        return output_path
        
    except Exception as e:
        print(f"[ERROR] No se pudo guardar la tabla: {e}")
        return None


if __name__ == '__main__':
    import sys
    
    print("=" * 70)
    print("FUZZY LOOKUP TABLE GENERATOR")
    print("=" * 70)
    
    # Parámetro opcional: incremento (paso)
    step = LOOKUP_TABLE_STEP  # default desde constante de configuración
    if len(sys.argv) > 1:
        try:
            step = float(sys.argv[1])
            if not (0.0 < step <= 1.0):
                raise ValueError("Step debe estar entre 0 y 1")
        except ValueError as e:
            print(f"[WARN] Argumento inválido: {sys.argv[1]} ({e}), usando default {step}")
    
    print(f"[CONFIG] Incremento configurado: {step} (genera {int(1.0/step)+1} valores por dimensión)")
    
    output_file = generate_lookup_table(step=step)
    
    print("\n" + "=" * 70)
    if output_file:
        print(f"[SUCCESS] Tabla fuzzy generada exitosamente")
        print(f"          Archivo: {output_file}")
        print(f"          Úsalo para: análisis, reportes, verificación")
    else:
        print(f"[FAILURE] Error generando tabla")
        sys.exit(1)
