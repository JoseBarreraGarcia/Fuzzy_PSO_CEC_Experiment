import numpy as np

from Diversity.Codes.diversity import calculate_diversity
from FUZZY.fuzzy_controller_w_3L import FuzzyInertiaController_3L
from afcs.optimizers.pso import PSOConfig, advance_swarm


def iterarPSO_FCS(maxIter, iter, dim, population, best, pBest, vel, ub0,
                  maxDiversity, fcs: FuzzyInertiaController_3L, w_set="O1"):
    """
    PSO con Fuzzy Controlled inertia weight.
    
    Parámetros:
        w_set (str): Set de funciones de pertenencia ('O1', 'O2', 'O3', etc.)
                     Si fcs tiene un w_set diferente, se crea uno nuevo localmente.
    """
    Vmax = 0.1 * ub0

    # Si el set del controlador no coincide, crear uno local
    if fcs.w_set.upper() != w_set.upper():
        fcs = FuzzyInertiaController_3L(wMin=fcs.wMin, wMax=fcs.wMax, w_set=w_set)

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

    step = advance_swarm(
        positions=population,
        velocities=vel,
        personal_best=pBest,
        global_best=best,
        inertia=w,
        cognitive_random=r1,
        social_random=r2,
        maximum_velocity=Vmax,
        config=PSOConfig(cognitive=2.0, social=2.0),
    )
    return step.positions, step.velocities, maxDiversity
