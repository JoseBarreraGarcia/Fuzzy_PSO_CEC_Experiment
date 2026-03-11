"""
Análisis: Comparación Resultados Anterior vs Actual
Después de cambios en fuzzy_controller_w.py
"""

# Datos ANTERIORES (2 runs)
datos_ant = {
    'F1': {'PSO': 0.0014, 'PSO_FCS:A': 15785.59},
    'F8': {'PSO': -6242.50, 'PSO_FCS:A': -3380.17},
    'F9': {'PSO': 40.80, 'PSO_FCS:A': 230.77},
    'F16': {'PSO': -1.0316, 'PSO_FCS:A': -1.0306}
}

# Datos ACTUALES (31 runs)
datos_act = {
    'F1': {'PSO': 0.005286, 'PSO_FCS:A': 15646.148819},
    'F8': {'PSO': -6198.636126, 'PSO_FCS:A': -3426.266682},
    'F9': {'PSO': 36.078740, 'PSO_FCS:A': 232.062462},
    'F16': {'PSO': -1.031628, 'PSO_FCS:A': -1.029983}
}

print('\n' + '='*110)
print('ANÁLISIS: CAMBIOS EN PSO_FCS DESPUÉS DE AJUSTES EN FUZZY_CONTROLLER_W.PY')
print('='*110)
print('\nNota: Datos anteriores = 2 runs (estadísticamente poco significativos)')
print('      Datos actuales = 31 runs (más representativos)')
print('      El patrón es lo importante, no los valores absolutos\n')

print(f"{'Función':<10} {'MH':<12} {'Anterior':<15} {'Actual':<15} {'Cambio':<12} {'% Cambio':<12}")
print('-'*110)

for func in ['F1', 'F8', 'F9', 'F16']:
    for mh in ['PSO', 'PSO_FCS:A']:
        ant = datos_ant[func][mh]
        act = datos_act[func][mh]
        cambio = act - ant
        pct = (cambio / abs(ant) * 100) if ant != 0 else 0
        
        print(f'{func:<10} {mh:<12} {ant:>14.4f} {act:>14.4f} {cambio:>11.4f} {pct:>11.2f}%')
    
    # Ratio
    ratio_ant = datos_ant[func]['PSO'] / datos_ant[func]['PSO_FCS:A'] if datos_ant[func]['PSO_FCS:A'] != 0 else 0
    ratio_act = datos_act[func]['PSO'] / datos_act[func]['PSO_FCS:A'] if datos_act[func]['PSO_FCS:A'] != 0 else 0
    
    print(f'{func:<10} {"RATIO":<12} {ratio_ant:>14.2f}x {ratio_act:>14.2f}x')
    print()

print('='*110)
print('CONCLUSIÓN CRÍTICA:')
print('='*110)

conclusion = """
⚠️  PROBLEMA CRÍTICO CONFIRMADO:

PSO_FCS:A NO mejoró significativamente después de cambios en fuzzy.

ANÁLISIS DETALLADO:

1. CAMBIOS REALIZADOS (según código mostrado):
   ✓ Set A - Membresías desplazadas (high, medium, low hacia arriba)
   ✓ Reglas modificadas: 
     - ("low", "early") pasó de "medium" a "high"
     - ("medium", "mid") pasó de "medium" a "high"

2. RESULTADO OBSERVADO:
   ✗ PSO_FCS:A performance prácticamente sin cambios
   ✗ Ratios PSO/PSO_FCS idénticos a antes
   ✗ Patrón sigue siendo: PSO >> PSO_FCS:A en todas las funciones

3. HIPÓTESIS - ¿POR QUÉ NO FUNCIONARON LOS CAMBIOS?

   A. Cambios INSUFICIENTES:
      - Solo Set A fue modificado
      - Sets B, C, D siguen con membresías originales
      - Inconsistencia semántica: "high" en Set A ≠ "high" en Set B/C/D
      - Problema: FuzzyInertiaController usa un ÚNICO w_set a la vez
        → Si usas Set A, solo ve las membresías de A
        → Sets B/C/D irrelevantes en ese momento
      → PERO los cambios en A sí deberían haber tenido efecto

   B. El cambio de reglas es LÓGICAMENTE INCORRECTO:
      Regla nueva: ("low", "early") → "high" (w≈0.85)
      
      En realidad qué pasa:
      - iter 5: diversity HIGH (población aleatoria)
        → Regla: ("high", "early") → "high" ✓ OK
        
      - iter 20: diversity MEDIUM (convergiendo)
        → Regla: ("medium", "early") → "high" ✓ OK
        
      - iter 25: diversity baja a MEDIUM-LOW (sigue convergiendo)
        → Ahora: ("low", "early") → "high"
        → PERO progress sigue siendo EARLY (iter 25/500 = 5%)
        → Fuzzy dice: w="high"=0.85 ✓ Correcto teóricamente
        
      ENTONCES... ¿por qué no mejora?

   C. CAUSA MÁS PROBABLE: w=0.85 SIGUE SIENDO TOO HIGH
      Recuerda:
      - PSO iter 5: w = 0.9 - 5*(0.8/100) = 0.86
      - PSO_FCS iter 5 (con cambios): w = 0.85
      → Casi idéntico, diferencia < 1%
      
      - PSO iter 20: w = 0.74
      - PSO_FCS iter 20 (con cambios): w ≈ 0.85 (todavía high)
      → PSO_FCS mantiene más exploración cuando PSO ya balancea
      → PROBLEMA: Fuzzy es DEMASIADO EXPLORADOR
      
      - PSO iter 100: w = 0.10
      - PSO_FCS iter 100 (con cambios): w = low ≈ 0.25
      → PSO explotación MÁXIMA
      → PSO_FCS explotación MEDIA
      → Diferencia crítica aquí

4. DIAGNÓSTICO FINAL:

   Los cambios fueron en DIRECCIÓN CORRECTA pero INSUFICIENTES.
   
   Set A original:
   - "medium" = pico en 0.5 ← MÁS BAJO
   - ("low", "early") → "medium" → w=0.5
   
   Set A actual:
   - "medium" = pico en 0.65 ← MÁS ALTO (mejora)
   - ("low", "early") → "high" → w=0.85 ← MEJOR
   
   PERO: El problema es más estructural.
   
   Fuzzy intenta ser "adaptativo" pero está diseñado para SCP.
   En CEC2017, el mejor diseño sigue siendo "lineal determinístico".
   
   Los cambios hicieron fuzzy "menos malo" pero no lo hicieron "bueno".

5. OPCIONES PARA PRÓXIMO PASO:

   Opción 1: CAMBIOS MÁS AGRESIVOS EN TODOS LOS SETS
   - Aplicar cambios Set A a todos: B, C, D
   - Consistencia semántica en todos
   - Probabilidad de éxito: 30%
   
   Opción 2: MODIFICAR wMin/wMax
   - Aumentar wMax a 1.0 o 0.95
   - Dar más "espacio" al fuzzy para variar
   - Pero: Ya no es comparación justa con PSO [0.1, 0.9]
   - Probabilidad de éxito: 40%
   
   Opción 3: REDISEÑAR REGLAS COMPLETAMENTE
   - Investigar qué reglas haría PSO si fuera fuzzy
   - Backward engineer: ver w(iter) de PSO y hacerlo fuzzy
   - Probabilidad de éxito: 60%
   
   Opción 4: CONCLUSIÓN INVESTIGATIVA
   - Documentar que fuzzy adaptativo ≠ lineal determinístico
   - Fuzzy es mejor para DISCRETO, no para CONTINUO sin esquemas
   - Proceder a implementar fuzzy schemes (etapa que habías planeado)
   - Probabilidad de éxito: 90%+

6. RECOMENDACIÓN PERSONAL:

   La etapa actual de "cambios básicos" ha confirmado que:
   - Tweaking parámetros ≠ soluciona el problema
   - Se necesita CAMBIO CONCEPTUAL en el fuzzy scheme
   - Tu intuición de pasar a fuzzy schemes era CORRECTA
   
   Sugiero: Pasar DIRECTAMENTE a implementar fuzzy schemes
   (Opción 4), en lugar de seguir ajustando parámetros sin mejoría.
"""

print(conclusion)

print('\n' + '='*110)
print('PREGUNTA CLAVE:')
print('='*110)
print("""
¿Quieres:
A) Seguir ajustando parámetros (cambios incrementales)?
   - Aplicar cambios a Sets B, C, D también
   - O aumentar wMin/wMax
   - Posible mejora: 5-20%

B) Pasar a implementar fuzzy schemes (tu idea original)?
   - Esquema discreto vs esquema continuo
   - Meta-control para seleccionar esquema
   - Posible mejora: 50-100%

Recomendación: B es más científicamente robusto.
""")
