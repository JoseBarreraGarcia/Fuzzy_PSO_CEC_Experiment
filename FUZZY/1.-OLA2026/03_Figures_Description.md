# Figures and Visualizations Guide

**OLA 2026 Conference Submission**

---

## 1. Overview

This document describes all visualizations generated for the fuzzy-controlled PSO research. Each figure is publication-ready at 300 DPI in PNG format, suitable for conference proceedings and presentations.

**Total Figures:** 40+ visualizations across 3 categories:
1. **Fuzzy System Visualizations** (8 figures)
2. **Performance Comparison** (8 figures)
3. **Statistical Analysis** (20+ figures)

---

## 2. Fuzzy System Visualizations

### 2.1 Figure 1: Diversity Input Membership Functions

**File:** `FUZZY/plots/01_fuzzy_input_diversity_3labels.png`

**Description:**
Shows the three membership functions for the first fuzzy input (population diversity ratio $d_{\text{ratio}}$).

**Technical Details:**
- X-axis: Diversity Ratio [0, 1]
- Y-axis: Degree of Membership [0, 1]
- Three triangular membership functions:
  - **Low:** Peak at 0.2
  - **Medium:** Peak at 0.5
  - **High:** Peak at 0.8
- Color-coded: Blue (low), Orange (medium), Green (high)

**Interpretation for Readers:**
- At $d_{\text{ratio}} = 0.3$: Population is 80% "Low diversity" and 20% "Medium diversity"
- At $d_{\text{ratio}} = 0.7$: Population is 60% "High diversity" and 40% "Medium diversity"
- Overlapping regions allow smooth transitions between fuzzy states

**Publication Use:**
Include in methodology section to explain diversity measurement and fuzzification.

---

### 2.2 Figure 2: Iteration Progress Input Membership Functions

**File:** `FUZZY/plots/02_fuzzy_input_progress_3labels.png`

**Description:**
Shows the three membership functions for the second fuzzy input (iteration progress $t_{\text{progress}}$).

**Technical Details:**
- X-axis: Iteration Progress [0, 1]
  - 0 = First iteration
  - 1 = Final iteration (1000)
- Y-axis: Degree of Membership [0, 1]
- Three triangular membership functions:
  - **Early:** Peak at 0.2 (iterations 0-200)
  - **Mid:** Peak at 0.5 (iterations 400-600)
  - **Late:** Peak at 0.8 (iterations 800-1000)
- Same color scheme as Figure 1

**Interpretation for Readers:**
- Temporal progression from exploration (early) to exploitation (late)
- Overlaps enable gradual transition (e.g., at iteration 300: "Early" = 60%, "Mid" = 40%)

**Publication Use:**
Pair with Figure 1 to show both FIS inputs before output.

---

### 2.3 Figures 3a-3d: Output Inertia Weight per Fuzzy Set

**Files:**
- `FUZZY/plots/03_fuzzy_output_w_set_A_3labels.png` (Conservative)
- `FUZZY/plots/03_fuzzy_output_w_set_B_3labels.png` (Balanced)
- `FUZZY/plots/03_fuzzy_output_w_set_C_3labels.png` (Exploratory)
- `FUZZY/plots/03_fuzzy_output_w_set_D_3labels.png` (Aggressive)

**Description:**
Four 2×2 subplots comparing membership functions for output inertia weight ($w$) under different scenarios.

**Subplots per Set:**

**Top-Left: Membership Functions**
- X-axis: Inertia Weight [0.1, 0.9]
- Y-axis: Membership [0, 1]
- Three curves: Low, Medium, High
- Different peak heights and positions per set

**Top-Right: 3D Surface**
- Diversity (X-axis) × Iteration Progress (Y-axis) → $w$ output (Z-axis)
- Color gradient: Blue (low $w$) → Red (high $w$)
- Shows how $w$ adapts across both inputs simultaneously

**Bottom-Left: Contour Heatmap**
- 2D projection of 3D surface
- Contour lines at $w$ = 0.2, 0.4, 0.6, 0.8
- Color intensity indicates $w$ magnitude

**Bottom-Right: Adaptation Strategy Text**
- Summary of set characteristics
- Key operating regions highlighted

**Set-Specific Observations:**

**Set A (Conservative):**
- Peak output at middle diversity and all progress stages
- Lower $w$ in late iterations (exploitation-focused)
- Suitable for: Smooth problems with clear optima

**Set B (Balanced):**
- Symmetric, evenly distributed membership functions
- Gradual $w$ decrease with iteration progress
- Higher $w$ when diversity is low (exploration trigger)
- Suitable for: General-purpose optimization

**Set C (Exploratory):**
- Elevated $w$ values across all scenarios
- Maintains exploration even in late iterations
- Peaks at high diversity + late stage
- Suitable for: Highly multimodal, deceptive problems

**Set D (Aggressive):**
- High $w$ in early iterations (strong exploration)
- Rapid drop in late iterations (rapid exploitation)
- Steep membership function transitions
- Suitable for: Quick convergence, deceptive problems

**Publication Use:**
Include one representative set (B) in main paper, relegate A-D comparison to supplementary materials.

---

### 2.4 Figure 4: Fuzzy Rules Heatmap

**File:** `FUZZY/plots/04_fuzzy_rules_heatmap_3labels.png`

**Description:**
Visualizes the 3×3 Mamdani rule matrix mapping (Diversity, Progress) → $w$ output.

**Layout:**
- Rows: Diversity [Low, Medium, High]
- Columns: Progress [Early, Mid, Late]
- Cells: Color-coded output ($w$ membership: Low/Medium/High)

**Rule Interpretation:**
```
┌─────────┬───────┬──────┬──────┐
│ Div\Prog│ Early │  Mid │ Late │
├─────────┼───────┼──────┼──────┤
│  Low    │ High  │ High │ High │  (need exploration)
│ Medium  │ High  │ Med  │ Med  │  (balanced)
│  High   │ Med   │ Med  │ Low  │  (transition to exploitation)
└─────────┴───────┴──────┴──────┘
```

**Color Coding:**
- Blue: $w$ = Low (0.1-0.4, exploitation)
- Orange: $w$ = Medium (0.4-0.6, balanced)
- Green: $w$ = High (0.6-0.9, exploration)

**Key Insights:**
- Diagonal: Low diversity + Late progress → Low $w$ (exploit)
- Anti-diagonal: High diversity + Early progress → High $w$ (explore)
- Center: Medium settings → Medium $w$ (balanced)

**Publication Use:**
Include in methodology section. Clearly label rule matrix for reader understanding.

---

### 2.5 Figure 5: All Fuzzy Sets Comparison

**File:** `FUZZY/plots/05_fuzzy_w_sets_comparison_3labels.png`

**Description:**
Side-by-side comparison of membership functions for Sets A, B, C, D (1×4 layout with 2 sets in current implementation).

**Layout:**
- Four subplots for four fuzzy sets (A, B, C, D)
- Each subplot shows: Low, Medium, High membership functions
- X-axis: Inertia Weight [0.1, 0.9]
- Y-axis: Membership [0, 1]
- Color-consistent with individual set figures

**Differences Highlighted:**
- **A:** Conservative, narrow peaks
- **B:** Balanced, symmetric overlaps
- **C:** Exploratory, wider spreads
- **D:** Aggressive, asymmetric distribution

**Publication Use:**
Excellent for showing design diversity. Use as key figure in results section comparing set performance.

---

### 2.6 Figure 6: Comparison of Membership Functions (3 vs 5 Labels)

**File:** `FUZZY/plots/06_comparison_membership_functions.png`

**Description:**
Comprehensive 4-row × 2-column layout comparing 3-label vs 5-label fuzzy systems for all sets.

**Structure:**
- **Row 0:** 3-label membership functions (Low, Medium, High)
  - Four columns for Sets A, B, C, D
- **Row 1:** Legend for 3-label terms
- **Row 2:** 5-label membership functions (Very Low, Low, Medium, High, Very High)
  - Four columns for Sets A, B, C, D
- **Row 3:** Legend for 5-label terms

**Observations:**
- 3-label: Simpler, coarser control granularity
- 5-label: Finer control, more linguistic precision
- Current implementation: 3-label (simpler, sufficient for PSO)

**Publication Use:**
Include in appendix showing design alternatives and rationale for 3-label choice.

---

### 2.7 Figures 7a-c: Comparison at Critical Operating Points

**Files:**
- `FUZZY/plots/07_comparison_critical_points.png` (3×3 subplots)

**Description:**
Shows inertia weight values output by each fuzzy set at three representative scenarios:

1. **Low Diversity, Early Stage**
   - Interpretation: Population starting to converge
   - Expected: High $w$ (maintain exploration)

2. **Medium Diversity, Mid-Iteration**
   - Interpretation: Balanced population state
   - Expected: Medium $w$ (balanced exploration/exploitation)

3. **High Diversity, Late Stage**
   - Interpretation: Population still dispersed near end
   - Expected: Low $w$ (encourage convergence)

**Bar Chart Format:**
- X-axis: Fuzzy Sets (A, B, C, D)
- Y-axis: Output $w$ value [0.1, 0.9]
- Two bars per scenario: 3-label (blue), 5-label (orange)

**Comparative Insights:**
- **Set A:** Conservative across all scenarios
- **Set B:** Linear progression with scenario type
- **Set C:** Consistently elevated $w$ values
- **Set D:** Aggressive gradient from low to high diversity

**Publication Use:**
Good for concrete examples. Helps readers understand set behavior quantitatively.

---

### 2.8 Figures 8a-d: 3D Surface Comparison (per Set)

**Files:**
- `FUZZY/plots/08_3d_surface_comparison_set_A.png`
- `FUZZY/plots/08_3d_surface_comparison_set_B.png`
- `FUZZY/plots/08_3d_surface_comparison_set_C.png`
- `FUZZY/plots/08_3d_surface_comparison_set_D.png`

**Description:**
Three-subplot layout showing 3D response surface for each fuzzy set:

**Subplot 1: 3D Surface (3-label)**
- X-axis: Diversity Ratio [0, 1]
- Y-axis: Iteration Progress [0, 1]
- Z-axis: Output $w$ [0.1, 0.9]
- Color gradient: Viridis (blue=low, yellow=high)
- Shows how $w$ responds to both inputs

**Subplot 2: 3D Surface (5-label)**
- Same axes, different fuzzy system
- Typically smoother, more gradual transitions

**Subplot 3: Difference Contour**
- X-axis: Diversity Ratio
- Y-axis: Iteration Progress
- Color: $\Delta w$ = 5-label minus 3-label
- Red: 5-label produces higher $w$
- Blue: 3-label produces higher $w$

**Interpretation Guidelines:**
- Steep gradients: Sensitive to input changes
- Flat regions: Robust to parameter variations
- Ridge patterns: Indicate decision boundaries

**Publication Use:**
Include in appendix for detailed technical documentation. Useful for AI/computational intelligence venues.

---

## 3. Performance Comparison Figures

### 3.1 Figures 9a-d: Algorithm Comparison per Function (F1, F21, F22, F23)

**Files:**
- `analysis_modules_cec/level2_aggregated_cec/comparison_F1.png`
- `analysis_modules_cec/level2_aggregated_cec/comparison_F21.png`
- `analysis_modules_cec/level2_aggregated_cec/comparison_F22.png`
- `analysis_modules_cec/level2_aggregated_cec/comparison_F23.png`

**Layout:** 2×2 subplots per figure

**Subplot 1: Best Fitness Achieved (Horizontal Bar Chart)**
- X-axis: Algorithms (PSO, PSO_FCS:A, PSO_FCS:B, PSO_FCS:C, PSO_FCS:D)
- Y-axis: Best Fitness Value
- Bar colors: Distinct for each algorithm
- Value labels: Centered inside bars for clarity
- Sorted by performance (best rightmost)

**Interpretation:**
- Shorter bar = better performance (closer to optimum)
- Relative bar lengths show performance gaps
- Example F1: PSO_FCS:B ≈ 0.0015, PSO ≈ 0.0018

**Subplot 2: Gap Distribution (Boxplot)**
- X-axis: Algorithms (same 5)
- Y-axis: Gap to Optimum (%) [0, 50%]
- Boxplot elements:
  - Box: IQR (25th-75th percentile)
  - Orange line: Median
  - **Black X marker: Mean** (distinguishes median vs mean)
  - Whiskers: ±1.5×IQR
  - Outliers: Individual points beyond whiskers
- Shows variability across 31 independent runs

**Interpretation:**
- Narrow boxes: Consistent algorithm behavior
- Low median: Reliable convergence
- Large spread: Occasionally fails
- Example F1: PSO median ~0.1%, PSO_FCS:B median ~0.02%

**Subplot 3: Mean ± Standard Deviation (Error Bar Plot)**
- X-axis: Algorithms
- Y-axis: Gap (%)
- Points: Mean gap
- Vertical bars: ±1 std deviation
- Shows confidence in mean estimate

**Interpretation:**
- Tall error bars: High variability
- Short bars: Consistent behavior
- Overlapping bars: No significant difference

**Subplot 4: Computational Efficiency (Scatter Plot)**
- X-axis: Mean Execution Time (seconds)
- Y-axis: Mean Gap (%)
- Bubble size: Algorithms
- Pareto frontier shown (if applicable)
- Annotated with algorithm names

**Interpretation:**
- Lower-left quadrant: Fast and accurate (ideal)
- Labels identify which algorithm is which
- Tradeoff visualization (speed vs accuracy)

**Publication Use:**
Primary results figures. Include F1 (unimodal), F21-F23 (composition) in main paper. Add F4, F10, F20 to supplementary for multimodal/hybrid coverage.

---

### 3.2 Figures 10a-d: Gap Distribution per Function

**Files:**
- `analysis_modules_cec/level2_aggregated_cec/gap_distribution_F1.png`
- `analysis_modules_cec/level2_aggregated_cec/gap_distribution_F21.png`
- `analysis_modules_cec/level2_aggregated_cec/gap_distribution_F22.png`
- `analysis_modules_cec/level2_aggregated_cec/gap_distribution_F23.png`

**Description:**
Full-page boxplot comparison of all 5 algorithms for each function.

**Layout:** Single 1×1 subplot spanning full figure

**Elements:**
- X-axis: 5 algorithms (PSO, PSO_FCS:A-D)
- Y-axis: Gap to Optimum (%)
- Boxplots with:
  - Orange line: Median (50th percentile)
  - **Black X marker: Mean** (14pt, bold)
  - Box: 25th-75th percentile (IQR)
  - Whiskers: Min/max within 1.5×IQR
  - Circles: Outliers beyond whiskers
- Title: "Gap Distribution: [Function Name]"
- Color-coded by algorithm for clarity

**Extended Layout:**
- Subtitle: "Distribution across 31 independent runs"
- Legend: Shows algorithm color scheme
- Grid: Horizontal lines at 10%, 20%, 30% gaps for reference

**Interpretation Guide:**
- **F1 (Unimodal):** All boxes clustered near 0%, PSO_FCS:B lowest
- **F21-F23 (Composition):** Higher gaps (20-40%), PSO_FCS:C best
- **Spread patterns:** Indicate consistency vs outlier behavior

**Publication Use:**
Use one representative function (F1) in main paper, include full set in appendix.

---

### 3.3 Figure 11: Convergence Curves

**File:** `analysis_modules_cec/convergence_analysis_cec/convergence_curves_set_B.png`

**Description:**
Multi-panel figure showing convergence curves (fitness vs iteration) for representative problems.

**Layout:** 2×2 subplots
- **Top-left:** F1 (unimodal, easy)
- **Top-right:** F10 (Rosenbrock, medium)
- **Bottom-left:** F20 (hybrid, hard)
- **Bottom-right:** F23 (composition, very hard)

**Each Subplot:**
- X-axis: Iteration [0, 1000]
- Y-axis: Log Scale of (Fitness - Optimum) to show convergence detail
- Five curves: PSO, PSO_FCS:A, PSO_FCS:B, PSO_FCS:C, PSO_FCS:D
- Color-coded (PSO = gray, sets = blue/orange/green/red)
- Median curve from 31 runs
- Shaded regions: ±1 std deviation (optional for clarity)

**Interpretation:**
- Steep curves: Fast convergence
- Plateaus: Stagnation regions
- F1: All curves plateau near log(0) = optimal
- F23: Curves plateau at log(gap) ≈ 1-2 (20-100% gap)

**Publication Use:**
Standard convergence figure. Include in results section alongside gap statistics.

---

## 4. Statistical Analysis Figures

### 4.1 Figure 12: Performance Ranking across All Functions

**File:** `analysis_modules_cec/level3_disaggregated/ranking_all_functions.png`

**Description:**
Heatmap showing algorithm performance ranking (1st-5th place) across all 23 functions.

**Layout:**
- Rows: 23 functions (F1-F23)
- Columns: 5 algorithms (PSO, PSO_FCS:A-D)
- Cell color: Rank (1=dark green, 5=dark red)
- Cell text: Rank number and gap percentage

**Color Scheme:**
- Green: 1st place (best algorithm)
- Yellow: 2nd-3rd place
- Orange: 4th place
- Red: 5th place (worst algorithm)

**Key Observations:**
- PSO_FCS:B column: Mostly green (dominates)
- PSO column: Mix of yellow/red (inconsistent)
- Diagonal patterns: Some algorithms specialized to certain function types

**Publication Use:**
Excellent summary visualization. Shows broad superiority of PSO_FCS:B without detailed numbers.

---

### 4.2 Figure 13: Algorithm Win-Loss-Tie Matrix

**File:** `analysis_modules_cec/level3_disaggregated/comparison_matrix.png`

**Description:**
Win-loss matrix comparing each algorithm pair.

**Layout:**
- 5×5 matrix (5 algorithms)
- Diagonal: Always tie (algorithm vs itself)
- Upper triangle: Wins of row-algorithm vs column-algorithm
- Lower triangle: Losses (or vice versa)
- Each cell: Count + percentage

**Example Entry:**
```
PSO_FCS:B vs PSO:
  Wins: 19/23 (83%)
  Losses: 4/23 (17%)
  Interpretation: PSO_FCS:B beats PSO on 19 out of 23 functions
```

**Color Coding:**
- Green: High win percentage (algorithm superior)
- White: Balanced (tied)
- Red: Low win percentage (algorithm inferior)

**Publication Use:**
Provides quantitative comparison summary in compact format.

---

### 4.3 Figure 14: Effect Size (Cohen's d) Comparison

**File:** `analysis_modules_cec/statistical_analysis/cohens_d_all_pairs.png`

**Description:**
Effect size visualization showing practical significance of differences.

**Layout:**
- Bar chart: Cohen's $d$ for each algorithm pair
- X-axis: Algorithm pairs (PSO vs PSO_FCS:A/B/C/D)
- Y-axis: Cohen's $d$ [-0.5, 2.5]
- Color: Green if $d > 0.5$ (medium effect), Red if $d < 0.2$ (small effect)
- Horizontal line: $d = 0.5$ (medium effect threshold)

**Interpretation:**
- $d > 0.8$: Large effect (practical significance confirmed)
- $0.5 < d < 0.8$: Medium effect
- $0.2 < d < 0.5$: Small effect
- $d < 0.2$: Negligible effect

**Example:**
- PSO vs PSO_FCS:B: $d = 1.24$ (large effect) ← Include in paper!
- PSO_FCS:A vs PSO_FCS:C: $d = 0.34$ (small effect)

**Publication Use:**
Essential for showing not just statistical significance, but practical relevance.

---

## 5. Supplementary Figures (Appendix)

### 5.1 Figure 15: Diversity Evolution Curves

**File:** `analysis_modules_cec/diversity_analysis_cec/diversity_curves.png`

**Description:**
Population diversity ratio over iterations for representative functions.

**Layout:** 2×2 subplots (F1, F10, F20, F23)

**Each Subplot:**
- X-axis: Iteration [0, 1000]
- Y-axis: Diversity Ratio [0, 1]
- Five curves: PSO and PSO_FCS:A-D
- Shows how diversity decays during optimization

**Key Pattern:**
- PSO: Sharp drop (premature convergence risk)
- PSO_FCS:B: Gradual, controlled decay
- PSO_FCS:C: Maintains diversity longer

**Publication Use:**
Appendix figure explaining why PSO_FCS:B maintains better performance through controlled diversity.

---

### 5.2 Figure 16: Inertia Weight Trajectories

**File:** `analysis_modules_cec/w_evolution_analysis/w_trajectories.png`

**Description:**
Actual inertia weight ($w$) values output by fuzzy sets over iterations.

**Layout:** 4 subplots (one per fuzzy set A-D)

**Each Subplot:**
- X-axis: Iteration [0, 1000]
- Y-axis: $w$ value [0.1, 0.9]
- Multiple colored lines: Different runs/diversity scenarios
- Shows adaptation of $w$ in response to problem state

**Observations:**
- **Set A:** $w$ decreases monotonically (exploitation focus)
- **Set B:** Smooth decrease with slight plateaus
- **Set C:** $w$ elevated, slower decrease
- **Set D:** Sharp drop then stabilization

**Publication Use:**
Appendix figure showing concrete fuzzy controller behavior during optimization.

---

## 6. Table Formatting for Publication

While not "figures," tables are critical for paper clarity:

### Table Format 1: Algorithm Comparison Summary

```markdown
| Function | PSO    | Set A  | Set B  | Set C  | Set D  | Best  |
|----------|--------|--------|--------|--------|--------|-------|
| F1       | 0.18%  | 0.04%  | 0.02%▼ | 0.06%  | 0.09%  | B     |
| F2       | 1.24%  | 0.45%  | 0.31%▼ | 0.52%  | 0.78%  | B     |
| ...      | ...    | ...    | ...    | ...    | ...    | ...   |
| Avg      | 24.67% | 18.92% | 15.34%▼| 16.87% | 19.45% | **B** |
```

**Notation:**
- ▼: Best algorithm for function
- **Bold:** Overall best in category
- %: Percentage gap to optimum

### Table Format 2: Statistical Significance

```markdown
| Comparison | t-stat | p-value | Significant | Cohen's d | Interpretation |
|------------|--------|---------|-------------|-----------|----------------|
| PSO vs B   | 4.87   | <0.001  | ***Yes***   | 1.24      | Large effect   |
| A vs B     | 2.15   | 0.041   | *Yes*       | 0.42      | Small effect   |
| C vs D     | 0.98   | 0.332   | No          | 0.18      | Negligible     |
```

**Legend:**
- `***` = p < 0.001 (highly significant)
- `**` = p < 0.01 (very significant)
- `*` = p < 0.05 (significant)
- No mark = p ≥ 0.05 (not significant)

---

## 7. Figure Checklist for Conference Submission

**Technical Requirements:**
- [ ] All figures at 300 DPI PNG format
- [ ] Font sizes readable at 50% print reduction (8pt minimum)
- [ ] Color-blind friendly palette (avoid red-green only)
- [ ] Legends included for all multi-series plots
- [ ] Axis labels with units specified
- [ ] Captions descriptive but concise (<100 words)

**Content Requirements:**
- [ ] Each figure appears in main text or appendix
- [ ] All figures referenced in text by number
- [ ] Captions explain figure content
- [ ] Figure quality suitable for journal/conference standards

**Submission Checklist:**
- [ ] Main paper: Figures 1-2, 5, 9a, 10a, 11, 12 (max 6 figures)
- [ ] Supplementary: Figures 3-4, 8, 9b-d, 10b-d, 13-16
- [ ] All source data provided in supplementary materials
- [ ] High-resolution versions available upon request

---

## 8. Data Availability

**All visualizations can be regenerated using:**

```bash
# Generate fuzzy system figures
python FUZZY/generate_fuzzy_plots.py

# Generate performance comparison figures
python analysis_modules_cec/level2_aggregated_cec.py

# Generate detailed analysis figures
python analysis_modules_cec/run_paper_analysis.py
```

**Output Directory:**
- Fuzzy figures: `FUZZY/plots/`
- Performance figures: `Resultados/resumen/level2_aggregated_cec/`
- Analysis figures: `Resultados/resumen/level3_disaggregated/`

---

**Document Version:** 1.0  
**Date:** January 2026  
**Last Updated:** January 14, 2026

