# Set Comparison Analysis: W-Value Matrices (3-Label vs 5-Label)

## Overview

The **Set Comparison Analysis** (implemented in `FUZZY/compare_all_sets_w_values.py`) generates three 4×4 matrices of heatmaps that visualize **how inertia weight controllers diverge** across fuzzy sets A, B, C, and D in both 3-label and 5-label configurations.

**What it answers:**
- How different are Sets A, B, C, D from each other?
- Does adding 5 linguistic labels change behavior equally for all sets, or does it affect some sets more than others?
- Which regions of the (diversity, progress) input space show the largest controller divergence?

---

## Generated Visualizations

### 1. **3-Label Comparison Matrix** (`09_comparison_matrix_3labels.png`)

**Structure:** 4×4 grid showing all pairwise comparisons of 3-label controllers.

**Rows/Columns:** Sets A, B, C, D

**Cell Content:** Heatmap of Δw = w_SetRow(3L) - w_SetColumn(3L)

**What it shows:**
- **Diagonal (A vs A, B vs B, etc.):** Zero values (same set)
- **Off-diagonal cells:** Difference in inertia weight decisions between two sets
  - **Red zones:** Set_Row produces higher w (more exploratory)
  - **Blue zones:** Set_Column produces higher w

**Key insights:**
- **Large red/blue zones:** Sets are fundamentally different in behavior
- **Light/white zones:** Sets make similar decisions in that region
- **Pattern differences:** Some sets specialize in different input regions

**Typical patterns observed:**
- Set A (conservative) produces low w overall → off-diagonal likely blue when compared to B/C/D
- Set D (aggressive) produces high w overall → off-diagonal likely red when compared to A/B/C
- Sets B and C show intermediate patterns

---

### 2. **5-Label Comparison Matrix** (`09_comparison_matrix_5labels.png`)

**Structure:** Same as 3-Label but for 5-label controllers.

**Interpretation:** Identical to 3-Label, but shows how the additional linguistic terms (very_low, very_high) affect inter-set divergence.

**Purpose:**
- Compare controller differentiation with 5 labels vs 3 labels
- Does granularity help distinguish sets better?
- Are the same "specialist regions" preserved with 5 labels?

**Expected differences:**
- More fine-grained output values → potentially sharper transitions
- May reveal hidden structure in mid-range (low/medium/high) behaviors

---

### 3. **3-Label vs 5-Label Cross-Comparison Matrix** (`09_comparison_matrix_3vs5labels.png`)

**Structure:** 4×4 grid with mixed label versions.

**Rows:** Sets A, B, C, D using **3-label controller**

**Columns:** Sets A, B, C, D using **5-label controller**

**Cell Content:** Heatmap of Δw = w_SetColumn(5L) - w_SetRow(3L)

**Critical diagonal cells (A/3L vs A/5L, etc.):**
- Show the **direct impact of upgrading from 3 to 5 labels** for the **same fuzzy set**
- **Red zones:** 5-label produces higher w (more exploratory at that point)
- **Blue zones:** 5-label produces lower w (more exploitative)
- **White zones:** 5-label and 3-label agree

**Off-diagonal cells:**
- Show cross-set incompatibilities (e.g., A/3L vs B/5L)
- Less directly interpretable but useful for understanding full behavior space

---

## Interpretation Guide

### Reading a Single Heatmap Cell

**Cell (i, j) shows: Δw = Set_i - Set_j**

```
Red     → Set_i produces HIGHER w (more exploratory)
Blue    → Set_j produces HIGHER w (Set_i more exploitative)
White   → Sets produce similar w (Δw ≈ 0)
Intense color → Large divergence (>0.3-0.5)
Pale color    → Small divergence (<0.1)
```

**Axes meaning:**
- **X-axis (Diversity):** 0.01 (low diversity) → 0.99 (high diversity)
- **Y-axis (Progress):** 0.01 (early iterations) → 0.99 (late iterations)

**Critical corners:**
- **Bottom-left (Low div, Early progress):** Exploration phase → expect high w
- **Top-right (High div, Late progress):** Exploitation phase → expect low w
- **Off-diagonal corners:** Mismatch between diversity and progress signal

---

## Key Research Questions

### Q1: Are the sets truly distinct?
**Answer location:** 3-Label Comparison Matrix, off-diagonal cells

- If mostly white → sets are redundant, pick one
- If colorful → sets specialize in different regions, all valuable

### Q2: Does 5-label granularity improve controller differentiation?
**Answer location:** Compare 3-Label matrix vs 5-Label matrix side-by-side

- If 5-label shows same patterns (scaled) → 5 labels confirm 3-label behavior
- If 5-label shows new red/blue zones → 5 labels reveal hidden structure
- If patterns shift substantially → 5 labels changes controller strategy

### Q3: How much does upgrading to 5-labels affect each set individually?
**Answer location:** Diagonal of 3-Label vs 5-Label matrix (A vs A, B vs B, etc.)

- **Set A diagonal:** Small Δw → 5-labels doesn't affect conservative set much
- **Set D diagonal:** Large Δw → 5-labels strongly modifies aggressive set
- Variance across diagonals → 5-label impact is non-uniform

### Q4: Which regions are most sensitive to label count?
**Answer location:** 3-Label vs 5-Label diagonal, identify strongest red/blue zones

**Typical findings:**
- Early-stage exploration (bottom-left) → often large Δw
- Balanced phases (center) → often smaller Δw
- Late-stage exploitation (top-right) → varies by set

---

## Performance Implications

### For Algorithm Design
- **If sets are very different:** Use set selection logic based on problem properties
- **If sets are similar:** Single best-performer set may suffice
- **If 5-label Δw is large:** Include it for important problem types

### For Benchmark Selection
- **Sets that diverge most in (low-div, early-prog):** Good for exploration-heavy problems
- **Sets that diverge most in (high-div, late-prog):** Good for fine-tuning problems
- **Uniform divergence:** Good for general-purpose optimization

### For Parameter Tuning
- **Large diagonal Δw in Set X:** Consider tuning w_range separately for 3L vs 5L
- **Small diagonal Δw:** 3-label version sufficient (saves computation)
- **Off-diagonal patterns:** Inform fuzzy rule design

---

## Integration with Experimental Pipeline

These matrices **inform configuration choices** in `util/json/experiments_config.json`:

```json
{
  "mhs": ["PSO", "PSO_FCS"],
  "mh_params": {
    "PSO_FCS": [
      {"w_set": "A", "num_labels": 3},
      {"w_set": "A", "num_labels": 5},
      {"w_set": "B", "num_labels": 3},
      {"w_set": "B", "num_labels": 5},
      ... (8 total configurations)
    ]
  }
}
```

**Decision rules based on set comparison:**
1. **Do off-diagonal cells show specialization?**
   - YES → Include all 4 sets (A, B, C, D)
   - NO → Drop redundant sets

2. **Do diagonal cells show significant Δw?**
   - YES → Run both 3-label and 5-label experiments
   - NO → Use only 3-label (faster, sufficient)

3. **Which regions show largest Δw in diagonals?**
   - Exploitation zones → prioritize CEC benchmarks with diverse-to-converged transitions
   - Exploration zones → prioritize complex multi-modal problems

---

## Visualization Technical Details

### Heatmap Color Scheme
- **Colormap:** `RdBu_r` (Red-Blue reversed)
  - Red = Positive Δw (first argument larger)
  - Blue = Negative Δw (second argument larger)
  - White = Zero Δw (equal)

### Value Range
- **vmin, vmax = -0.5 to 0.5**
- Constrains color scale to visible differences
- Values outside range saturate to extreme colors

### Grid Resolution
- **50×50 points** per heatmap
- Covers full (0.01, 0.99) input space
- Sufficient for visual pattern detection while keeping computation reasonable

### Figure Layout
- **Figure size:** 16×14 inches (publication quality)
- **Grid:** 4×4 subplots (16 heatmaps)
- **DPI:** 300 (high-resolution)
- **Colorbar:** Single shared colorbar showing Δw scale

---

## Common Patterns & Interpretations

### Pattern 1: Diagonal Blues (Off-diagonal consistently blue in row i)
**Interpretation:** Set i is **universally more exploitative** than others
- Likely Set A (conservative)
- Suitable for: Problems requiring careful convergence
- Risk: May miss global optima in highly multimodal spaces

### Pattern 2: Diagonal Reds (Off-diagonal consistently red in row i)
**Interpretation:** Set i is **universally more exploratory** than others
- Likely Set D (aggressive)
- Suitable for: Complex landscapes, early-stage search
- Risk: May waste evaluations on redundant exploration

### Pattern 3: Checkerboard pattern (Mixed red/blue across matrix)
**Interpretation:** Sets show **complementary specialization**
- Different regions favor different sets
- Suitable for: Hybrid algorithms using set selection
- Benefit: Ensemble potential

### Pattern 4: Weak colors (Pale throughout)
**Interpretation:** All controllers make **similar decisions**
- Possible redundancy
- Check if 3-label is sufficient (save computation)
- Consider if problem diversity in benchmark is high enough

### Pattern 5: Sharp red/blue zones in diagonal (3L vs 5L)
**Interpretation:** 5-label **substantially alters behavior** for that set
- Region where extra granularity matters most
- May correlate with algorithm performance gains
- Consider benchmarking specifically in that input region

---

## Next Steps

1. **Generate matrices** for your current fuzzy controllers:
   ```bash
   python FUZZY/compare_all_sets_w_values.py
   ```

2. **Visual inspection:** Open the three PNG files and identify:
   - Dominant colors per set (red vs blue dominance)
   - Spatial patterns (diagonal blocks, stripes, checkerboard)
   - Intensity variations (pale vs saturated regions)

3. **Quantitative analysis:** Compute statistics from heatmaps:
   - Mean |Δw| per set pair → which diverges most?
   - Std dev of Δw per region → where is variation concentrated?
   - Correlation of patterns between 3L and 5L matrices → consistency

4. **Integration decision:**
   - If |Δw| > 0.3 for any diagonal → keep both 3-label and 5-label
   - If max off-diagonal |Δw| < 0.15 → consider dropping redundant sets
   - If corners show specialized patterns → design problem-specific set selection logic

5. **Performance validation:**
   - Run PSO_FCS with all 8 configurations on benchmark suite
   - Compare convergence curves for A/3L vs A/5L (to validate diagonal findings)
   - Test on problems with different diversity profiles (high → convergent, low → multimodal)

---

## References

- **Fuzzy Logic Fundamentals:** See `03_fuzzy_controller_w.py` docstring
- **3-Label Controller:** `FUZZY/fuzzy_controller_w.py`
- **5-Label Controller:** `FUZZY/fuzzy_controller_w_5labels.py`
- **Base Surface Plots:** `FUZZY/plots/08_3d_surface_comparison_set_*.png`
- **All W-value Plots:** `FUZZY/plots/03_fuzzy_output_w_set_*.png`

---

**Last updated:** January 6, 2026  
**Author:** Fuzzy PSO Research System  
**Related files:** `FUZZY/compare_all_sets_w_values.py`, `FUZZY/fuzzy_plots.py`
