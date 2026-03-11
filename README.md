# Scalable Fuzzy PSO Parameter System

**Status**: ✅ PRODUCTION READY

## 📖 Documentation

All documentation is in the `documentation/` folder with numbered files showing reading order:

1. **[documentation/1_Index.md](documentation/1_Index.md)** ← Start here
2. **[documentation/2_Readme_fuzzy_system.md](documentation/2_Readme_fuzzy_system.md)** - Quick start (5 min)
3. **[documentation/3_Implementation_status.md](documentation/3_Implementation_status.md)** - Technical details (15 min)
4. **[documentation/4_Fuzzy_sets_deep_dive.md](documentation/4_Fuzzy_sets_deep_dive.md)** - Deep dive (20 min)
5. **[documentation/5_Final_report.txt](documentation/5_Final_report.txt)** - Complete reference (40 min)
6. **[documentation/6_System_documentation.py](documentation/6_System_documentation.py)** - Run with `python` to see ASCII diagrams

## 🛠️ Quick Commands

```bash
# View analysis results
python compare_fuzzy_sets.py
python detailed_w_analysis.py

# Full pipeline
python reiniciarDB.py && python poblarDB.py && python main.py && python analisis.py
```

## 📊 What You Have

- ✅ PSO_FCS:A and PSO_FCS:B working and tested
- ✅ w, diversity, progress tracked per iteration
- ✅ Comparison plots and statistics
- ✅ Ready to add C, D, E... fuzzy sets

## ➕ Add New Fuzzy Set

1. Edit `util/json/experiments_config.json` (add 1 line)
2. Run pipeline: `python reiniciarDB.py && python poblarDB.py && python main.py`

That's it! Zero code changes needed.

---

**→ Start with [documentation/1_Index.md](documentation/1_Index.md)**
