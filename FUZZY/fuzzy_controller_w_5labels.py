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


class FuzzyInertiaController_5labels:
    """
    Mamdani FIS con 5 etiquetas lingüísticas:
      Inputs: diversity_ratio d in [0,1], progress t in [0,1]
      Output: w in [0, 1]
      
    5 etiquetas: very_low, low, medium, high, very_high
    Reglas: 5×5 = 25
    
    CLEI2026: input_set controla las MFs de entrada (diversity, progress).
    w_set controla las MFs de salida (inertia weight).
    """

    def __init__(self, w_set, input_set="I1", rule_set="R1", n_grid=501):
        self.wMin = 0.0
        self.wMax = 1.0
        self.w_set = str(w_set).upper()
        self.input_set = str(input_set).upper()
        self.rule_set = str(rule_set).upper()
        self.n_grid = int(n_grid)
        self.w_history = [self.wMax]  # Valor inicial: exploración máxima en iter=0

        # Universo de salida normalizado [0,1]
        self.y = np.linspace(0.0, 1.0, self.n_grid)

        # Entradas: configurables via input_set (CLEI2026)
        self.div_mf, self.it_mf = self._build_input_mfs(self.input_set)

        # Salida w (sets A, B con 5 etiquetas)
        self.w_mf = self._build_w_mfs(self.w_set)

        # Reglas 5x5: seleccionables via rule_set (WEA2026)
        self.rules = self._build_rules_5x5(self.rule_set)

    def _build_input_mfs(self, input_set):
        """
        CLEI2026: Define diferentes configuraciones de MFs para las variables de entrada.
        Todas usan 5 etiquetas para diversity y progress.
        
        I1 - Standard:  Distribución uniforme, solapamiento moderado (baseline OLA2026)
        I2 - Narrow:    Menor solapamiento, transiciones más abruptas
        I3 - Wide:      Mayor solapamiento, transiciones más suaves
        I4 - Shoulder:  Funciones hombro en extremos, mayor certeza en bordes
        """
        INPUT_SETS = {
            # I1: Standard - baseline (distribución actual OLA2026)
            "I1": {
                "div": {
                    "very_low": (0.0, 0.15, 0.30),
                    "low":      (0.2, 0.35, 0.5),
                    "medium":   (0.35, 0.5, 0.65),
                    "high":     (0.5, 0.65, 0.80),
                    "very_high":(0.7, 0.85, 1.0),
                },
                "it": {
                    "very_early": (0.0, 0.15, 0.30),
                    "early":      (0.2, 0.35, 0.5),
                    "mid":        (0.35, 0.5, 0.65),
                    "late":       (0.5, 0.65, 0.80),
                    "very_late":  (0.7, 0.85, 1.0),
                },
            },
            # I2: Narrow/Separado - menor solapamiento, transiciones más estrechas
            "I2": {
                "div": {
                    "very_low": (0.0, 0.1, 0.2),
                    "low":      (0.2, 0.3, 0.4),
                    "medium":   (0.4, 0.5, 0.6),
                    "high":     (0.6, 0.7, 0.8),
                    "very_high":(0.8, 0.9, 1.0),
                },
                "it": {
                    "very_early": (0.0, 0.1, 0.2),
                    "early":      (0.2, 0.3, 0.4),
                    "mid":        (0.4, 0.5, 0.6),
                    "late":       (0.6, 0.7, 0.8),
                    "very_late":  (0.8, 0.9, 1.0),
                },
            },
            # I3: Wide/Amplio - máximo solapamiento, mezcla más gradual
            "I3": {
                "div": {
                    "very_low": (0.0, 0.15, 0.35),
                    "low":      (0.15, 0.3, 0.5),
                    "medium":   (0.3, 0.5, 0.7),
                    "high":     (0.5, 0.7, 0.85),
                    "very_high":(0.65, 0.85, 1.0),
                },
                "it": {
                    "very_early": (0.0, 0.15, 0.35),
                    "early":      (0.15, 0.3, 0.5),
                    "mid":        (0.3, 0.5, 0.7),
                    "late":       (0.5, 0.7, 0.85),
                    "very_late":  (0.65, 0.85, 1.0),
                },
            },
            # I4: Shoulder/Hombro - funciones trapezoidales en los extremos
            "I4": {
                "div": {
                    "very_low": (0.0, 0.0, 0.25),      # hombro izquierdo
                    "low":      (0.15, 0.3, 0.45),
                    "medium":   (0.35, 0.5, 0.65),
                    "high":     (0.55, 0.7, 0.85),
                    "very_high":(0.75, 1.0, 1.0),      # hombro derecho
                },
                "it": {
                    "very_early": (0.0, 0.0, 0.25),    # hombro izquierdo
                    "early":      (0.15, 0.3, 0.45),
                    "mid":        (0.35, 0.5, 0.65),
                    "late":       (0.55, 0.7, 0.85),
                    "very_late":  (0.75, 1.0, 1.0),    # hombro derecho
                },
            },
        }
        if input_set not in INPUT_SETS:
            raise ValueError(f"input_set='{input_set}' no definido. Sets disponibles: {list(INPUT_SETS.keys())}")
        
        return INPUT_SETS[input_set]["div"], INPUT_SETS[input_set]["it"]

    def _build_w_mfs(self, w_set):
        """
        Mapeo de sets A, B, C, D con 5 etiquetas.
        
        Distribución en [0, 1]:
        - very_low:  0.0-0.2  (puro explotador)
        - low:       0.2-0.4  (explotador)
        - medium:    0.4-0.6  (balanceado)
        - high:      0.6-0.8  (explorador)
        - very_high: 0.8-1.0  (puro explorador)
        
        Sets replicados de la versión 3-labels, extendidos a 5:
        """
        W_SETS = {
            "A": {
                # Set B: Balanceado (distribución uniforme [0.0;1.0])
                "very_low": (0.0, 0.17, 0.33),
                "low":      (0.17, 0.33, 0.5),
                "medium":   (0.33, 0.5, 0.67),
                "high":     (0.50, 0.67, 0.83),
                "very_high":(0.67, 0.83, 1.0),
            },
            "B": {
                # Set C: Mayor Peso en los extremos (distribución uniforme [0.1;0.9])
                "very_low": (0.23, 0.23, 0.37),
                "low":      (0.23, 0.37, 0.5),
                "medium":   (0.37, 0.5, 0.63),
                "high":     (0.5, 0.63, 0.77),
                "very_high":(0.63, 0.77, 0.77),
            },
            #"C": {
            #    # Set A: Balanceado (distribución uniforme [0.1;0.9])
            #    "very_low": (0.1, 0.23, 0.37),
            #    "low":      (0.23, 0.37, 0.5),
            #    "medium":   (0.37, 0.5, 0.63),
            #    "high":     (0.5, 0.63, 0.77),
            #    "very_high":(0.63, 0.77, 0.90),
            #},
            #"D": {
            #    # Set D: Mayor Peso en los extremos (distribución uniforme [0.0;0.1])
            #    "very_low": (0.17, 0.17, 0.33),
            #    "low":      (0.17, 0.33, 0.5),
            #    "medium":   (0.33, 0.5, 0.67),
            #    "high":     (0.50, 0.67, 0.83),
            #    "very_high":(0.67, 0.83, 0.83),
            #},
        }
        if w_set not in W_SETS:
            raise ValueError(f"w_set='{w_set}' no definido. Sets disponibles: {list(W_SETS.keys())}")
        
        return W_SETS[w_set]

    def _build_rules_5x5(self, rule_set):
        """
        WEA2026: 6 variantes de bases de reglas 5×5 (25 reglas cada una).
        Rows = diversity (very_low..very_high), Columns = progress (very_early..very_late).
        
        R1: Baseline - explore early, exploit late, diversity-reactive
        R2: Exploitation-dominant - aggressive low w bias
        R3: Exploration-dominant - aggressive high w bias
        R4: Diversity-reactive - w = f(diversity) only, progress-agnostic
        R5: Progress-dominant - w = f(progress) only, diversity-agnostic
        R6: Inverse - opposite of R1 (exploit early, explore late)
        """
        RULE_SETS = {
            # R1: Baseline (current system)
            "R1": {
                ("very_low", "very_early"): "very_high",
                ("very_low", "early"):      "very_high",
                ("very_low", "mid"):        "high",
                ("very_low", "late"):       "high",
                ("very_low", "very_late"):  "medium",
                ("low", "very_early"):      "very_high",
                ("low", "early"):           "high",
                ("low", "mid"):             "high",
                ("low", "late"):            "medium",
                ("low", "very_late"):       "low",
                ("medium", "very_early"):   "high",
                ("medium", "early"):        "high",
                ("medium", "mid"):          "medium",
                ("medium", "late"):         "low",
                ("medium", "very_late"):    "very_low",
                ("high", "very_early"):     "high",
                ("high", "early"):          "medium",
                ("high", "mid"):            "medium",
                ("high", "late"):           "low",
                ("high", "very_late"):      "very_low",
                ("very_high", "very_early"):"medium",
                ("very_high", "early"):     "medium",
                ("very_high", "mid"):       "low",
                ("very_high", "late"):      "very_low",
                ("very_high", "very_late"): "very_low",
            },
            # R2: Exploitation-dominant
            "R2": {
                ("very_low", "very_early"): "high",
                ("very_low", "early"):      "medium",
                ("very_low", "mid"):        "low",
                ("very_low", "late"):       "very_low",
                ("very_low", "very_late"):  "very_low",
                ("low", "very_early"):      "medium",
                ("low", "early"):           "medium",
                ("low", "mid"):             "low",
                ("low", "late"):            "very_low",
                ("low", "very_late"):       "very_low",
                ("medium", "very_early"):   "medium",
                ("medium", "early"):        "low",
                ("medium", "mid"):          "low",
                ("medium", "late"):         "very_low",
                ("medium", "very_late"):    "very_low",
                ("high", "very_early"):     "medium",
                ("high", "early"):          "low",
                ("high", "mid"):            "very_low",
                ("high", "late"):           "very_low",
                ("high", "very_late"):      "very_low",
                ("very_high", "very_early"):"low",
                ("very_high", "early"):     "low",
                ("very_high", "mid"):       "very_low",
                ("very_high", "late"):      "very_low",
                ("very_high", "very_late"): "very_low",
            },
            # R3: Exploration-dominant
            "R3": {
                ("very_low", "very_early"): "very_high",
                ("very_low", "early"):      "very_high",
                ("very_low", "mid"):        "very_high",
                ("very_low", "late"):       "high",
                ("very_low", "very_late"):  "high",
                ("low", "very_early"):      "very_high",
                ("low", "early"):           "very_high",
                ("low", "mid"):             "high",
                ("low", "late"):            "high",
                ("low", "very_late"):       "medium",
                ("medium", "very_early"):   "very_high",
                ("medium", "early"):        "high",
                ("medium", "mid"):          "high",
                ("medium", "late"):         "medium",
                ("medium", "very_late"):    "medium",
                ("high", "very_early"):     "very_high",
                ("high", "early"):          "high",
                ("high", "mid"):            "high",
                ("high", "late"):           "medium",
                ("high", "very_late"):      "low",
                ("very_high", "very_early"):"high",
                ("very_high", "early"):     "high",
                ("very_high", "mid"):       "medium",
                ("very_high", "late"):      "medium",
                ("very_high", "very_late"): "low",
            },
            # R4: Diversity-reactive (progress-agnostic)
            "R4": {
                ("very_low", "very_early"): "very_low",
                ("very_low", "early"):      "very_low",
                ("very_low", "mid"):        "very_low",
                ("very_low", "late"):       "very_low",
                ("very_low", "very_late"):  "very_low",
                ("low", "very_early"):      "low",
                ("low", "early"):           "low",
                ("low", "mid"):             "low",
                ("low", "late"):            "low",
                ("low", "very_late"):       "low",
                ("medium", "very_early"):   "medium",
                ("medium", "early"):        "medium",
                ("medium", "mid"):          "medium",
                ("medium", "late"):         "medium",
                ("medium", "very_late"):    "medium",
                ("high", "very_early"):     "high",
                ("high", "early"):          "high",
                ("high", "mid"):            "high",
                ("high", "late"):           "high",
                ("high", "very_late"):      "high",
                ("very_high", "very_early"):"very_high",
                ("very_high", "early"):     "very_high",
                ("very_high", "mid"):       "very_high",
                ("very_high", "late"):      "very_high",
                ("very_high", "very_late"): "very_high",
            },
            # R5: Progress-dominant (diversity-agnostic)
            "R5": {
                ("very_low", "very_early"): "very_high",
                ("very_low", "early"):      "high",
                ("very_low", "mid"):        "medium",
                ("very_low", "late"):       "low",
                ("very_low", "very_late"):  "very_low",
                ("low", "very_early"):      "very_high",
                ("low", "early"):           "high",
                ("low", "mid"):             "medium",
                ("low", "late"):            "low",
                ("low", "very_late"):       "very_low",
                ("medium", "very_early"):   "very_high",
                ("medium", "early"):        "high",
                ("medium", "mid"):          "medium",
                ("medium", "late"):         "low",
                ("medium", "very_late"):    "very_low",
                ("high", "very_early"):     "very_high",
                ("high", "early"):          "high",
                ("high", "mid"):            "medium",
                ("high", "late"):           "low",
                ("high", "very_late"):      "very_low",
                ("very_high", "very_early"):"very_high",
                ("very_high", "early"):     "high",
                ("very_high", "mid"):       "medium",
                ("very_high", "late"):      "low",
                ("very_high", "very_late"): "very_low",
            },
            # R6: Inverse (opposite of R1)
            "R6": {
                ("very_low", "very_early"): "medium",
                ("very_low", "early"):      "medium",
                ("very_low", "mid"):        "low",
                ("very_low", "late"):       "low",
                ("very_low", "very_late"):  "very_high",
                ("low", "very_early"):      "very_low",
                ("low", "early"):           "low",
                ("low", "mid"):             "low",
                ("low", "late"):            "medium",
                ("low", "very_late"):       "high",
                ("medium", "very_early"):   "low",
                ("medium", "early"):        "low",
                ("medium", "mid"):          "medium",
                ("medium", "late"):         "high",
                ("medium", "very_late"):    "very_high",
                ("high", "very_early"):     "low",
                ("high", "early"):          "medium",
                ("high", "mid"):            "medium",
                ("high", "late"):           "high",
                ("high", "very_late"):      "very_high",
                ("very_high", "very_early"):"very_low",
                ("very_high", "early"):     "very_low",
                ("very_high", "mid"):       "high",
                ("very_high", "late"):      "very_high",
                ("very_high", "very_late"): "very_high",
            },
        }
        if rule_set not in RULE_SETS:
            raise ValueError(f"rule_set='{rule_set}' no definido. Sets disponibles: {list(RULE_SETS.keys())}")
        
        return RULE_SETS[rule_set]

    def compute_w(self, diversity_ratio, progress):
        # Reparación mínima: evitar bordes exactos (0 o 1)
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

        # Escalamiento a [0, 1]
        w = self.wMin + w_norm * (self.wMax - self.wMin)
        w = float(np.clip(w, self.wMin, self.wMax))
        self.w_history.append(w)
        return w
