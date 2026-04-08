# Experimental Configuration: Adaptive PSO with Fuzzy Logic Inertia Weight Control

**OLA 2026 Conference Submission**

---

## 1. Introduction

This document describes the complete experimental setup for evaluating Particle Swarm Optimization (PSO) enhanced with Mamdani Fuzzy Inference System (FIS) for inertia weight ($w$) control. The study investigates how fuzzy logic-based adaptation of PSO parameters can improve convergence and solution quality across continuous optimization benchmarks.

---

## 2. Algorithm Configuration

### 2.1 Standard PSO (Baseline)

**Parameters:**
```
Population size:      Pop = 50 particles
Inertia weight:       w = 0.7298 (fixed)
Cognitive coefficient: c₁ = 1.49618
Social coefficient:    c₂ = 1.49618
Maximum iterations:    MaxIter = 1000
```

**Velocity Update Equation:**
$$v_i(t+1) = w \cdot v_i(t) + c_1 \cdot \text{rand}() \cdot (p_{best,i} - x_i(t)) + c_2 \cdot \text{rand}() \cdot (g_{best} - x_i(t))$$

**Position Update:**
$$x_i(t+1) = x_i(t) + v_i(t+1)$$

**Termination Criteria:**
- Maximum iterations reached (1000)
- Function evaluations budget: NFE = Pop × MaxIter = 50,000

### 2.2 Fuzzy-Controlled PSO (PSO_FCS)

#### 2.2.1 Mamdani Fuzzy Inference System Architecture

**Input 1: Population Diversity Ratio** ($d_{\text{ratio}}$)
$$d_{\text{ratio}} = \frac{1}{D} \sum_{k=1}^{D} \frac{\max_k(x_{i,k}) - \min_k(x_{i,k})}{\text{SearchSpace}_k}$$

Where:
- $D$ = problem dimension
- $k$ = dimension index
- Normalized to [0, 1]

**Input Membership Functions:**
| Term | Range | Membership |
|------|-------|-----------|
| Low | [0.0, 0.4] | Triangular(0.0, 0.2, 0.4) |
| Medium | [0.3, 0.7] | Triangular(0.3, 0.5, 0.7) |
| High | [0.6, 1.0] | Triangular(0.6, 0.8, 1.0) |

**Input 2: Iteration Progress** ($t_{\text{progress}}$)
$$t_{\text{progress}} = \frac{\text{current iteration}}{\text{max iterations}}$$

Normalized to [0, 1]

**Input Membership Functions:**
| Term | Range | Membership |
|------|-------|-----------|
| Early | [0.0, 0.4] | Triangular(0.0, 0.2, 0.4) |
| Mid | [0.3, 0.7] | Triangular(0.3, 0.5, 0.7) |
| Late | [0.6, 1.0] | Triangular(0.6, 0.8, 1.0) |

**Output: Inertia Weight** ($w$)

Mapped to user-defined range $[w_{\min}, w_{\max}]$. Standard range: [0.1, 0.9]

**Output Membership Functions - Set A (Conservative)**
| Term | Normalized Range | Membership |
|------|---------|-----------|
| Low | [0.00, 0.50] | Triangular(0.00, 0.25, 0.50) |
| Medium | [0.25, 0.75] | Triangular(0.25, 0.50, 0.75) |
| High | [0.50, 1.00] | Triangular(0.50, 0.75, 1.00) |

**Output Membership Functions - Set B (Balanced)**
| Term | Normalized Range | Membership |
|------|---------|-----------|
| Low | [0.25, 0.50] | Triangular(0.25, 0.25, 0.50) [shoulder] |
| Medium | [0.25, 0.75] | Triangular(0.25, 0.50, 0.75) |
| High | [0.50, 0.75] | Triangular(0.50, 0.75, 0.75) [shoulder] |

**Output Membership Functions - Set C (Exploratory)**
| Term | Normalized Range | Membership |
|------|---------|-----------|
| Low | [0.10, 0.40] | Triangular(0.10, 0.25, 0.40) |
| Medium | [0.35, 0.65] | Triangular(0.35, 0.50, 0.65) |
| High | [0.60, 0.90] | Triangular(0.60, 0.75, 0.90) |

**Output Membership Functions - Set D (Aggressive)**
| Term | Normalized Range | Membership |
|------|---------|-----------|
| Low | [0.00, 0.40] | Triangular(0.00, 0.20, 0.40) |
| Medium | [0.20, 0.65] | Triangular(0.20, 0.50, 0.65) |
| High | [0.60, 0.80] | Triangular(0.60, 0.80, 0.80) [shoulder] |

#### 2.2.2 Fuzzy Inference Rules

**3×3 Rule Matrix (Mamdani):**

| Diversity \ Progress | Early | Mid | Late |
|-----------|-------|-----|------|
| **Low** | High | Medium | Low |
| **Medium** | High | Medium | Medium |
| **High** | Medium | Medium | Low |

**Interpretation:**
- **Early + Low Diversity**: $w_{\text{High}}$ → Encourage exploration
- **Late + High Diversity**: $w_{\text{Low}}$ → Encourage exploitation
- **Mid iterations**: $w_{\text{Medium}}$ → Balanced approach

#### 2.2.3 Defuzzification

**Method:** Center of Gravity (COG)
$$w_{\text{COG}} = \frac{\sum_i \mu_i(z) \cdot z_i}{\sum_i \mu_i(z)}$$

Where:
- $\mu_i(z)$ = degree of membership
- $z_i$ = output sample points

---

## 3. Benchmark Problems

### 3.1 Continuous Optimization: CEC2017 Benchmark Suite

**Standard:** CEC2017 Special Session on Real-Parameter Optimization (IEEE Congress on Evolutionary Computation)

**Functions Evaluated:** 23 functions (F1-F23)

#### 3.1.1 Problem Categories and Dimensions

| Category | Functions | Characteristics | Dimension (D) |
|----------|-----------|-----------------|----------------|
| Unimodal | F1-F4 | Convex, continuous | 10, 30, 50 |
| Multimodal | F5-F10 | Multiple local optima, high complexity | 10, 30, 50 |
| Hybrid | F11-F20 | Mixed characteristics, increased difficulty | 10, 30, 50 |
| Composition | F21-F23 | Shifted, rotated, composition functions | 10, 30, 50 |

#### 3.1.2 Function Details (Subset)

**F1: Sphere Function**
$$f(\mathbf{x}) = \sum_{i=1}^{D} x_i^2$$
- Optimum: $f(\mathbf{x}^*) = 100$
- Search space: $[-100, 100]^D$
- Properties: Simple, unimodal, separable

**F4: Shifted Elliptic Function**
$$f(\mathbf{x}) = \sum_{i=1}^{D} (10^6)^{\frac{i-1}{D-1}} x_i^2$$
- Optimum: $f(\mathbf{x}^*) = 400$
- Search space: $[-100, 100]^D$
- Properties: Multimodal, condition number 10⁶

**F10: Shifted Rosenbrock Function**
$$f(\mathbf{x}) = \sum_{i=1}^{D-1} [100(x_{i+1} - x_i^2)^2 + (x_i - 1)^2]$$
- Optimum: $f(\mathbf{x}^*) = 500$
- Search space: $[-100, 100]^D$
- Properties: Narrow valley, difficult optimization landscape

**F21: Shifted Sphere Function (Rotated)**
- Optimum: $f(\mathbf{x}^*) = -10.1532$
- Search space: $[-5, 5]^D$
- Properties: Rotated, shifted variant

**F22: Shifted Sphere Function (Rotated, Composition)**
- Optimum: $f(\mathbf{x}^*) = -10.4028$
- Search space: $[-5, 5]^D$
- Properties: Composition of multiple functions

**F23: Shifted Sphere Function (Shifted, Scaled)**
- Optimum: $f(\mathbf{x}^*) = -10.5363$
- Search space: $[-5, 5]^D$
- Properties: Complex composition structure

---

## 4. Experimental Design

### 4.1 Study Scope

**Objective:** Compare PSO with fuzzy inertia weight control (4 fuzzy sets) against standard PSO across CEC2017 benchmarks.

**Algorithms Evaluated:**
1. PSO (baseline, standard parameters)
2. PSO_FCS:A (Fuzzy-Controlled PSO, Set A - conservative)
3. PSO_FCS:B (Fuzzy-Controlled PSO, Set B - balanced)
4. PSO_FCS:C (Fuzzy-Controlled PSO, Set C - exploratory)
5. PSO_FCS:D (Fuzzy-Controlled PSO, Set D - aggressive)

**Total configurations: 5 algorithms**

### 4.2 Benchmark Functions

**All 23 CEC2017 functions (F1-F23)**
- Dimensions tested: D = 10, 30, 50 (primary analysis: D=10)
- Total function evaluations per run: 50,000 (Pop=50, MaxIter=1000)

### 4.3 Statistical Methodology

**Number of Independent Runs:** 31 runs per algorithm-function combination

**Rationale:** 
- Sufficient sample size for statistical testing ($n=31 \geq 30$)
- Enables t-tests and effect size analysis
- Matches standard convention in CEC competitions

**Random Initialization:**
- Each run uses different random seed
- Initial positions: uniform random in $[-100, 100]^D$
- Initial velocities: $v_i(0) = 0$

### 4.4 Performance Metrics

#### 4.4.1 Solution Quality

**Final Best Fitness:**
$$f_{\text{best}} = \min_{i=1}^{31} f(\mathbf{x}_{\text{best},i})$$

**Gap to Optimum (percentage):**
$$\text{Gap\%} = \frac{|f_{\text{best}} - f_{\text{optimum}}|}{|f_{\text{optimum}}|} \times 100$$

**Mean Gap (across 31 runs):**
$$\text{Gap\%}_{\text{mean}} = \frac{1}{31} \sum_{i=1}^{31} \text{Gap\%}_i$$

**Standard Deviation:**
$$\sigma = \sqrt{\frac{1}{30} \sum_{i=1}^{31} (\text{Gap\%}_i - \text{Gap\%}_{\text{mean}})^2}$$

Note: Using $n-1=30$ for sample standard deviation (unbiased estimator)

#### 4.4.2 Convergence Behavior

**Convergence Curve:** Best fitness vs. iteration (tracked every iteration)

**Generation Gap:** Fitness improvement per generation

**Stagnation Detection:** Iterations without improvement

#### 4.4.3 Computational Cost

**Wall-clock Time:** Execution time (seconds) on reference hardware
- CPU: Intel Core i7 or equivalent
- Memory: 16 GB RAM
- Python version: 3.11+

**Function Evaluations (NFE):**
$$\text{NFE} = \text{Population Size} \times \text{Iterations} = 50 \times 1000 = 50,000$$

---

## 5. Experimental Setup and Data Collection

### 5.1 Database Schema

**Table: experiments**
- `id_experimento` (PRIMARY KEY)
- `experimento` (Experiment name: PSO, PSO_FCS, etc.)
- `MH` (Metaheuristic: PSO, PSO_FCS)
- `paramMH` (JSON: inertia weight set: A, B, C, D)
- `estado` (Status: pending, executing, completed, error)
- `fk_id_instancia` (Foreign key to benchmark function)

**Table: instancias**
- `id_instancia` (PRIMARY KEY)
- `tipo_problema` (BEN for benchmark)
- `nombre` (F1, F2, ..., F23)
- `dimension` (10, 30, 50)
- `optimo` (Known optimum value)

**Table: resultados**
- `id_resultado` (PRIMARY KEY)
- `fitness` (Final best value found)
- `gap_optimo_pct` (Percentage gap to optimum)
- `tiempoEjecucion` (Wall-clock time in seconds)
- `solucion` (Best solution vector)
- `fk_id_experimento` (Foreign key to experiments)

**Table: iteraciones**
- `id_archivo` (PRIMARY KEY)
- `nombre` (CSV filename)
- `archivo` (CSV data: iteration, fitness, diversity, w_value)
- `fk_id_experimento` (Foreign key to experiments)

### 5.2 Data Collection Process

**Workflow:**
1. **Initialization:** Populate database with experiment configurations from JSON
   ```bash
   python reiniciarDB.py    # Reset database
   python poblarDB.py       # Populate with experiment configs
   ```

2. **Execution:** Run all experiments
   ```bash
   python main.py           # Execute all pending experiments
   ```
   
   For each experiment:
   - Load PSO/PSO_FCS parameters
   - Initialize population
   - Log iteration data to CSV (diversity, $w$, fitness)
   - Store final results to database
   
3. **Analysis:** Generate reports and visualizations
   ```bash
   python analisis.py       # Generate level 1-3 analysis
   ```

### 5.3 Key Data Points per Run

**Per-Iteration Logging (1000 data points):**
- Iteration number
- Current best fitness
- Population diversity ratio
- Inertia weight value ($w_t$)
- Number of function evaluations (NFE)

**Final Results:**
- Best fitness achieved
- Gap to optimum (%)
- Execution time
- Diversity at convergence
- Number of iterations to convergence

---

## 6. Fuzzy Set Characteristics (Graphical Analysis)

### 6.1 Output Membership Functions by Set

All sets map diversity and iteration progress to inertia weight in range $[w_{\min}, w_{\max}] = [0.1, 0.9]$

**Set A (Conservative):**
- Focuses on exploitation in later iterations
- Lower $w$ values for mid-to-late stages
- Suitable for problems with clear optima nearby

**Set B (Balanced):**
- Even distribution of membership functions
- Smooth transition between exploration/exploitation
- Default configuration for general-purpose optimization

**Set C (Exploratory):**
- Emphasis on exploration across all iterations
- Higher $w$ values even in late stages
- Good for multimodal, deceptive problems

**Set D (Aggressive):**
- Extreme exploration in early iterations
- Rapid transition to exploitation
- Aggressive convergence strategy

### 6.2 Visualization

See `FUZZY/plots/`:
- `01_fuzzy_input_diversity_3labels.png` - Diversity membership functions
- `02_fuzzy_input_progress_3labels.png` - Iteration progress membership functions
- `03_fuzzy_output_w_set_A_3labels.png` through `03_fuzzy_output_w_set_D_3labels.png` - Output functions per set
- `05_fuzzy_w_sets_comparison_3labels.png` - All sets side-by-side comparison

---

## 7. Expected Outcomes and Validation

### 7.1 Research Questions

1. **Does fuzzy logic adaptation improve PSO convergence?**
   - Compare mean fitness gaps across all functions
   - Analyze convergence curves

2. **Which fuzzy set is most effective?**
   - Rank sets A-D by average performance
   - Identify problem characteristics where each set excels

3. **What is the computational overhead?**
   - Compare execution times (PSO vs PSO_FCS)
   - Estimate fuzzy evaluation cost

### 7.2 Evaluation Criteria

**Statistical Significance:**
- Paired t-tests (PSO vs each PSO_FCS variant)
- Effect sizes (Cohen's $d$)
- Significance level: $\alpha = 0.05$

**Performance Ranking:**
- Average fitness across functions
- Percentage of problems where algorithm is best
- Robustness measure (low standard deviation)

**Scalability:**
- Performance across dimensions D = 10, 30, 50
- Computational cost scaling

---

## 8. Configuration Summary Table

| Parameter | Value | Notes |
|-----------|-------|-------|
| Population Size | 50 | Standard PSO benchmark |
| Max Iterations | 1000 | Total NFE = 50,000 |
| Inertia Weight (PSO) | 0.7298 | Fixed, validated baseline |
| Cognitive/Social Coeff. | 1.49618 | Constriction factor: χ = 0.7298 |
| Fuzzy Sets | A, B, C, D | See Section 2.2.1 |
| Diversity Metric | Per-dimension normalized | [0, 1] range |
| Defuzzification | Center of Gravity | Standard Mamdani |
| Benchmark Suite | CEC2017 | 23 functions |
| Dimensions | 10, 30, 50 | Focus: D=10 |
| Independent Runs | 31 | Per algorithm-function |
| Total Experiments | 5 algorithms × 23 functions × 31 runs = 3,565 |
| Performance Metric | Gap to Optimum (%) | Normalized, comparable |

---

## 9. Software and Reproducibility

### 9.1 Implementation

- **Language:** Python 3.11+
- **Key Libraries:** NumPy, Matplotlib, SQLite3
- **Version Control:** Git repository
- **Database:** SQLite (deterministic, portable)

### 9.2 Reproducibility

**Random Seed Management:**
- Seed reproducibility through run ID
- All 31 runs per algorithm use different seeds
- Randomness only in initialization, diversity calculation is deterministic

**Configuration File:**
```json
{
  "ben": true,
  "mhs": ["PSO", "PSO_FCS"],
  "mh_params": {
    "PSO_FCS": [
      {"w_set": "A"},
      {"w_set": "B"},
      {"w_set": "C"},
      {"w_set": "D"}
    ]
  },
  "dimensions": [10, 30, 50]
}
```

### 9.3 Code Availability

All code available in repository:
- PSO implementations: `Metaheuristics/Codes/PSO.py`, `PSO_FCS.py`
- Fuzzy controller: `FUZZY/fuzzy_controller_w.py`
- Benchmark functions: `Problem/Benchmark/`
- Main executor: `Solver/solverBEN.py`
- Analysis: `analysis_modules_cec/`

---

## 10. References and Standards

**CEC2017 Benchmark:**
- Special Session on Real-Parameter Single-Objective Optimization
- IEEE Congress on Evolutionary Computation 2017
- Available: https://github.com/P-N-Suganthan/CEC2017

**PSO Standards:**
- Clerc, M., & Kennedy, J. (2002). The particle swarm-explosion, stability, and convergence in a multidimensional complex space.
- Inertia weight: Standard IEEE benchmark value

**Fuzzy Logic:**
- Mamdani, E. H. (1974). Applications of fuzzy algorithms for control of simple dynamic plant.
- Defuzzification: Standard COG method

---

## Appendix: File Structure

```
Solver_CEC/
├── FUZZY/
│   ├── fuzzy_controller_w.py          # 3-label FIS, Sets A-D
│   ├── fuzzy_plots.py                 # Visualization generation
│   ├── ola2026/                       # Conference submission materials
│   │   ├── 01_Experimental_Configuration.md  # This document
│   │   ├── 02_Results_Summary.md
│   │   └── 03_Figures_Description.md
│   └── plots/                         # Generated visualizations
├── Metaheuristics/Codes/
│   ├── PSO.py                         # Standard PSO implementation
│   └── PSO_FCS.py                     # Fuzzy-controlled PSO
├── Problem/Benchmark/                 # CEC2017 functions
├── Solver/
│   └── solverBEN.py                   # Main solver execution
├── BD/
│   ├── sqlite.py                      # Database schema
│   └── resultados.db                  # Experimental results
└── analysis_modules_cec/              # Analysis and visualization

Total Experiments: 3,565 runs
Total Function Evaluations: 178.25 million
Execution Time: ~48 hours (parallel on 8-core CPU)
```

---

**Document Version:** 1.0  
**Date:** January 2026  
**Prepared for:** OLA 2026 Conference Submission

