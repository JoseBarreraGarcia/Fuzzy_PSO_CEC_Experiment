import numpy as np

from Diversity.Codes.diversity import calculate_diversity
from FUZZY.fuzzy_controller_w import FuzzyInertiaController


def iterarPSO_FCS(maxIter, iter, dim, population, best, pBest, vel, ub0,
                  maxDiversity, fcs: FuzzyInertiaController, w_set="B"):
    """
    PSO con Fuzzy Controlled inertia weight.
    
    Parámetros:
        w_set (str): Set de funciones de pertenencia ('A', 'B', 'C', etc.)
                     Si fcs tiene un w_set diferente, se crea uno nuevo localmente.
    """
    Vmax = 0.1 * ub0
    c1 = 2.0
    c2 = 2.0

    # Si el set del controlador no coincide, crear uno local
    if fcs.w_set.upper() != w_set.upper():
        fcs = FuzzyInertiaController(wMin=fcs.wMin, wMax=fcs.wMax, w_set=w_set)

    # --- 1) Diversidad actual + normalización ---
    div_t, maxDiversity, XPL, XPT = calculate_diversity(population, maxDiversity)
    diversity_ratio = 0.0 if maxDiversity <= 1e-12 else (div_t / maxDiversity)

    # --- 2) Progreso ---
    progress = 0.0 if maxIter <= 0 else (iter / maxIter)

    # --- 3) Control difuso de w ---
    w = fcs.compute_w(diversity_ratio=diversity_ratio, progress=progress)

    # --- 4) Random r1, r2 ---
    r1 = np.random.rand(population.shape[0], dim)
    r2 = np.random.rand(population.shape[0], dim)

    # Asegurar broadcasting estable si best es (dim,)
    best = np.asarray(best).reshape(1, -1)

    # --- 5) Update velocities ---
    vel = (
        w * vel
        + c1 * r1 * (pBest - population)
        + c2 * r2 * (best - population)
    )

    # --- 6) Clip vel ---
    vel = np.clip(vel, -Vmax, Vmax)

    # --- 7) Update positions ---
    population = population + vel

    return population, vel, maxDiversity
