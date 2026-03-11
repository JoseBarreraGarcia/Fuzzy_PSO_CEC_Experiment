# Next Steps Guide

## 🎯 Immediate Actions (Today)

### 1. Test the System
```bash
cd "c:\Users\josec\Experimentos_Fuzzy_Python\(solver_bioinspirados)"
.\env\Scripts\python.exe test_integration.py
```
**Expected Output**: All 3 tests passing ✓

### 2. Generate Plots
```bash
.\env\Scripts\python.exe generate_fuzzy_plots.py
```
**Expected Output**: 8 PNG files in FUZZY/plots/

### 3. View Results
Open `FUZZY/plots/` folder:
- 01_fuzzy_input_diversity.png
- 02_fuzzy_input_progress.png
- 03_fuzzy_output_w_set_A.png through D
- 04_fuzzy_rules_heatmap.png
- 05_fuzzy_w_sets_comparison.png

---

## 📋 For Your Next Paper/Presentation

### If Writing Academic Paper
1. Open `FUZZY/plots/04_fuzzy_rules_heatmap.png`
2. Copy to manuscript folder
3. Insert with caption:
   ```latex
   \includegraphics[width=0.7\textwidth]{figures/fuzzy_rules_heatmap.png}
   ```

### If Preparing Conference Talk
1. Copy `05_fuzzy_w_sets_comparison.png` to presentation
2. Add slide title: "Fuzzy Inertia Weight Control"
3. Explain: How PSO adapts weight based on diversity and progress

### If Documenting System
1. Create README with embedded images:
   ```markdown
   ## Fuzzy Control Strategy
   ![Diversity Input](FUZZY/plots/01_fuzzy_input_diversity.png)
   ![Rules](FUZZY/plots/04_fuzzy_rules_heatmap.png)
   ```

---

## 🔬 To Run Experiments with New Fuzzy Sets

### Step 1: Define New Set
Edit `FUZZY/fuzzy_controller_w.py`, find `W_SETS` dictionary (around line 30):
```python
W_SETS = {
    'A': {...},
    'B': {...},
    'C': {...},
    'D': {...},
    'E': {  # ← ADD NEW SET
        'low': (a1, b1, c1),
        'medium': (a2, b2, c2),
        'high': (a3, b3, c3),
    }
}
```

### Step 2: Add to Config
Edit `util/json/experiments_config.json`:
```json
{
  "mh_params": [
    {"w_set": "A", "label": "PSO_FCS:A"},
    {"w_set": "E", "label": "PSO_FCS:E"}  # ← NEW
  ]
}
```

### Step 3: Run Pipeline
```bash
python reiniciarDB.py        # Reset database
python poblarDB.py            # Load new experiments
python main.py                # Run PSO variants
python analisis.py            # Analyze results + generate fuzzy plots
```

### Result
- New plot: `FUZZY/plots/03_fuzzy_output_w_set_E.png`
- Experiments with fuzzy set E saved in database
- Analysis results in `Resultados/resumen/`

---

## 🛠️ For Developers

### Understand the Architecture
```
PSO Solver
    ↓
Fuzzy Controller (FUZZY/fuzzy_controller_w.py)
    ├── Input: diversity_ratio [0,1]
    ├── Input: iteration_progress [0,1]
    └── Output: inertia weight w [wMin, wMax]
    ↓
Plots Generated (FUZZY/fuzzy_plots.py)
    ├── Show membership functions
    ├── Show rule base
    └── Show output for each w_set
```

### Key Files to Know
- **Logic**: `FUZZY/fuzzy_controller_w.py` (Mamdani FIS implementation)
- **Visuals**: `FUZZY/fuzzy_plots.py` (matplotlib-based plots)
- **Orchestration**: `analisis.py` (calls run_fuzzy_plots())
- **Config**: `util/json/experiments_config.json` (experiment definitions)

### To Modify Colors/Fonts
Edit `FUZZY/fuzzy_plots.py`:
- Line ~60: `colors = {...}` ← Change colors
- Line ~32: `mpl.rcParams[...]` ← Change font/size
- Line ~75: `dpi=300` ← Change resolution

---

## 📚 Documentation to Read

### Quick (5 minutes)
1. This file (NEXT_STEPS.md)
2. `FUZZY_PLOTS_QUICKREF.txt`

### Medium (20 minutes)
3. `FUZZY/PLOTS_README.md`
4. `PROJECT_COMPLETION_REPORT.md`

### Complete (45 minutes)
5. `.github/copilot-instructions.md` (full system architecture)
6. `FUZZY_INTEGRATION_SUMMARY.md` (technical implementation)

---

## 🐛 If Something Breaks

### Fuzzy Plots Not Generating
```bash
python test_integration.py
# Check output for specific failures
```

### "charmap" Errors
```bash
pip install --upgrade matplotlib
# Already fixed in v2.1, but ensure latest version
```

### Missing Plots After Running analisis.py
1. Check `FUZZY/plots/` exists
2. Check write permissions on FUZZY folder
3. Run: `python generate_fuzzy_plots.py` (standalone)
4. Check console output for errors

### Plots Look Bad/Wrong
1. Open `FUZZY/fuzzy_plots.py`
2. Verify membership functions in plot functions
3. Check `fuzzy_controller_w.py` for actual membership definitions
4. Regenerate: `python generate_fuzzy_plots.py`

---

## 💡 Pro Tips

### Save Plots for Backup
```bash
cp FUZZY/plots/*.png "backup_location/"
# Or use Windows Explorer to copy FUZZY/plots/ folder
```

### Convert PNG to PDF (for LaTeX)
```bash
# Install: pip install pdf
# Then use ImageMagick or online converter
convert 04_fuzzy_rules_heatmap.png 04_fuzzy_rules_heatmap.pdf
```

### Embed in Powerpoint
1. Insert → Pictures → Select PNG from FUZZY/plots/
2. Right-click → Compress Pictures → Select "High Fidelity" option
3. Resizes while maintaining 300 DPI quality

### Version Control
```bash
# Ignore large PNG files in git
echo "FUZZY/plots/*.png" >> .gitignore
# But keep the code (fuzzy_plots.py, etc.)
git add FUZZY/*.py
git add .github/copilot-instructions.md
```

---

## 📞 Quick Reference Commands

```bash
# Generate fuzzy plots
python generate_fuzzy_plots.py

# Full analysis (3 levels + fuzzy plots)
python analisis.py

# Validate installation
python test_integration.py

# Reset everything (careful!)
python reiniciarDB.py

# Check plot files
dir FUZZY\plots\              # Windows
ls FUZZY/plots/               # Linux/Mac

# View plot info
ls -lh FUZZY/plots/*.png      # Size of each plot
file FUZZY/plots/*.png        # File format verification
```

---

## ✅ Verification Checklist

Before considering this complete, verify:

- [ ] `test_integration.py` passes all 3 tests
- [ ] 8 PNG files exist in `FUZZY/plots/`
- [ ] Each PNG is 200+ KB (quality check)
- [ ] `python analisis.py` executes without errors
- [ ] Fuzzy plots section appears in analisis.py output
- [ ] Documentation files readable (PLOTS_README.md, etc.)
- [ ] Can open PNG files (check aspect ratio, labels visible)
- [ ] `copilot-instructions.md` updated with new section

---

## 🎉 Success Indicators

You'll know everything is working when:

1. ✅ Run `python analisis.py`
2. ✅ See "Fuzzy set visualizations" in output summary
3. ✅ 8 PNG files in `FUZZY/plots/` folder
4. ✅ Each PNG opens and shows clear, labeled plots
5. ✅ Can copy plots to Word/PowerPoint/LaTeX without issues
6. ✅ Plots look professional (300 DPI, clear fonts)

---

## 📋 Execution Plan (This Week)

| Day | Action | Expected Outcome |
|-----|--------|------------------|
| Today | Run `test_integration.py` | All tests pass ✓ |
| Today | Generate plots | 8 PNG files created |
| Today | Review documentation | Understand system |
| This week | Use in paper/presentation | Plots visible in document |
| This week | Test with new fuzzy set | E.g., PSO_FCS:E working |
| Next week | Integrate into publication | Submit paper with fuzzy figures |

---

## 🚀 You're Ready To

✅ Generate publication-quality fuzzy visualizations
✅ Include them in academic papers
✅ Present to conferences
✅ Document your fuzzy control system
✅ Extend with new fuzzy sets
✅ Customize colors and styles

---

**Final Status**: ✅ **System Ready to Use**

All components integrated, tested, and documented. Ready for your next paper, presentation, or system documentation.

**Contact Support**: 
- Review error messages with `python test_integration.py`
- Check `FUZZY/PLOTS_README.md` for troubleshooting
- Read `.github/copilot-instructions.md` for architecture questions

---

**Document Version**: 1.0 (Feb 2025)
**For**: Scalable Fuzzy PSO Parameter System v2.1
