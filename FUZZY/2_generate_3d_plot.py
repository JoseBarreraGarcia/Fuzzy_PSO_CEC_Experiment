#!/usr/bin/env python3
"""
Generate 3D surface comparison plot
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Ensure imports work
sys.path.insert(0, os.getcwd())

from fuzzy_controller_w import FuzzyInertiaController
from fuzzy_controller_w_5labels import FuzzyInertiaController_5labels

def plot_3d_comparison(input_set="I1"):
    """Create 3D surface comparison between 3-label and 5-label controllers."""
    
    os.makedirs('FUZZY/plots', exist_ok=True)
    
    print("Generating 3D surface comparison...")
    
    div_range = np.linspace(0.01, 0.99, 50)
    prog_range = np.linspace(0.01, 0.99, 50)
    DIV, PROG = np.meshgrid(div_range, prog_range)
    
    ctrl3 = FuzzyInertiaController(w_set='A', input_set=input_set)
    ctrl5 = FuzzyInertiaController_5labels(w_set='A', input_set=input_set)
    
    W3 = np.zeros_like(DIV)
    W5 = np.zeros_like(DIV)
    
    for i in range(DIV.shape[0]):
        for j in range(DIV.shape[1]):
            W3[i, j] = ctrl3.compute_w(DIV[i, j], PROG[i, j])
            W5[i, j] = ctrl5.compute_w(DIV[i, j], PROG[i, j])
    
    fig = plt.figure(figsize=(14, 5))
    
    # 3D Surface para 3 labels
    ax1 = fig.add_subplot(131, projection='3d')
    ax1.plot_surface(DIV, PROG, W3, cmap='viridis', alpha=0.8)
    ax1.set_xlabel('Diversity Ratio', fontsize=9)
    ax1.set_ylabel('Progress (iter/maxIter)', fontsize=9)
    ax1.set_zlabel('Inertia Weight w', fontsize=9)
    ax1.set_title('Set A: 3 Labels\nw ∈ [0.0, 1.0]', fontsize=10, fontweight='bold')
    
    # 3D Surface para 5 labels
    ax2 = fig.add_subplot(132, projection='3d')
    ax2.plot_surface(DIV, PROG, W5, cmap='viridis', alpha=0.8)
    ax2.set_xlabel('Diversity Ratio', fontsize=9)
    ax2.set_ylabel('Progress (iter/maxIter)', fontsize=9)
    ax2.set_zlabel('Inertia Weight w', fontsize=9)
    ax2.set_title('Set A: 5 Labels\nw ∈ [0.0, 1.0]', fontsize=10, fontweight='bold')
    
    # Diferencia
    ax3 = fig.add_subplot(133)
    diff = W5 - W3
    contour = ax3.contourf(DIV, PROG, diff, levels=20, cmap='RdBu_r')
    ax3.set_xlabel('Diversity Ratio', fontsize=9)
    ax3.set_ylabel('Progress (iter/maxIter)', fontsize=9)
    ax3.set_title('Difference: 5-labels minus 3-labels', fontsize=10, fontweight='bold')
    cbar = plt.colorbar(contour, ax=ax3)
    cbar.set_label('Δw', fontsize=9)
    
    plt.tight_layout()
    output_path = './FUZZY/plots/08_3d_surface_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight', format='png')
    plt.close(fig)
    
    print(f"✅ Saved: {output_path}")
    return output_path

if __name__ == '__main__':
    plot_3d_comparison()
