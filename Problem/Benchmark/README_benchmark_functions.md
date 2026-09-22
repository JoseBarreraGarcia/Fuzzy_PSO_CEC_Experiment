# Benchmark Functions Reference

This document describes the three groups of benchmark functions available in this framework, their mathematical origins, global optima, search bounds, valid dimensions, and how to configure them in `config/experiments.json`.

---

## Group 1 — Classical Benchmark Suite (F1–F23)

### Origin and Reference

This 23-function suite is the standard benchmark set widely used in the swarm intelligence and metaheuristics literature. The canonical reference used in this project is:

> Abualigah, L., Diabat, A., Mirjalili, S., Abd Elaziz, M., & Gandomi, A. H. (2021).
> **The Arithmetic Optimization Algorithm**.
> *Computer Methods in Applied Mechanics and Engineering*, 376, 113609.
> https://doi.org/10.1016/j.cma.2020.113609

The individual functions originate from earlier CEC competitions and classical papers (indicated per function below). The Python implementation in this project is in `Problem/Benchmark/Problem.py`.

### Characteristics

- **F1–F7**: Unimodal. A single global minimum. Used to test convergence speed and exploitation.
- **F8–F13**: Multimodal (scalable). Many local minima that scale with dimension. Used to test exploration.
- **F14–F23**: Multimodal (fixed dimension). Classic low-dimensional functions with known analytic optima.

### Function Table

| ID | Name | Dim | Bounds | Optimum | Notes |
|----|------|-----|--------|---------|-------|
| F1 | Sphere | Any | [-100, 100] | 0 | CEC 2005 F1. Simplest unimodal. |
| F2 | Schwefel 2.22 | Any | [-10, 10] | 0 | Unimodal, non-separable. |
| F3 | Schwefel 1.2 (Rotated Hyper-Ellipsoid) | Any | [-100, 100] | 0 | CEC 2005 F2. Unimodal, non-separable. |
| F4 | Schwefel 2.21 (MaxMod) | Any | [-100, 100] | 0 | CEC 2008 F2. |
| F5 | Rosenbrock | Any | [-30, 30] | 0 | CEC 2005 F6. Narrow valley. |
| F6 | Shifted Step | Any | [-100, 100] | 0 | CEC 2005 F1 variant. |
| F7 | Quartic with Noise | Any | [-1.28, 1.28] | 0 | Stochastic due to uniform noise. |
| F8 | Schwefel 2.26 | Any | [-500, 500] | −418.9829 × dim | Deceptive multimodal. Optimo depends on dim. |
| F9 | Rastrigin | Any | [-5.12, 5.12] | 0 | CEC 2005 F9. Highly multimodal. |
| F10 | Ackley | Any | [-32, 32] | 0 | CEC 2014 F5. |
| F11 | Griewank | Any | [-600, 600] | 0 | CEC 2014 F7. |
| F12 | Generalized Penalized 1 | Any | [-50, 50] | 0 | |
| F13 | Generalized Penalized 2 | Any | [-50, 50] | 0 | |
| F14 | Shekel's Foxholes | **2** | [-65.536, 65.536] | 1 | Fixed dim. `aS` matrix is 2×25. |
| F15 | Kowalik | **4** | [-5, 5] | 0.00030 | Fixed dim. Uses `L[0]..L[3]` explicitly. |
| F16 | Six-Hump Camel-Back | **2** | [-5, 5] | −1.0316 | Fixed dim. Uses `L[0]` and `L[1]` only. |
| F17 | Branin's RCOS | **2** | [-5, 5] | 0.398 | Fixed dim. Uses `L[0]` and `L[1]` only. |
| F18 | Goldstein-Price | **2** | [-2, 2] | 3 | Fixed dim. |
| F19 | Hartmann 3D | **3** | [0, 1] | −3.86 | Fixed dim. `aH` matrix is 4×3. |
| F20 | Hartmann 6D | **6** | [0, 1] | −3.32 | Fixed dim. `aH` matrix is 4×6. |
| F21 | Shekel-5 | **4** | [0, 10] | −10.1532 | Fixed dim. Shekel variant with 5 terms. |
| F22 | Shekel-7 | **4** | [0, 10] | −10.4029 | Fixed dim. Shekel variant with 7 terms. |
| F23 | Shekel-10 | **4** | [0, 10] | −10.5364 | Fixed dim. Shekel variant with 10 terms. |

> **Note on F8**: The stored optimum in the database is −418.9829 (per-dimension value). For dim=100 the true optimum is −41898.29. The solver searches for minimum.

### Configuration in `experiments.json`

```json
"dimensiones": {
    "BEN": {
        "F1": [30, 100],
        "F5": [100],
        "F8": [100],
        "F14": [2],
        "F15": [4],
        "F16": [2],
        "F17": [2],
        "F18": [2],
        "F19": [3],
        "F20": [6],
        "F21": [4],
        "F22": [4],
        "F23": [4]
    }
},
"instancias": {
    "BEN": ["F1", "F5", "F8", "F14", "F16", "F21", "F22", "F23"]
}
```

Rules:
- F1–F13: dimension is free. Typical values: 30, 50, 100. Multiple dimensions accepted: `[30, 100]` creates one experiment per dimension.
- F14–F23: dimension is **fixed by the formula**. Using any other value will produce shape errors or mathematically incorrect results.

---

## Group 2 — IEEE CEC 2017 Benchmark Suite (F1CEC2017–F30CEC2017)

### Origin and Reference

> Wu, G., Mallipeddi, R., & Suganthan, P. N. (2017).
> **Problem Definitions and Evaluation Criteria for the CEC 2017 Special Session and Competition on Single Objective Real-Parameter Numerical Optimization**.
> Technical Report, Nanyang Technological University, Singapore.
> Competition URL: https://www.ntu.edu.sg/home/epnsugan/index_files/CEC2017/CEC2017.htm

The Python implementation used in this project is by **Duncan Tilley** (MIT License), available at:
> https://github.com/dmolokanov/cec2017

Source files: `Problem/Benchmark/CEC/cec2017/` (simple.py, hybrid.py, composition.py, functions.py, transforms.py, basic.py)

### Characteristics

- All functions are **shifted and rotated** using official matrices from the competition.
- Rotation matrices and shift vectors are preloaded for dimensions: **2, 10, 20, 30, 50, 100** only.
- Global optima follow the pattern: $f^* = i \times 100$ for function $f_i$.
- Search space is **always** [−100, 100] for all dimensions.

### Function Table

| ID in config | CEC2017 | Type | Name | f* | Notes |
|---|---|---|---|---|---|
| F1CEC2017 | f1 | Simple | Shifted & Rotated Bent Cigar | 100 | |
| F2CEC2017 | f2 | Simple | (Deprecated) Sum of Different Power | 200 | Removed from official suite post-2017 |
| F3CEC2017 | f3 | Simple | Shifted & Rotated Zakharov | 300 | |
| F4CEC2017 | f4 | Simple | Shifted & Rotated Rosenbrock | 400 | |
| F5CEC2017 | f5 | Simple | Shifted & Rotated Rastrigin | 500 | |
| F6CEC2017 | f6 | Simple | Shifted & Rotated Schaffer F7 | 600 | |
| F7CEC2017 | f7 | Simple | Shifted & Rotated Lunacek Bi-Rastrigin | 700 | |
| F8CEC2017 | f8 | Simple | Shifted & Rotated Non-Cont. Rastrigin | 800 | |
| F9CEC2017 | f9 | Simple | Shifted & Rotated Levy | 900 | |
| F10CEC2017 | f10 | Simple | Shifted & Rotated Schwefel | 1000 | |
| F11CEC2017 | f11 | Hybrid (N=3) | Zakharov + Rosenbrock + Rastrigin | 1100 | |
| F12CEC2017 | f12 | Hybrid (N=3) | Elliptic + Schwefel + Bent Cigar | 1200 | |
| F13CEC2017 | f13 | Hybrid (N=3) | Bent Cigar + Rosenbrock + LIWZ | 1300 | |
| F14CEC2017 | f14 | Hybrid (N=4) | Schwefel + H-G Bat + Rosenbrock + Elliptic | 1400 | |
| F15CEC2017 | f15 | Hybrid (N=4) | Bent Cigar + H-G Bat + Rastrigin + Rosenbrock | 1500 | |
| F16CEC2017 | f16 | Hybrid (N=4) | Expanded Schaffer + H-G Bat + Rosenbrock + Schwefel | 1600 | |
| F17CEC2017 | f17 | Hybrid (N=5) | Elliptic + Rastrigin + Ackley + Schwefel + Rosenbrock | 1700 | |
| F18CEC2017 | f18 | Hybrid (N=5) | Bentcigar + Rastrigin + Schwefel + H-G Bat + LIWZ | 1800 | |
| F19CEC2017 | f19 | Hybrid (N=5) | Bent Cigar + Rastrigin + Schwefel + Ackley + LIWZ | 1900 | |
| F20CEC2017 | f20 | Hybrid (N=6) | H-G Bat + Rastrigin + Schwefel + Rosenbrock + Ackley + Elliptic | 2000 | |
| F21CEC2017 | f21 | Composition (N=3) | Rosenbrock + High Cond. Elliptic + Rastrigin | 2100 | |
| F22CEC2017 | f22 | Composition (N=3) | Rastrigin + Griewank + Modified Schwefel | 2200 | |
| F23CEC2017 | f23 | Composition (N=4) | Rosenbrock + Ackley + Modified Schwefel + Rastrigin | 2300 | |
| F24CEC2017 | f24 | Composition (N=4) | Ackley + Elliptic + Griewank + Rastrigin | 2400 | |
| F25CEC2017 | f25 | Composition (N=5) | Rastrigin + Happy Cat + Ackley + Discus + Rosenbrock | 2500 | |
| F26CEC2017 | f26 | Composition (N=5) | Schaffer F6 + Schwefel + Griewank + Rosenbrock + Rastrigin | 2600 | |
| F27CEC2017 | f27 | Composition (N=6) | H-G Bat + Rastrigin + Schwefel + Bent Cigar + Elliptic + Schaffer F6 | 2700 | |
| F28CEC2017 | f28 | Composition (N=6) | Ackley + Griewank + Discus + Rosenbrock + Happy Cat + Schaffer F6 | 2800 | |
| F29CEC2017 | f29 | Composition (N=3, hybrid) | Hybrid f15 + f16 + f17 | 2900 | Uses shuffles |
| F30CEC2017 | f30 | Composition (N=3, hybrid) | Hybrid f15 + f18 + f19 | 3000 | Uses shuffles |

### Valid Dimensions

Only the following dimensions are supported (rotation/shift matrices are precomputed for these):

| Dimension | Notes |
|-----------|-------|
| 2 | Very low-dimensional, mostly for visualization |
| 10 | Low-dimensional |
| 20 | Medium |
| 30 | Standard competition dimension |
| 50 | Large |
| 100 | Very large |

**Using any other dimension (e.g., 7, 15, 200) will raise an IndexError** when accessing `transforms.rotations[nx]`.

### Configuration in `experiments.json`

```json
"dimensiones": {
    "BEN": {
        "F1CEC2017": [30],
        "F5CEC2017": [30],
        "F10CEC2017": [10, 30],
        "F24CEC2017": [10],
        "F28CEC2017": [30],
        "F30CEC2017": [30]
    }
},
"instancias": {
    "BEN": ["F1CEC2017", "F5CEC2017", "F10CEC2017", "F24CEC2017", "F28CEC2017", "F30CEC2017"]
}
```

> **Note on F2CEC2017**: This function was officially deprecated from the CEC 2017 suite after publication. The implementation prints a deprecation warning when called. It is available but not recommended for publications.

---

## Group 3 — opfunu Library Functions

### Origin and Reference

Functions accessed via the `opfunu` library (pip package):

> Kumar, A., Wu, G., Ali, M. Z., Mallipeddi, R., Suganthan, P. N., & Das, S. (2020).
> **A test-suite of non-convex constrained optimization problems from the real-world and some baseline results**.
> *Swarm and Evolutionary Computation*, 56, 100693.

Library: https://github.com/thieu1995/opfunu

These functions cover CEC competitions from 2005 to 2022. Bounds and optima are read automatically from the library at database population time (`insertarInstanciasBEN()` in `BD/sqlite.py`).

### Available Functions (configured in `BD/sqlite.py`)

| CEC Year | Functions available |
|----------|-------------------|
| CEC 2005 | F32005, F72005, F122005, F132005, F172005, F232005 |
| CEC 2008 | F22008, F32008, F42008, F52008, F62008, F72008 |
| CEC 2010 | F12010, F42010, F102010, F132010, F162010, F172010 |
| CEC 2013 | F32013, F52013, F72013, F132013, F242013, F262013 |
| CEC 2014 | F12014, F32014, F62014, F162014, F242014, F292014 |
| CEC 2015 | F12015, F22015, F62015, F72015, F102015, F112015 |
| CEC 2017 | F12017, F22017, F192017, F242017, F272017, F292017 |
| CEC 2019 | F12019, F22019, F32019, F42019, F52019, F92019 |
| CEC 2020 | F12020, F32020, F42020, F72020, F92020, F102020 |
| CEC 2021 | F12021, F22021, F42021, F52021, F62021, F102021 |
| CEC 2022 | F12022, F22022, F82022, F92022, F112022, F122022 |

### Configuration in `experiments.json`

```json
"dimensiones": {
    "BEN": {
        "F12017": [30],
        "F242017": [10, 30]
    }
},
"instancias": {
    "BEN": ["F12017", "F242017"]
}
```

Dimensions for opfunu functions depend on each function's internal `dim_default`. If no entry exists in `dimensiones["BEN"]`, the pipeline falls back to `func_class().dim_default` automatically (see `obtener_dimensiones_ben()` in `1_0_poblarDB.py`).

---

## Dimension Configuration Rules Summary

| Group | Dimension | Config key format | Example |
|-------|-----------|-------------------|---------|
| Classical | Free (F1–F13) | `"FN": [dim1, dim2, ...]` | `"F1": [30, 100]` |
| Classical | Fixed (F14–F23) | Must match formula | `"F14": [2]` |
| CEC 2017 | Only 2,10,20,30,50,100 | `"FNCEC2017": [dim]` | `"F5CEC2017": [30]` |
| opfunu | Varies by function | `"FNyear": [dim]` or omit for default | `"F12017": [30]` |

Using a list with multiple values (e.g., `[10, 30, 100]`) creates **one independent experiment per dimension**.

---

## How Dimensions Flow Through the Pipeline

```
experiments.json → 1_0_poblarDB.py
    dimensiones["BEN"]["F5"] = [100]
        ↓
    experiment record stored as: "F5 100"
        ↓
2_main.py
    dim = int("F5 100".split(" ")[1])  # → 100
        ↓
Solver/solverBEN.py
    lb = [-30] * 100
    ub = [30] * 100
    population.shape = (pop, 100)
```

---

## Key Files

| File | Role |
|------|------|
| `Problem/Benchmark/Problem.py` | F1–F23 implementations + fitness dispatcher |
| `Problem/Benchmark/CEC/cec2017/simple.py` | CEC2017 f1–f10 (Simple) |
| `Problem/Benchmark/CEC/cec2017/hybrid.py` | CEC2017 f11–f20 (Hybrid) |
| `Problem/Benchmark/CEC/cec2017/composition.py` | CEC2017 f21–f30 (Composition) |
| `Problem/Benchmark/CEC/cec2017/transforms.py` | Rotation/shift/shuffle matrices |
| `BD/sqlite.py` | `insertarInstanciasBEN()` — stores bounds + optima in DB |
| `config/experiments.json` | `dimensiones` + `instancias` — selects which functions to run |
