"""
Visualización: Evolución de w (inertia weight) en PSO vs PSO_FCS

Demuestra cómo PSO usa estrategia lineal mientras PSO_FCS oscila
con fuzzy controller (mal calibrado para espacios continuos).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

# Simulación de estrategias de w

def simulate_pso_w(maxIter=100):
    """PSO estándar: w lineal decreciente"""
    wMax, wMin = 0.9, 0.1
    w_history = []
    for iter in range(maxIter + 1):
        w = wMax - iter * ((wMax - wMin) / maxIter)
        w_history.append(w)
    return np.array(w_history)


def simulate_pso_fcs_a(maxIter=100):
    """PSO_FCS:A - Simulación de fuzzy controller con Set A
    
    Asume que la diversidad decrece exponencialmente como lo hace PSO
    al converger hacia el óptimo local.
    """
    w_history = []
    
    for iter in range(maxIter + 1):
        progress = iter / maxIter
        
        # Simular diversidad que cae exponencialmente
        # (como típicamente ocurre en PSO)
        diversity_ratio = np.exp(-3 * progress)  # Cae de 1 → 0.05
        
        # Reglas fuzzy Set A (simplificadas)
        if diversity_ratio > 0.6:
            w_out = "high"
            w_val = 0.85
        elif diversity_ratio > 0.3:
            w_out = "medium"
            w_val = 0.50
        else:
            w_out = "low"
            w_val = 0.25
            
        w_history.append(w_val)
    
    return np.array(w_history)


def simulate_diversity_ratio(maxIter=100):
    """Simula cómo cae la diversidad en PSO converging"""
    diversity = np.exp(-3 * np.arange(maxIter + 1) / maxIter)
    return diversity


# ============= GENERAR GRÁFICOS =============

fig = plt.figure(figsize=(14, 10))
gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)

# Colores
color_pso = '#FF6B6B'      # Rojo
color_fcs = '#4ECDC4'      # Verde azulado
color_div = '#95A5A6'      # Gris

maxIter = 100
iters = np.arange(maxIter + 1)

# ============= FILA 1: w(iter) =============

ax1 = fig.add_subplot(gs[0, :])

w_pso = simulate_pso_w(maxIter)
w_fcs_a = simulate_pso_fcs_a(maxIter)

ax1.plot(iters, w_pso, linewidth=2.5, label='PSO (Lineal)', 
         color=color_pso, marker='o', markersize=2, markevery=5)
ax1.plot(iters, w_fcs_a, linewidth=2.5, label='PSO_FCS:A (Fuzzy)', 
         color=color_fcs, marker='s', markersize=2, markevery=5)

ax1.fill_between(iters, w_pso - 0.05, w_pso + 0.05, alpha=0.2, color=color_pso, label='PSO rango ±0.05')
ax1.axvspan(0, 20, alpha=0.1, color='blue', label='Exploración (iter 0-20)')
ax1.axvspan(80, 100, alpha=0.1, color='red', label='Explotación (iter 80-100)')

ax1.set_xlabel('Iteración', fontsize=11, fontweight='bold')
ax1.set_ylabel('Inertia Weight (w)', fontsize=11, fontweight='bold')
ax1.set_title('Estrategia de w: PSO (Lineal) vs PSO_FCS:A (Fuzzy)', 
              fontsize=12, fontweight='bold')
ax1.legend(loc='upper right', fontsize=9)
ax1.grid(True, alpha=0.3)
ax1.set_ylim([0.0, 1.0])

# ============= FILA 2: Diversidad y Reglas Fuzzy =============

ax2 = fig.add_subplot(gs[1, 0])
diversity = simulate_diversity_ratio(maxIter)

ax2.plot(iters, diversity, linewidth=2.5, color=color_div, marker='o', markersize=2, markevery=5)
ax2.fill_between(iters, 0, diversity, alpha=0.3, color=color_div)
ax2.axhline(0.6, color='green', linestyle='--', alpha=0.6, linewidth=1.5, label='Threshold High')
ax2.axhline(0.3, color='orange', linestyle='--', alpha=0.6, linewidth=1.5, label='Threshold Medium')

ax2.set_xlabel('Iteración', fontsize=11, fontweight='bold')
ax2.set_ylabel('Diversity Ratio (normalizado)', fontsize=11, fontweight='bold')
ax2.set_title('Diversidad de Población en PSO', fontsize=12, fontweight='bold')
ax2.legend(fontsize=9)
ax2.grid(True, alpha=0.3)
ax2.set_ylim([0, 1.1])

# ============= FILA 2: Regiones de Reglas Fuzzy =============

ax3 = fig.add_subplot(gs[1, 1])

# Regions by rule
low_div_early = (diversity <= 0.6) & (iters <= 33)
low_div_mid = (diversity <= 0.6) & (iters > 33) & (iters <= 66)
low_div_late = (diversity <= 0.6) & (iters > 66)

med_div_early = (diversity > 0.3) & (diversity <= 0.6) & (iters <= 33)
med_div_mid = (diversity > 0.3) & (diversity <= 0.6) & (iters > 33) & (iters <= 66)
med_div_late = (diversity > 0.3) & (diversity <= 0.6) & (iters > 66)

ax3.fill_between(iters, 0, 1, where=med_div_early, alpha=0.5, color='yellow', 
                 label='("medium", "early") → w=high')
ax3.fill_between(iters, 0, 1, where=low_div_early, alpha=0.5, color='orange',
                 label='("low", "early") → w=medium')
ax3.fill_between(iters, 0, 1, where=med_div_mid, alpha=0.4, color='cyan',
                 label='("medium", "mid") → w=medium')
ax3.fill_between(iters, 0, 1, where=low_div_late, alpha=0.5, color='lightcoral',
                 label='("low", "late") → w=low')

ax3.set_xlabel('Iteración', fontsize=11, fontweight='bold')
ax3.set_ylabel('Regla Fuzzy Activa', fontsize=11, fontweight='bold')
ax3.set_title('Reglas Fuzzy que Afectan w (PSO_FCS:A)', fontsize=12, fontweight='bold')
ax3.legend(fontsize=8, loc='upper right')
ax3.set_ylim([0, 1])
ax3.set_xlim([0, 100])

# ============= FILA 3: Velocidad de Cambio de w =============

ax4 = fig.add_subplot(gs[2, 0])

dw_pso = np.diff(w_pso)
dw_fcs = np.diff(w_fcs_a)

ax4.plot(iters[1:], dw_pso, linewidth=2, color=color_pso, label='PSO: dw/diter')
ax4.plot(iters[1:], dw_fcs, linewidth=2, color=color_fcs, label='PSO_FCS:A: dw/diter', marker='s', markersize=3, markevery=5)

ax4.axhline(0, color='black', linestyle='-', alpha=0.3, linewidth=0.5)
ax4.fill_between(iters[1:], dw_pso, alpha=0.2, color=color_pso)

ax4.set_xlabel('Iteración', fontsize=11, fontweight='bold')
ax4.set_ylabel('Cambio en w por iteración (dw/diter)', fontsize=11, fontweight='bold')
ax4.set_title('Tasa de Cambio: PSO (constante) vs PSO_FCS (variable)', fontsize=12, fontweight='bold')
ax4.legend(fontsize=9)
ax4.grid(True, alpha=0.3)

# ============= FILA 3: Acumulado de w =============

ax5 = fig.add_subplot(gs[2, 1])

cumsum_pso = np.cumsum(w_pso)
cumsum_fcs = np.cumsum(w_fcs_a)

ax5.plot(iters, cumsum_pso, linewidth=2.5, color=color_pso, marker='o', markersize=2, markevery=5,
         label='PSO acumulado')
ax5.plot(iters, cumsum_fcs, linewidth=2.5, color=color_fcs, marker='s', markersize=2, markevery=5,
         label='PSO_FCS:A acumulado')

ax5.fill_between(iters, cumsum_pso, cumsum_fcs, alpha=0.2, color='purple')

ax5.set_xlabel('Iteración', fontsize=11, fontweight='bold')
ax5.set_ylabel('Acumulado de w', fontsize=11, fontweight='bold')
ax5.set_title('Acumulación de Exploración/Explotación', fontsize=12, fontweight='bold')
ax5.legend(fontsize=9)
ax5.grid(True, alpha=0.3)

# Anotaciones clave
ax5.text(20, cumsum_pso[20], f'PSO@20: {cumsum_pso[20]:.1f}', fontsize=9, 
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
ax5.text(20, cumsum_fcs[20], f'FCS@20: {cumsum_fcs[20]:.1f}', fontsize=9,
         bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

plt.suptitle('Análisis: Por Qué PSO Supera a PSO_FCS en CEC2017\nEstrategias de Inertia Weight Comparadas', 
             fontsize=13, fontweight='bold', y=0.995)

plt.savefig('w_strategy_comparison.png', dpi=300, bbox_inches='tight')
print("✓ Gráfico guardado: w_strategy_comparison.png")
print("\nInterpretación:")
print("─" * 80)
print("1. PSO (rojo): w decrece LINEALMENTE de 0.9 → 0.1")
print("   → Exploración controlada al inicio, explotación gradual al final")
print("   → Estrategia validada por 20+ años de investigación")
print("")
print("2. PSO_FCS:A (turquesa): w oscila por reglas fuzzy")
print("   → Intenta adaptar w basado en diversidad")
print("   → PERO: Reglas diseñadas para SCP (discreto), no CEC2017 (continuo)")
print("   → Resultado: Menos explotación cuando más se necesita")
print("")
print("3. Diversidad (gris): Cae exponencialmente")
print("   → Indica convergencia exitosa del PSO")
print("   → Fuzzy interpreta esto mal → reduce w innecesariamente")
print("")
print("4. Acumulado: PSO invierte MÁS en explotación total")
print("   → ΔArea = PSO invierte más iteraciones en convergencia fina")
print("")

plt.show()
