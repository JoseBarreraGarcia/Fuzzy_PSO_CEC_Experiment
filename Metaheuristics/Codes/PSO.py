import numpy as np

from afcs.optimizers.pso import LegacyLinearInertia, PSOConfig, advance_swarm

def iterarPSO(maxIter, iter, dim, population, best, pBest, vel, ub0):
    """
    Particle Swarm Optimization (PSO) - Optimized with NumPy.
    """
    
    Vmax = ub0 * 0.1
    w = LegacyLinearInertia(max_iterations=maxIter).value_at(iter)

    # Generate random values r1 and r2 for all particles and dimensions
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
    return step.positions, step.velocities
