# WEA 2026 Paper Plan
## "Sensitivity Analysis of Fuzzy Rule Base Structure for Adaptive Inertia Weight Control in PSO"

**Conference:** WEA 2026 (Pereira, Colombia)  
**Track:** Track 2: Optimization (primary) — covers metaheuristics, computational methods, optimization and AI  
**Format:** CCIS Springer (LNCS style), indexed by Scopus  
**Submission:** Microsoft CMT - https://cmt3.research.microsoft.com/WEA2026/

---

## 1. Research Context: Three-Paper Series

This paper is the **third** in a series studying the **three independent axes** of a Mamdani Fuzzy Inference System (FIS) applied to adaptive inertia weight control in PSO:

| Paper | Conference | Axis Under Study | Fixed Components |
|-------|-----------|-------------------|------------------|
| OLA 2026 | OLA 2026 | **Output MFs** (w_set A/B/C/D) | Inputs: I1, Rules: R1 |
| CLEI 2026 | CLEI 2026 | **Input MFs** (I1/I2/I3/I4) × Granularity (3/5 labels) | Output: A, Rules: R1 |
| **WEA 2026** | **WEA 2026** | **Rule Base Structure** (R1–R6) × Granularity (3/5 labels) | Inputs: I1, Output: A |

**Key insight:** Each paper isolates one FIS component while controlling the others, enabling systematic factorial analysis of what drives performance in fuzzy-controlled metaheuristics.

---

## 2. Research Question

> **How does the structure of the fuzzy rule base affect the performance of fuzzy-controlled PSO when input and output membership functions are held constant?**

### Sub-questions:
1. Is the rule base the most, or least, influential FIS component for PSO performance?
2. Do certain rule "strategies" (exploration-biased, exploitation-biased, diversity-reactive, progress-reactive) consistently outperform others?
3. Is performance sensitivity to rule structure problem-dependent (unimodal vs. multimodal vs. composition functions)?
4. Does granularity (3 vs 5 labels) amplify or attenuate the effect of rule base structure?
5. Can we identify "robust" rule bases that perform well across diverse problem landscapes?

---

## 3. Rule Base Variants to Test

### 3.1. Three-Label System (3×3 = 9 rules)

With 3 input labels per variable × 3 output labels, each rule maps to {low, medium, high}, giving $3^9 = 19{,}683$ possible rule bases. We select **6 semantically meaningful** variants:

#### R1: Baseline (Current System)
```
Strategy: Explore-early, exploit-late, diversity-reactive
Rationale: Standard literature-inspired strategy. Balances both inputs with 
           progressive transition from exploration to exploitation.

            early    mid      late
low         high     low      low
medium      high     medium   low
high        high     high     medium
```

#### R2: Exploitation-Dominant
```
Strategy: Aggressively favor low inertia (exploitation)
Rationale: Prioritize convergence speed, rapid exploitation. Only high 
           diversity in early stages produces high w.

            early    mid      late
low         medium   low      low
medium      medium   low      low
high        high     medium   low
```

#### R3: Exploration-Dominant
```
Strategy: Aggressively favor high inertia (exploration)  
Rationale: Prioritize search space coverage, resist premature convergence.
           Almost always high w unless diversity is low in late stages.

            early    mid      late
low         high     high     medium
medium      high     high     high
high        high     high     high
```

#### R4: Diversity-Reactive (Progress-Agnostic)
```
Strategy: w depends ONLY on diversity, progress has NO effect
Rationale: Let population state drive adaptation entirely. The iteration 
           count is irrelevant; only the current diversity matters.

            early    mid      late
low         low      low      low
medium      medium   medium   medium
high        high     high     high
```

#### R5: Progress-Dominant (Diversity-Agnostic)
```
Strategy: w depends ONLY on progress, diversity has NO effect
Rationale: Classic decreasing-w schedule encoded as fuzzy rules. Mimics 
           linear decrease regardless of population state.

            early    mid      late
low         high     medium   low
medium      high     medium   low
high        high     medium   low
```

#### R6: Inverse (Counter-Intuitive)
```
Strategy: Opposite of R1 baseline - exploit early, explore late
Rationale: Control/sanity check. Output labels are mirrored from R1 
           (high↔low, medium stays). If this performs well, the rule 
           structure doesn't matter.

            early    mid      late
low         low      high     high
medium      low      medium   high
high        low      low      medium
```

### 3.2. Five-Label System (5×5 = 25 rules)

With 5 input labels × 5 output labels, $5^{25} \approx 2.98 \times 10^{17}$ possible rule bases. Same 6 semantic strategies, extended to finer granularity.

**Input labels:** very_low (VL), low (L), medium (M), high (H), very_high (VH)  
**Progress labels:** very_early (VE), early (E), mid (Mi), late (La), very_late (VLa)  
**Output labels:** very_low (vl), low (l), medium (m), high (h), very_high (vh)

#### R1-5L: Baseline (Current 5-Label System)
```
Strategy: Same as R1-3L but with finer granularity transitions.
           Current system from fuzzy_controller_w_5labels.py

              VE      E       Mi      La      VLa
very_low      vh      vh      h       h       m
low           vh      h       h       m       l
medium        h       h       m       l       vl
high          h       m       m       l       vl
very_high     m       m       l       vl      vl
```

#### R2-5L: Exploitation-Dominant
```
Strategy: Strong bias toward low w. Only extreme low diversity triggers 
           high w, and only in very early stages.

              VE      E       Mi      La      VLa
very_low      h       m       l       vl      vl
low           m       m       l       vl      vl
medium        m       l       l       vl      vl
high          m       l       vl      vl      vl
very_high     l       l       vl      vl      vl
```

#### R3-5L: Exploration-Dominant
```
Strategy: Strong bias toward high w. Only very late stages with high 
           diversity reduce w.

              VE      E       Mi      La      VLa
very_low      vh      vh      vh      h       h
low           vh      vh      h       h       m
medium        vh      h       h       m       m
high          vh      h       h       m       l
very_high     h       h       m       m       l
```

#### R4-5L: Diversity-Reactive (Progress-Agnostic)
```
Strategy: w = f(diversity) only. Each row is constant across all 
           progress stages.

              VE      E       Mi      La      VLa
very_low      vl      vl      vl      vl      vl
low           l       l       l       l       l
medium        m       m       m       m       m
high          h       h       h       h       h
very_high     vh      vh      vh      vh      vh
```

#### R5-5L: Progress-Dominant (Diversity-Agnostic)
```
Strategy: w = f(progress) only. Each column is constant across all 
           diversity levels. Mimics linear decrease.

              VE      E       Mi      La      VLa
very_low      vh      h       m       l       vl
low           vh      h       m       l       vl
medium        vh      h       m       l       vl
high          vh      h       m       l       vl
very_high     vh      h       m       l       vl
```

#### R6-5L: Inverse (Counter-Intuitive)
```
Strategy: Mirror of R1-5L. Output labels inverted: vh↔vl, h↔l, m stays.
           Exploit early, explore late.

              VE      E       Mi      La      VLa
very_low      m       m       l       l       vh
low           vl      l       l       m       h
medium        l       l       m       h       vh
high          l       m       m       h       vh
very_high     vl      vl      h       vh      vh
```

### 3.3. Rule Variant Summary

| ID | Label | Strategy | User Requirement |
|----|-------|----------|------------------|
| R1 | Baseline | Explore-early, exploit-late, balanced | **Balanced** ✓ |
| R2 | Exploitation | Aggressive low w bias | **Exploitation** ✓ |
| R3 | Exploration | Aggressive high w bias | **Exploration** ✓ |
| R4 | Diversity-Reactive | w = f(diversity) only | Additional: isolates diversity |
| R5 | Progress-Dominant | w = f(progress) only | Additional: isolates progress |
| R6 | Inverse | Opposite of R1 | Additional: sanity control |

**Note:** R1 (balanced), R2 (exploitation), R3 (exploration) directly fulfill the minimum 3-variant requirement. R4, R5, R6 provide additional analytical insight into which *input variable* is more important for the rule mapping.

---

## 4. Experimental Design

### Fixed Components (Control Variables)
- **Input MFs:** I1 (Standard symmetric triangular)
- **Output MFs:** Set A (Standard symmetric triangular)
- **Inference:** Mamdani (min-firing, max-aggregation)
- **Defuzzification:** Centroid (COG)
- **wMin = 0.0, wMax = 1.0**

### Two Granularity Levels
- **3 labels:** low/medium/high (9 rules per variant)
- **5 labels:** very_low/low/medium/high/very_high (25 rules per variant)

### PSO Parameters (Fixed — same as CLEI 2026)
- Population: 50
- Iterations: 500
- c1 = c2 = 2.0
- Runs per configuration: 31 (statistical significance)
- Seed: 42 (reproducible)

### Benchmark Functions (same as CLEI 2026)
| Function | Category | Dimension |
|----------|----------|-----------|
| F1 | Unimodal | 100 |
| F5 | Multimodal | 100 |
| F11 | Hybrid | 100 |
| F21 | Composition | 4 |
| F22 | Composition | 4 |
| F23 | Composition | 4 |

### Configurations

| Config | Granularity | Rule Set | Input | Output |
|--------|-------------|----------|-------|--------|
| PSO-STD | — | — | — | — |
| PSO-FCS-R1-3L | 3 labels | R1 | I1 | A |
| PSO-FCS-R2-3L | 3 labels | R2 | I1 | A |
| PSO-FCS-R3-3L | 3 labels | R3 | I1 | A |
| PSO-FCS-R4-3L | 3 labels | R4 | I1 | A |
| PSO-FCS-R5-3L | 3 labels | R5 | I1 | A |
| PSO-FCS-R6-3L | 3 labels | R6 | I1 | A |
| PSO-FCS-R1-5L | 5 labels | R1 | I1 | A |
| PSO-FCS-R2-5L | 5 labels | R2 | I1 | A |
| PSO-FCS-R3-5L | 5 labels | R3 | I1 | A |
| PSO-FCS-R4-5L | 5 labels | R4 | I1 | A |
| PSO-FCS-R5-5L | 5 labels | R5 | I1 | A |
| PSO-FCS-R6-5L | 5 labels | R6 | I1 | A |

### Total Experiments
- 12 fuzzy variants × 6 functions × 31 runs = **2,232 experiments**
- Plus baseline: 1 PSO-STD × 6 functions × 31 runs = **186 experiments**
- **Total: 2,418 experiments**

---

## 5. Statistical Analysis Plan

1. **Descriptive:** Mean, Std, CV%, IQR per (rule_variant × granularity, function)
2. **Non-parametric comparison:** Wilcoxon rank-sum test (paired, per function)
3. **Multiple comparison correction:** Holm-Bonferroni
4. **Effect size:** Cohen's d or Cliff's delta
5. **Ranking:** Friedman test + Nemenyi post-hoc (across all functions)
6. **By category:** Separate analysis for Unimodal / Multimodal / Composition
7. **Granularity effect:** Compare R_i-3L vs R_i-5L (does finer granularity amplify rule effects?)

---

## 6. Expected Visualizations

1. **Rule base heatmaps** (6×2 panels: R1–R6 for 3L and 5L) - visual comparison of rule structures
2. **Critical Difference (CD) diagram** - Nemenyi post-hoc ranking (all 13 configs)
3. **Boxplot grid** - Per-function comparison across configs
4. **w trajectory comparison** - How different rules produce different w profiles over time
5. **3L vs 5L paired comparison** - Same rule strategy, different granularity
6. **Convergence curves** - Selected representative functions
7. **Surface/heatmap response** - w output surface for each rule variant (diversity × progress → w)

---

## 7. Proposed Paper Structure (LNCS/CCIS, ~12-15 pages)

```
Title: Sensitivity Analysis of Fuzzy Rule Base Structure 
       for Adaptive Inertia Weight Control in PSO

1. Introduction                                          (~1.5 pages)
   - PSO and the inertia weight problem
   - Fuzzy logic for adaptive parameter control
   - Three-paper series context (OLA: output, CLEI: input, WEA: rules)
   - Research gap: rule base structure rarely studied in isolation
   - Contribution statement (3 points)

2. Related Work                                          (~1.5 pages)
   2.1 Adaptive Inertia Weight Strategies
   2.2 Fuzzy Logic in Metaheuristic Control
   2.3 Sensitivity Analysis of FIS Components

3. Fuzzy PSO Framework                                   (~2 pages)
   3.1 Standard PSO Formulation
   3.2 Mamdani FIS for Inertia Weight
   3.3 Input/Output Membership Functions (Fixed: I1, Set A)
   3.4 Rule Base as the Variable Under Study

4. Experimental Design                                   (~2 pages)
   4.1 Rule Base Variants (R1–R6): Semantic Justification
       - Table: 3-label rules (9 rules × 6 variants)
       - Table: 5-label rules (25 rules × 6 variants)
   4.2 CEC 2017 Benchmark Functions
   4.3 PSO Configuration and Baselines
   4.4 Statistical Methodology

5. Results and Discussion                                (~3.5 pages)
   5.1 Overall Ranking Across All Functions
   5.2 Performance by Function Category
   5.3 Statistical Significance Analysis
   5.4 Granularity Effect (3L vs 5L per rule strategy)
   5.5 Inertia Weight Behavior Analysis

6. Conclusions and Future Work                           (~1 page)
   - Key findings 
   - Practical recommendations for rule design
   - Future: combine best rule base (WEA) + best input MFs (CLEI) 
     + best output MFs (OLA) → fully optimized FIS

References                                               (~1 page)
```

**Estimated total:** 12.5 pages (within CCIS guidelines)

---

## 8. Key Contribution Claims

1. **First systematic study** isolating fuzzy rule base structure effects on PSO performance while controlling input/output MFs
2. **Six semantically-grounded rule variants** (exploration, exploitation, balanced, diversity-reactive, progress-dominant, inverse) tested at **two granularity levels** (3 and 5 labels)
3. **Consistent evaluation** using same benchmarks, parameters, and methodology as companion papers (OLA/CLEI), enabling cross-paper comparison of FIS component importance
4. **Practical design guideline**: which rule "philosophy" to adopt depending on optimization problem characteristics

---

## 9. Keywords

Particle Swarm Optimization, Fuzzy Logic, Mamdani FIS, Inertia Weight, Rule Base, Sensitivity Analysis, CEC 2017, Metaheuristics
