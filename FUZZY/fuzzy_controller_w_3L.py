import numpy as np

def tri(x, a, b, c):
    """Triangular membership. Permite hombros si a=b o b=c."""
    x = float(x)
    if a == b and x <= b:
        return 1.0
    if b == c and x >= b:
        return 1.0
    if x <= a or x >= c:
        return 0.0
    if a < x < b:
        return (x - a) / (b - a + 1e-12)
    if b < x < c:
        return (c - x) / (c - b + 1e-12)
    return 1.0 if x == b else 0.0


class FuzzyInertiaController_3L:
    """
    Mamdani FIS (3 labels: low, medium, high):
      Inputs: diversity_ratio d in [0,1], progress t in [0,1]
      Output: w in [wMin, wMax]
    
    CLEI2026: input_set controla las MFs de entrada (diversity, progress).
    w_set controla las MFs de salida (inertia weight).
    """

    def __init__(self, w_set, input_set="I1", rule_set="R1", wMin=0.0, wMax=1.0, n_grid=501):
        self.wMin = float(wMin)
        self.wMax = float(wMax)
        self.w_set = str(w_set).upper()
        self.input_set = str(input_set).upper()
        self.rule_set = str(rule_set).upper()
        self.n_grid = int(n_grid)
        self.w_history = [self.wMax]  # Valor inicial: exploración máxima en iter=0


        # Universo de salida normalizado [0,1]
        self.y = np.linspace(0.0, 1.0, self.n_grid)

        # Entradas: configurables via input_set (CLEI2026)
        self.div_mf, self.it_mf = self._build_input_mfs(self.input_set)

        # Salida w (set A estricta; set B con hombro)
        self.w_mf = self._build_w_mfs(self.w_set)

        # Precomputar cotas de centroide para rescalado interno
        self._w_norm_min, self._w_norm_max = self._compute_centroid_bounds()

        # Reglas 3x3: seleccionables via rule_set (WEA2026)
        self.rules = self._build_rules(self.rule_set)

    def _build_input_mfs(self, input_set):
        """
        CLEI2026: Define diferentes configuraciones de MFs para las variables de entrada.
        Todas usan 3 etiquetas (low/medium/high para diversity, early/mid/late para progress).
        
        I1 - Standard:  Distribución uniforme, solapamiento moderado (baseline OLA2026)
        I2 - Narrow:    Menor solapamiento, transiciones más abruptas
        I3 - Wide:      Mayor solapamiento, transiciones más suaves
        I4 - Shoulder:  Funciones hombro en extremos (trapezoidal), mayor certeza en bordes
        """
        INPUT_SETS = {
            # I1: Standard/Simétrico - baseline (distribución actual OLA2026)
            "I1": {
                "div": {
                    "low":    (0.0, 0.2, 0.4),
                    "medium": (0.3, 0.5, 0.7),
                    "high":   (0.6, 0.8, 1.0),
                },
                "it": {
                    "early":  (0.0, 0.2, 0.4),
                    "mid":    (0.3, 0.5, 0.7),
                    "late":   (0.6, 0.8, 1.0),
                },
            },
            # I2: Narrow/Separado - menor solapamiento, zonas de transición más estrechas
            # "I2": {
            #     "div": {
            #         "low":    (0.0, 0.16, 0.33),
            #         "medium": (0.33, 0.5, 0.66),
            #         "high":   (0.66, 0.84, 1.0),
            #     },
            #     "it": {
            #         "early":  (0.0, 0.16, 0.33),
            #         "mid":    (0.33, 0.5, 0.66),
            #         "late":   (0.66, 0.84, 1.0),
            #     },
            # },
            # I3: Wide/Amplio - máximo solapamiento, mezcla más gradual
            # "I3": {
            #     "div": {
            #         "low":    (0.0, 0.25, 0.5),
            #         "medium": (0.25, 0.5, 0.75),
            #         "high":   (0.5, 0.75, 1.0),
            #     },
            #     "it": {
            #         "early":  (0.0, 0.25, 0.5),
            #         "mid":    (0.25, 0.5, 0.75),
            #         "late":   (0.5, 0.75, 1.0),
            #     },
            # },
            # I4: Shoulder/Hombro - funciones trapezoidales en los extremos
            # "I4": {
            #     "div": {
            #         "low":    (0.0, 0.0, 0.35),    # hombro izquierdo
            #         "medium": (0.2, 0.5, 0.8),
            #         "high":   (0.65, 1.0, 1.0),    # hombro derecho
            #     },
            #     "it": {
            #         "early":  (0.0, 0.0, 0.35),    # hombro izquierdo
            #         "mid":    (0.2, 0.5, 0.8),
            #         "late":   (0.65, 1.0, 1.0),    # hombro derecho
            #     },
            # },
        }
        if input_set not in INPUT_SETS:
            raise ValueError(f"input_set='{input_set}' no definido. Sets disponibles: {list(INPUT_SETS.keys())}")
        
        return INPUT_SETS[input_set]["div"], INPUT_SETS[input_set]["it"]

    def _compute_centroid_bounds(self):
        """Calcula centroides min/max de las MFs de salida para rescalado [0,1]."""
        centroids = []
        for label, (a, b, c) in self.w_mf.items():
            mf_vals = np.array([tri(val, a, b, c) for val in self.y], dtype=float)
            den = np.trapz(mf_vals, self.y)
            if den > 1e-12:
                centroids.append(np.trapz(self.y * mf_vals, self.y) / den)
        return min(centroids), max(centroids)

    def _build_w_mfs(self, w_set):
        W_SETS ={
            "O1": {
                "high":   (0.50, 1.0, 1.0),  # #cambiado a hombro para w alto, favoreciendo un w alto (exploración máxima)
                "medium": (0.25, 0.5, 0.75),  # 
                "low":    (0.00, 0.0, 0.50),  #  #cambiado a hombro para w bajo, favoreciendo un w bajo(explotación máxima)
            },
            #"O2": {
            #    "high":   (0.50, 0.75, 0.75),  # 
            #    "medium": (0.25, 0.5, 0.75),  # 
            #    "low":    (0.25, 0.25, 0.50),  # 
            #},
            #"O3": {
            #    "high":   (0.60, 0.75, 0.90),  # 
            #    "medium": (0.35, 0.5, 0.65),  # 
            #    "low":    (0.10, 0.25, 0.40),  #     
            #},
            #"O4": {
            #    "high":   (0.60, 0.80, 0.80),  # 
            #    "medium": (0.35, 0.5, 0.65),  # 
            #    "low":    (0.20, 0.20, 0.40),  #  
            #},
        }
        if w_set not in W_SETS:
            raise ValueError(f"w_set='{w_set}' no definido. Sets disponibles: {list(W_SETS.keys())}")
        
        return W_SETS[w_set]

    def _build_rules(self, rule_set):
        """
        WEA2026: 8 variantes de bases de reglas 3×3 (9 reglas cada una).
        Rows = diversity (low, medium, high), Columns = progress (early, mid, late).
        
        Diseño factorial ortogonal 2×3:
                            Div-agnostic(—)  Div-following(→)  Div-compensating(←)
        Progress ↓ (H→L):  R1               R5                R6
        Progress ↑ (L→H):  R2               R7                R8
        Progress — (flat):  (not useful)     R3                R4

        Additive model: output = clip(progress_effect + diversity_effect)
        3L mapping: sum ≤ -1 → L, sum = 0 → M, sum ≥ +1 → H

        R1: Progress ↓, diversity-agnostic (emulates PSO standard linear decrease)
        R2: Progress ↑, diversity-agnostic (anti-classical)
        R3: Diversity-following, progress-agnostic (w tracks diversity)
        R4: Diversity-compensating, progress-agnostic (w opposes diversity)
        R5: Progress ↓ + diversity-following (classical + adaptive)
        R6: Progress ↓ + diversity-compensating (classical + reactive)
        R7: Progress ↑ + diversity-following (anti-classical + adaptive)
        R8: Progress ↑ + diversity-compensating (anti-classical + reactive)

        Mirror pairs: R1↔R2, R3↔R4, R5↔R8, R6↔R7
        """
        RULE_SETS = {
            # R1: Progress ↓, diversity-agnostic (emulates PSO standard linear w decrease)
            # All rows identical: H → M → L
            "R1": {
                ("low",    "early"): "high",
                ("medium", "early"): "high",
                ("high",   "early"): "high",
                ("low",    "mid"):   "medium",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "medium",
                ("low",    "late"):  "low",
                ("medium", "late"):  "low",
                ("high",   "late"):  "low",
            },
            # R2: Progress ↑, diversity-agnostic (anti-classical: exploit early, explore late)
            # All rows identical: L → M → H (mirror of R1)
            "R2": {
                ("low",    "early"): "low",
                ("medium", "early"): "low",
                ("high",   "early"): "low",
                ("low",    "mid"):   "medium",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "medium",
                ("low",    "late"):  "high",
                ("medium", "late"):  "high",
                ("high",   "late"):  "high",
            },
            # R3: Diversity-following, progress-agnostic (w tracks diversity)
            # All columns identical: L → M → H (mirror of R4)
            "R3": {
                ("low",    "early"): "low",
                ("medium", "early"): "medium",
                ("high",   "early"): "high",
                ("low",    "mid"):   "low",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "high",
                ("low",    "late"):  "low",
                ("medium", "late"):  "medium",
                ("high",   "late"):  "high",
            },
            # R4: Diversity-compensating, progress-agnostic (w opposes diversity)
            # All columns identical: H → M → L (mirror of R3)
            "R4": {
                ("low",    "early"): "high",
                ("medium", "early"): "medium",
                ("high",   "early"): "low",
                ("low",    "mid"):   "high",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "low",
                ("low",    "late"):  "high",
                ("medium", "late"):  "medium",
                ("high",   "late"):  "low",
            },
            # R5: Progress ↓ + diversity-following (additive: explore early + w tracks diversity)
            # Diagonal gradient: high top-left, low bottom-right (mirror of R8)
            "R5": {
                ("low",    "early"): "medium",
                ("medium", "early"): "high",
                ("high",   "early"): "high",
                ("low",    "mid"):   "low",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "high",
                ("low",    "late"):  "low",
                ("medium", "late"):  "low",
                ("high",   "late"):  "medium",
            },
            # R6: Progress ↓ + diversity-compensating (additive: explore early + w opposes diversity)
            # Diagonal gradient: high bottom-left, low top-right (mirror of R7)
            "R6": {
                ("low",    "early"): "high",
                ("medium", "early"): "high",
                ("high",   "early"): "medium",
                ("low",    "mid"):   "high",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "low",
                ("low",    "late"):  "medium",
                ("medium", "late"):  "low",
                ("high",   "late"):  "low",
            },
            # R7: Progress ↑ + diversity-following (additive: exploit early + w tracks diversity)
            # Diagonal gradient: low top-left, high bottom-right (mirror of R6)
            "R7": {
                ("low",    "early"): "low",
                ("medium", "early"): "low",
                ("high",   "early"): "medium",
                ("low",    "mid"):   "low",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "high",
                ("low",    "late"):  "medium",
                ("medium", "late"):  "high",
                ("high",   "late"):  "high",
            },
            # R8: Progress ↑ + diversity-compensating (additive: exploit early + w opposes diversity)
            # Diagonal gradient: low bottom-left, high top-right (mirror of R5)
            "R8": {
                ("low",    "early"): "medium",
                ("medium", "early"): "low",
                ("high",   "early"): "low",
                ("low",    "mid"):   "high",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "low",
                ("low",    "late"):  "high",
                ("medium", "late"):  "high",
                ("high",   "late"):  "medium",
            },
        }
        if rule_set not in RULE_SETS:
            raise ValueError(f"rule_set='{rule_set}' no definido. Sets disponibles: {list(RULE_SETS.keys())}")
        
        return RULE_SETS[rule_set]


    def compute_w(self, diversity_ratio, progress):
        # Reparación mínima: evitar bordes exactos (0 o 1) para no quedar sin reglas activas
        eps = 1e-12
        d = float(np.clip(diversity_ratio, eps, 1.0 - eps))
        t = float(np.clip(progress, eps, 1.0 - eps))

        # Fuzzificación
        mu_d = {k: tri(d, *abc) for k, abc in self.div_mf.items()}
        mu_t = {k: tri(t, *abc) for k, abc in self.it_mf.items()}

        # Inferencia Mamdani (min) + agregación (max)
        agg = np.zeros_like(self.y, dtype=float)

        for (d_lab, t_lab), out_lab in self.rules.items():
            firing = min(mu_d[d_lab], mu_t[t_lab])
            if firing <= 0.0:
                continue

            a, b, c = self.w_mf[out_lab]
            mf_out = np.array([tri(val, a, b, c) for val in self.y], dtype=float)
            agg = np.maximum(agg, np.minimum(firing, mf_out))

        # Defuzzificación (centroide)
        den = np.trapz(agg, self.y)
        if den <= 1e-12:
            w_norm = 0.5
        else:
            w_norm = np.trapz(self.y * agg, self.y) / den

        # Rescalar w_norm de [c_min, c_max] a [0, 1] (compensa compresión del centroide)
        w_norm = (w_norm - self._w_norm_min) / (self._w_norm_max - self._w_norm_min)
        w_norm = float(np.clip(w_norm, 0.0, 1.0))

        # Escalamiento a [wMin, wMax]
        w = self.wMin + w_norm * (self.wMax - self.wMin)
        w = float(np.clip(w, self.wMin, self.wMax))
        self.w_history.append(w)
        return w


def get_fuzzy_controller(w_set, num_labels=3, input_set="I1", rule_set="R1", wMin=0.0, wMax=1.0):
    """Factory unico: enruta SIEMPRE al controlador parametrico FuzzyInertiaController_Auto.

    Las particiones y reglas se generan algorithmically desde config/fuzzy_partitions.json
    (make_partition_uniform + make_rule_matrix). Soporta num_labels >= 2 arbitrario.

    Los controladores legacy FuzzyInertiaController_3L / _5L permanecen disponibles
    por import directo pero NO se invocan via este factory (sus MFs ad-hoc de WEA2026
    son referencia historica, no parte del esquema MDPI sistematizado).
    """
    from FUZZY.fuzzy_controller_auto import FuzzyInertiaController_Auto
    return FuzzyInertiaController_Auto(
        w_set=w_set, num_labels=num_labels, input_set=input_set,
        rule_set=rule_set, wMin=wMin, wMax=wMax,
    )
