"""Generate OLA2026 presentation PPTX (English) from manuscript_OLA2026.tex.

15 slides, English text, numbered references [n] with per-slide footer citations,
and speaker notes (script) per slide.
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

ROOT = Path(__file__).resolve().parent
PLOTS = ROOT.parent / "plots"
OUT = ROOT / "OLA2026_generated.pptx"

NAVY = RGBColor(0x0B, 0x2E, 0x4F)
ACCENT = RGBColor(0xC0, 0x39, 0x2B)
GRAY = RGBColor(0x55, 0x55, 0x55)
LIGHT = RGBColor(0x88, 0x88, 0x88)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HIGHLIGHT = RGBColor(0xFD, 0xE7, 0xC8)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_title(slide, text, top=0.3, size=30, color=NAVY):
    tx = slide.shapes.add_textbox(Inches(0.5), Inches(top), Inches(12.3), Inches(0.9))
    tf = tx.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = color


def add_subtitle(slide, text, top=1.05, size=16):
    tx = slide.shapes.add_textbox(Inches(0.5), Inches(top), Inches(12.3), Inches(0.5))
    p = tx.text_frame.paragraphs[0]
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.italic = True; r.font.color.rgb = GRAY


def add_bullets(slide, items, left=0.7, top=1.7, width=12.0, height=5.0, size=20):
    tx = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = tx.text_frame; tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        if isinstance(item, tuple):
            level, text = item
        else:
            level, text = 0, item
        p.level = level
        r = p.add_run(); r.text = text
        r.font.size = Pt(size if level == 0 else size - 3)
        r.font.color.rgb = NAVY if level == 0 else GRAY
        p.space_after = Pt(8)


def add_image(slide, name, left, top, width=None, height=None, fallback_text=None):
    p = PLOTS / name
    if p.exists():
        kw = {}
        if width: kw["width"] = Inches(width)
        if height: kw["height"] = Inches(height)
        slide.shapes.add_picture(str(p), Inches(left), Inches(top), **kw)
        return True
    if fallback_text:
        tx = slide.shapes.add_textbox(Inches(left), Inches(top),
                                       Inches(width or 5), Inches(height or 3))
        r = tx.text_frame.paragraphs[0].add_run()
        r.text = f"[Figure: {fallback_text}]"
        r.font.size = Pt(14); r.font.italic = True; r.font.color.rgb = GRAY
    return False


def add_footer(slide, refs_text=None):
    if refs_text:
        tx = slide.shapes.add_textbox(Inches(0.3), Inches(7.1), Inches(9.5), Inches(0.35))
        p = tx.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
        r = p.add_run(); r.text = refs_text
        r.font.size = Pt(9); r.font.italic = True; r.font.color.rgb = LIGHT
    tx = slide.shapes.add_textbox(Inches(9.8), Inches(7.1), Inches(3.2), Inches(0.35))
    p = tx.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
    r = p.add_run(); r.text = "OLA 2026 — Barrera-García et al."
    r.font.size = Pt(10); r.font.color.rgb = LIGHT


def add_table(slide, data, left, top, width, height, header=True, font_size=14):
    rows, cols = len(data), len(data[0])
    tbl = slide.shapes.add_table(rows, cols, Inches(left), Inches(top),
                                  Inches(width), Inches(height)).table
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = str(val)
            for para in cell.text_frame.paragraphs:
                for run in para.runs:
                    run.font.size = Pt(font_size)
                    if header and r_idx == 0:
                        run.font.bold = True; run.font.color.rgb = WHITE
                    else:
                        run.font.color.rgb = NAVY
            if header and r_idx == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = NAVY
    return tbl


def set_notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


# ============================================================
# SLIDE 1 — Title with affiliations
# ============================================================
s = prs.slides.add_slide(BLANK)
tx = s.shapes.add_textbox(Inches(0.7), Inches(1.3), Inches(12), Inches(2.0))
tf = tx.text_frame; tf.word_wrap = True
p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "On the Impact of Linguistic Granularity\nand Fuzzy Semantic Design in\nParticle Swarm Optimization"
r.font.size = Pt(36); r.font.bold = True; r.font.color.rgb = NAVY

tx = s.shapes.add_textbox(Inches(0.7), Inches(3.6), Inches(12), Inches(0.6))
p = tx.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = ("José Barrera-García\u00B9\u02E3\u00B2  ·  Broderick Crawford\u00B9  ·  "
          "Eric Monfroy\u00B3  ·  Felipe Cisternas-Caneo\u00B9\u02E3\u00B2  ·  "
          "Ricardo Soto\u00B9  ·  Giovanni Giachetti\u2074")
r.font.size = Pt(15); r.font.color.rgb = GRAY

tx = s.shapes.add_textbox(Inches(0.7), Inches(4.3), Inches(12), Inches(2.0))
tf = tx.text_frame; tf.word_wrap = True
affils = [
    "\u00B9 Pontificia Universidad Católica de Valparaíso, Chile",
    "\u00B2 Universidad de Alcalá, Spain",
    "\u00B3 Université d'Angers, LERIA, France",
    "\u2074 Universidad Andrés Bello, Chile",
]
for i, line in enumerate(affils):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = line
    r.font.size = Pt(13); r.font.color.rgb = GRAY
    p.space_after = Pt(4)

tx = s.shapes.add_textbox(Inches(0.7), Inches(6.6), Inches(12), Inches(0.5))
p = tx.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "OLA 2026 — International Conference on Optimization and Learning"
r.font.size = Pt(15); r.font.bold = True; r.font.color.rgb = ACCENT

set_notes(s, (
    "SCRIPT (Slide 1 — Title):\n"
    "Good morning. Thank you for being here. My name is José Barrera-García, "
    "and I will present joint work with Broderick Crawford, Eric Monfroy, "
    "Felipe Cisternas-Caneo, Ricardo Soto, and Giovanni Giachetti, conducted "
    "across PUCV in Chile, the University of Alcalá in Spain, the University "
    "of Angers in France, and Universidad Andrés Bello. The talk is titled "
    "'On the Impact of Linguistic Granularity and Fuzzy Semantic Design in "
    "Particle Swarm Optimization.' I will spend the next fifteen minutes "
    "describing an experimental study that isolates one design dimension of "
    "fuzzy-controlled PSO that is rarely analysed in the literature."
))

# ============================================================
# SLIDE 2 — Abstract
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Summary")
add_subtitle(s, "Question: how much does the semantic design of a fuzzy controller actually matter in PSO?")
add_bullets(s, [
    "The performance of fuzzy-controlled PSO depends on design choices often treated as secondary.",
    "Linguistic granularity and membership-function design are rarely analysed explicitly.",
    "Experimental study: three- and five-label schemes under identical control logic (inputs: iteration progress + diversity).",
    "Finding: fuzzy control improves robustness in complex multimodal landscapes; it provides no benefit on unimodal or regular problems.",
])
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 2 — Summary):\n"
    "The work starts from a simple question. Fuzzy controllers are widely used "
    "to adapt PSO parameters, but most papers fix one fuzzy configuration up "
    "front and never test alternatives. We ask: how much does that semantic "
    "design — the number of linguistic labels and the shape of the membership "
    "functions — actually matter? Our study compares three- and five-label "
    "schemes under exactly the same control logic. The take-away, which I will "
    "develop in the rest of the talk, is that fuzzy control is not universally "
    "better: it helps on rugged multimodal problems, and clearly hurts on "
    "smooth or structurally regular ones."
))

# ============================================================
# SLIDE 3 — Introduction
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Motivation")
add_bullets(s, [
    "PSO performance depends on the exploration–exploitation balance, regulated by the inertia weight w [1, 2].",
    "Fuzzy control adapts w using qualitative descriptions of the search state [3].",
    "Most fuzzy-PSO variants fix linguistic partitions and membership functions a priori, with no semantic analysis.",
    "Research question: to what extent do different fuzzy schemes — under identical logic — change performance across landscapes?",
    (1, "Contribution: not a new algorithm. We isolate and measure the effect of fuzzy semantic design."),
])
add_footer(s, refs_text=(
    "[1] Kennedy & Eberhart, ICNN 1995  ·  "
    "[2] Shi & Eberhart, IEEE WCCI 1998  ·  "
    "[3] Shi & Eberhart, FUZZ-IEEE 2001"
))
set_notes(s, (
    "SCRIPT (Slide 3 — Motivation):\n"
    "PSO behaviour is governed by the inertia weight w, which controls the "
    "balance between exploration and exploitation. This was already clear in "
    "Kennedy and Eberhart's original paper, and was made explicit by Shi and "
    "Eberhart shortly after. Fuzzy control is a natural way to adapt w online: "
    "it lets us describe the search state qualitatively — 'low diversity', "
    "'late stage', and so on. The problem is that, in the literature, the "
    "fuzzy partition and the membership functions are almost always fixed a "
    "priori. Nobody asks whether that semantic choice matters. Our research "
    "question is exactly that. And let me be very explicit: this paper does "
    "not propose a new optimisation algorithm. It is an experimental study "
    "designed to isolate the effect of semantic design."
))

# ============================================================
# SLIDE 4 — Related Work
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Related Work")
add_bullets(s, [
    "Fuzzy adaptation in PSO: Shi & Eberhart [3] (seminal); Nobile et al. [4] FST-PSO; Xia et al. [5] MIMO fuzzy; Komarudin et al. [6] fuzzy signatures.",
    "Membership-function design: Olivas et al. [7] — different shapes give significant differences with the same rule base.",
    "Linguistic granularity & granular computing: Huang [8], Zhang [9], Zhao [10] — semantic resolution is not a neutral choice.",
    "Positioning: linguistic granularity is rarely an explicit experimental factor in PSO. This work fills that gap.",
], size=18)
add_footer(s, refs_text=(
    "[3] Shi & Eberhart 2001  ·  [4] Nobile et al. 2018  ·  [5] Xia et al. 2022  ·  "
    "[6] Komarudin et al. 2021  ·  [7] Olivas et al. 2014  ·  "
    "[8] Huang 2022  ·  [9] Zhang 2022  ·  [10] Zhao 2021"
))
set_notes(s, (
    "SCRIPT (Slide 4 — Related Work):\n"
    "The literature on fuzzy-adaptive PSO is rich. After Shi and Eberhart's "
    "seminal proposal, more sophisticated controllers appeared: Nobile's "
    "fuzzy self-tuning PSO, Xia's MIMO fuzzy controller, and Komarudin's "
    "fuzzy signatures. All of them focus on the architecture of the "
    "controller. A second line of work, exemplified by Olivas, has shown that "
    "even when the rule base is held fixed, changing membership-function "
    "shapes produces statistically significant performance differences. "
    "Finally, the granular-computing community — Huang, Zhang, and Zhao — has "
    "shown that linguistic resolution is not a neutral transformation. What "
    "is missing is the systematic combination of these observations inside "
    "PSO. Our work fills that gap."
))

# ============================================================
# SLIDE 5 — PSO Baseline
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Baseline Particle Swarm Optimization")
tx = s.shapes.add_textbox(Inches(0.7), Inches(1.6), Inches(12), Inches(1.8))
tf = tx.text_frame; tf.word_wrap = True
for i, line in enumerate([
    "v_i(t+1) = w · v_i(t) + c\u2081 r\u2081 (p_i − x_i(t)) + c\u2082 r\u2082 (g − x_i(t))",
    "x_i(t+1) = x_i(t) + v_i(t+1)",
]):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = line
    r.font.size = Pt(22); r.font.name = "Cambria Math"; r.font.color.rgb = NAVY
add_bullets(s, [
    "Baseline inertia: linear decreasing schedule, 0.9 → 0.1 [11].",
    "All other PSO parameters identical across variants — controlled comparison.",
    "Serves as the reference to assess the effect of fuzzy adaptation of w.",
], top=4.0, size=18)
add_footer(s, refs_text="[11] Abualigah et al., Computers & Industrial Engineering 2021")
set_notes(s, (
    "SCRIPT (Slide 5 — Baseline PSO):\n"
    "These are the standard PSO update equations. The only thing that "
    "changes between our experimental variants is the inertia weight w. The "
    "baseline uses a linear decreasing schedule from zero point nine down to "
    "zero point one, which is one of the most common choices in the "
    "literature. Every other parameter — population, cognitive and social "
    "coefficients, velocity bounds — is held identical across all variants. "
    "This is what allows us to attribute observed differences to the inertia "
    "control mechanism alone."
))

# ============================================================
# SLIDE 6 — Fuzzy controller
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Fuzzy Controller for Inertia Weight Adaptation")
add_bullets(s, [
    "Mamdani-type FIS, evaluated ONCE per iteration at the swarm level.",
    "Input 1 — Iteration progress:   t_progress = t / T_max",
    "Input 2 — Population diversity (per-dimension, normalised):",
    (1, "D(t) = (1/d) · Σ_k [ max_i x_{i,k}(t) − min_i x_{i,k}(t) ] / (U_k − L_k)"),
    "Output: w_t ∈ [w_min, w_max];   defuzzification by centroid.",
], top=1.4, size=18)
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 6 — Fuzzy Controller):\n"
    "We use a standard Mamdani fuzzy inference system, evaluated once per "
    "iteration at the swarm level, not at the particle level. It takes two "
    "normalised inputs. The first is iteration progress: a simple ratio "
    "between the current and the maximum iteration. The second is population "
    "diversity, computed per dimension as the normalised spatial spread of "
    "the swarm. This is a classical metric and bounds the value to the unit "
    "interval. The output is the inertia weight w, restricted to a working "
    "interval, and obtained by centroid defuzzification. The point I want to "
    "stress is that across all our variants, this architecture is exactly "
    "the same. Only the linguistic representation changes."
))

# ============================================================
# SLIDE 7 — Linguistic schemes
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Linguistic Schemes Evaluated")
add_bullets(s, [
    "Two granularities: 3 labels and 5 labels.",
    "For each granularity, two configurations: Set A and Set B.",
    "Sets A and B differ only in shape, overlap and placement of the membership functions.",
    "Linguistic variables, universes of discourse and rule structure: identical.",
    "Membership functions remain static throughout the optimisation.",
], top=1.3, size=17, height=2.6)
add_image(s, "06_input_diversity_comparison_membership_functions_I1.png",
          left=0.5, top=4.2, width=6.0, fallback_text="Diversity MFs")
add_image(s, "06_input_progress_comparison_membership_functions_I1.png",
          left=6.8, top=4.2, width=6.0, fallback_text="Progress MFs")
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 7 — Linguistic Schemes):\n"
    "We evaluate two linguistic granularities — three labels and five labels "
    "— and for each granularity we test two distinct configurations of "
    "membership functions, called Set A and Set B. Sets A and B differ only "
    "in the shape, the overlap, and the placement of the triangular and "
    "trapezoidal membership functions. The linguistic variables themselves, "
    "the universes of discourse, and the rule structure are kept identical. "
    "Membership functions are static — they do not change during the run. "
    "On the bottom you can see, on the left, the diversity input membership "
    "functions and, on the right, the iteration progress input. This four-way "
    "design — A3, B3, A5, B5 — is what lets us isolate the effect of "
    "semantic resolution from the effect of control logic."
))

# ============================================================
# SLIDE 8 — Output and rule base
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Output and Rule Base")
add_subtitle(s, "Increasing granularity refines the control surface while preserving the strategy.")
add_image(s, "04_fuzzy_rules_heatmap_3labels_R1.png",
          left=0.4, top=1.7, width=6.2, fallback_text="Rules 3-labels")
add_image(s, "04_fuzzy_rules_heatmap_5labels_R1.png",
          left=6.8, top=1.7, width=6.2, fallback_text="Rules 5-labels")
tx = s.shapes.add_textbox(Inches(0.4), Inches(6.5), Inches(12), Inches(0.4))
p = tx.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "Left: 3-label rule base    ·    Right: 5-label rule base"
r.font.size = Pt(14); r.font.italic = True; r.font.color.rgb = GRAY
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 8 — Rule Base):\n"
    "These two heatmaps show the rule base for both granularities. On the "
    "left, the three-by-three rule matrix for the three-label scheme; on the "
    "right, the five-by-five matrix for the five-label scheme. The colour "
    "coding indicates the dominant output linguistic term — low, medium, or "
    "high inertia — for each combination of inputs. The crucial point is that "
    "the qualitative strategy is preserved when we move from three to five "
    "labels: the rule base becomes finer, but it does not encode a different "
    "control philosophy. So any performance change we observe between "
    "granularities will reflect the resolution of the control surface, not a "
    "change of strategy."
))

# ============================================================
# SLIDE 9 — Benchmarks
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Benchmark Functions")
add_subtitle(s, "Classical functions with contrasting landscapes (Opfunu library [12]).")
data = [
    ["Function", "Type", "Dim.", "Global Optimum"],
    ["F1 (Sphere)",        "Unimodal",            "100", "0.0"],
    ["F11 (Griewank)",     "Multimodal regular",  "100", "0.0"],
    ["F21 (Shekel, m=5)",  "Multimodal rugged",   "4",   "−10.1532"],
    ["F23 (Shekel, m=10)", "Multimodal rugged",   "4",   "−10.5363"],
]
add_table(s, data, left=2.0, top=2.0, width=9.3, height=3.5, font_size=18)
add_footer(s, refs_text="[12] Van Thieu, Opfunu — Python library for benchmark functions, 2024")
set_notes(s, (
    "SCRIPT (Slide 9 — Benchmarks):\n"
    "We deliberately chose a small set of four classical functions, but with "
    "very different landscape characteristics. F1, the sphere function, is "
    "smooth and unimodal — we evaluate it in one hundred dimensions to "
    "stress convergence in a large search space. F11, Griewank, is "
    "multimodal but structurally regular, also in one hundred dimensions. "
    "F21 and F23 are Shekel functions in four dimensions, with five and ten "
    "components respectively — these are rugged, with many deep local minima "
    "concentrated in a small search space. All implementations come from the "
    "Opfunu library, so the definitions are reproducible and standard."
))

# ============================================================
# SLIDE 10 — Protocol
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Experimental Protocol")
data = [
    ["Parameter", "Value"],
    ["Population size", "50 particles"],
    ["Iterations", "500"],
    ["Independent runs", "31"],
    ["Random seeds", "42, 43, …, 72 (shared across algorithms)"],
    ["Hardware", "Intel Core i7 2.8 GHz, 16 GB RAM"],
    ["Implementation", "Python 3.11.9, sequential CPU execution"],
]
add_table(s, data, left=1.0, top=1.5, width=8.5, height=3.6, font_size=15)
tx = s.shapes.add_textbox(Inches(9.8), Inches(1.5), Inches(3.3), Inches(5))
tf = tx.text_frame; tf.word_wrap = True
items = [
    ("Variants:", 16, True),
    ("PSO baseline", 14, False),
    ("PSO-FCS-A3", 14, False),
    ("PSO-FCS-B3", 14, False),
    ("PSO-FCS-A5", 14, False),
    ("PSO-FCS-B5", 14, False),
    ("", 10, False),
    ("Performance metric:", 16, True),
    ("Gap(%) = |f_best − f_opt| / |f_opt| × 100", 13, False),
]
for i, (txt, sz, bold) in enumerate(items):
    p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
    r = p.add_run(); r.text = txt
    r.font.size = Pt(sz); r.font.bold = bold
    r.font.color.rgb = NAVY if bold else GRAY
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 10 — Experimental Protocol):\n"
    "All variants share an identical experimental protocol: fifty particles, "
    "five hundred iterations, thirty-one independent runs per algorithm-"
    "function combination. To reduce stochastic noise while preserving "
    "comparability, we use a shared seeding strategy: every algorithm uses "
    "the same seed for the same run number, starting at forty-two. We "
    "evaluate the baseline PSO plus the four fuzzy variants — A three, B "
    "three, A five, B five. Performance is measured by the relative gap to "
    "the known optimum, and we report mean and standard deviation over the "
    "thirty-one runs."
))

# ============================================================
# SLIDE 11 — Results table
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Results — Performance Summary")
add_subtitle(s, "Best variant per function highlighted (mean fitness, std, mean gap, time [s]).")
data = [
    ["Function", "Method",        "Mean Fitness", "Std Dev",  "Mean Gap (%)", "Time (s)"],
    ["F1",  "PSO",          "23.070",     "11.474",  "23.1%",      "9.903"],
    ["F1",  "PSO-FCS-A3",   "74972.756",  "3560.587","74972.8%",   "12.028"],
    ["F1",  "PSO-FCS-A5",   "74768.800",  "3863.507","74768.8%",   "12.059"],
    ["F1",  "PSO-FCS-B3",   "74912.469",  "3653.264","74912.5%",   "12.076"],
    ["F1",  "PSO-FCS-B5",   "76414.155",  "3178.414","76414.2%",   "12.769"],
    ["F11", "PSO",          "1.208",      "0.103",   "1.2%",       "10.308"],
    ["F11", "PSO-FCS-A3",   "675.755",    "32.045",  "675.8%",     "12.686"],
    ["F11", "PSO-FCS-A5",   "674.625",    "34.755",  "674.6%",     "12.072"],
    ["F11", "PSO-FCS-B3",   "675.212",    "32.879",  "675.2%",     "12.176"],
    ["F11", "PSO-FCS-B5",   "688.725",    "28.603",  "688.7%",     "12.019"],
    ["F21", "PSO",          "−6.289",     "3.803",   "38.1%",      "5.928"],
    ["F21", "PSO-FCS-A3",   "−7.649",     "1.598",   "24.7%",      "6.190"],
    ["F21", "PSO-FCS-A5",   "−7.749",     "1.275",   "23.7%",      "6.385"],
    ["F21", "PSO-FCS-B3",   "−7.683",     "1.659",   "24.3%",      "6.216"],
    ["F21", "PSO-FCS-B5",   "−7.699",     "1.602",   "24.2%",      "6.353"],
    ["F23", "PSO",          "−7.519",     "3.877",   "28.6%",      "10.761"],
    ["F23", "PSO-FCS-A3",   "−8.203",     "1.419",   "22.1%",      "10.973"],
    ["F23", "PSO-FCS-A5",   "−8.133",     "1.279",   "22.8%",      "11.145"],
    ["F23", "PSO-FCS-B3",   "−8.139",     "1.243",   "22.8%",      "10.979"],
    ["F23", "PSO-FCS-B5",   "−8.124",     "1.339",   "22.9%",      "11.133"],
]
tbl = add_table(s, data, left=0.5, top=1.55, width=12.3, height=5.4, font_size=10)
for ridx in [1, 6, 13, 17]:
    for c in range(len(data[0])):
        cell = tbl.cell(ridx, c)
        cell.fill.solid(); cell.fill.fore_color.rgb = HIGHLIGHT
        for para in cell.text_frame.paragraphs:
            for run in para.runs:
                run.font.bold = True; run.font.color.rgb = ACCENT
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 11 — Results Table):\n"
    "This is the full performance summary; let me walk you through the key "
    "rows. On F1, the unimodal sphere, baseline PSO reaches a mean fitness "
    "of about twenty-three, while every fuzzy variant collapses to roughly "
    "seventy-five thousand — a gap of more than seventy thousand percent. "
    "Something similar happens on F11, the regular Griewank function: PSO "
    "gets one point two, fuzzy variants stay around six hundred and "
    "seventy-five. I want to be direct about this: in these two settings, "
    "fuzzy adaptation is catastrophic. The picture flips on the rugged "
    "Shekel functions. On F21, baseline PSO has a gap of thirty-eight "
    "percent; the best fuzzy variant, A-five, brings it down to twenty-three "
    "point seven. On F23, the gap drops from twenty-eight point six to "
    "twenty-two point one with A-three. And — importantly — the standard "
    "deviation is roughly halved. So fuzzy control buys us robustness on "
    "the right kind of problem."
))

# ============================================================
# SLIDE 12 — Problem-dependent insight
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Main Insight: the Effect Is Problem-Dependent")
data = [
    ["Smooth / regular landscapes (F1, F11)", "Rugged multimodal (F21, F23)"],
    ["Baseline PSO dominates",                 "Fuzzy-controlled PSO dominates"],
    ["Fuzzy adaptation interferes\nwith efficient baseline dynamics", "Fuzzy adaptation improves\nmean and robustness"],
    ["Fuzzy variants drastically inflate the gap", "Fuzzy variants noticeably reduce the std"],
    ["Fuzzy time slightly higher (~12 s vs ~10 s)", "Modest overhead, justified by the gain"],
]
add_table(s, data, left=0.7, top=1.7, width=12.0, height=4.5, font_size=15)
tx = s.shapes.add_textbox(Inches(0.7), Inches(6.5), Inches(12.0), Inches(0.5))
p = tx.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run()
r.text = "\"Fuzzy-controlled inertia adaptation is strongly problem-dependent.\" — paper"
r.font.size = Pt(14); r.font.italic = True; r.font.color.rgb = ACCENT
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 12 — Problem-Dependent Insight):\n"
    "The contrast on the previous slide leads us to the central claim of the "
    "paper. On the left column, smooth or structurally regular landscapes: "
    "baseline PSO dominates, and fuzzy adaptation actually interferes with "
    "an already efficient process. On the right column, rugged multimodal "
    "landscapes: fuzzy control improves both the mean and the robustness. "
    "The execution-time overhead of the fuzzy inference — about two extra "
    "seconds per run — is modest and is justified only when fuzzy control "
    "actually helps. The honest take-away is the one in italics: fuzzy "
    "adaptation is strongly problem-dependent. There is no universal "
    "winner, and any future work that claims one should be questioned."
))

# ============================================================
# SLIDE 13 — Granularity & MF design
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Effect of Granularity and MF Design")
add_bullets(s, [
    "On F1 and F11: no configuration (granularity nor Set A/B) recovers the baseline performance.",
    "On F21 and F23: 5-label schemes give a mild improvement in mean gap and, at times, lower variability.",
    "Set A vs Set B: no systematic advantage for either configuration on any function.",
    "Conclusion: semantic design is a measurable but secondary effect.",
    (1, "The dominant factor is whether an adaptive mechanism is appropriate — not how it is semantically refined."),
], size=18)
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 13 — Granularity Effect):\n"
    "Now to the central research question. When fuzzy control fails — on F1 "
    "and F11 — neither switching to five labels nor changing from Set A to "
    "Set B rescues the performance. When fuzzy control works — on F21 and "
    "F23 — five-label schemes do tend to give a small additional improvement "
    "in mean gap and sometimes lower variability, but the effect is mild and "
    "not consistent. Comparing Set A against Set B, we observe no systematic "
    "advantage for either, on any function. So our answer to the research "
    "question is: semantic design is a measurable factor, but a secondary "
    "one. The first-order question is whether to use adaptive control at "
    "all; semantic refinement is a second-order tuning lever."
))

# ============================================================
# SLIDE 14 — Conclusions
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Conclusions and Future Work")
add_bullets(s, [
    "1. Baseline PSO outperforms fuzzy variants on unimodal or structurally regular problems.",
    "2. On complex multimodal problems, PSO-FCS improves average performance and robustness (lower mean gap, lower std).",
    "3. Linguistic granularity and MF design have a measurable but secondary effect — no configuration dominates universally.",
    "",
    "Future work:",
    (1, "Additional search-process metrics as fuzzy inputs."),
    (1, "Dynamic mechanisms to select / adapt the fuzzy configuration online."),
    (1, "Machine-learning-assisted meta-control of adaptive fuzzy strategies [13]."),
], size=17, top=1.4)
add_footer(s, refs_text="[13] Karimi-Mamaghan et al., EJOR 2022 — Machine learning at the service of metaheuristics")
set_notes(s, (
    "SCRIPT (Slide 14 — Conclusions and Future Work):\n"
    "To summarise the three key findings. First: baseline PSO is hard to "
    "beat on unimodal or structurally regular problems — adaptive inertia "
    "tends to disrupt rather than help. Second: on complex multimodal "
    "problems, fuzzy-controlled PSO does deliver a meaningful improvement "
    "in both average performance and robustness. Third: the semantic design "
    "of the controller — granularity and membership functions — is "
    "measurable, but it is a secondary effect compared to the binary "
    "decision of using adaptive control or not. Going forward, we plan to "
    "enrich the controller's inputs with additional search-process metrics, "
    "to design dynamic mechanisms that switch fuzzy configurations during "
    "the run, and to explore machine-learning-assisted meta-control, in "
    "line with recent work at the intersection of ML and metaheuristics."
))

# ============================================================
# SLIDE 15 — Acknowledgements & Q&A
# ============================================================
s = prs.slides.add_slide(BLANK)
add_title(s, "Acknowledgements · Questions")
add_bullets(s, [
    "ANID Doctorado Nacional 21230203 — F. Cisternas-Caneo",
    "ANID Doctorado Nacional 21242516 — J. Barrera-García",
    "",
    "Contact: jose.barrera@pucv.cl",
], top=1.7, size=20)
tx = s.shapes.add_textbox(Inches(0.5), Inches(4.5), Inches(12.3), Inches(2.0))
p = tx.text_frame.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
r = p.add_run(); r.text = "Questions?"
r.font.size = Pt(60); r.font.bold = True; r.font.color.rgb = NAVY
add_footer(s)
set_notes(s, (
    "SCRIPT (Slide 15 — Acknowledgements & Q&A):\n"
    "Before opening for questions, I want to acknowledge ANID Chile, which "
    "supports both Felipe Cisternas-Caneo and myself through National "
    "Doctoral scholarships. Thanks again to the OLA programme committee for "
    "the opportunity to present, and to all of you for your attention. I "
    "would be very happy to take questions now."
))

prs.save(str(OUT))
print(f"OK: {OUT}")
print(f"Slides: {len(prs.slides)}")
