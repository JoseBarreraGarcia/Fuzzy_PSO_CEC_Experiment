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


class FuzzyInertiaController:
    """
    Mamdani FIS:
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
            "I2": {
                "div": {
                    "low":    (0.0, 0.16, 0.33),
                    "medium": (0.33, 0.5, 0.66),
                    "high":   (0.66, 0.84, 1.0),
                },
                "it": {
                    "early":  (0.0, 0.16, 0.33),
                    "mid":    (0.33, 0.5, 0.66),
                    "late":   (0.66, 0.84, 1.0),
                },
            },
            # I3: Wide/Amplio - máximo solapamiento, mezcla más gradual
            "I3": {
                "div": {
                    "low":    (0.0, 0.25, 0.5),
                    "medium": (0.25, 0.5, 0.75),
                    "high":   (0.5, 0.75, 1.0),
                },
                "it": {
                    "early":  (0.0, 0.25, 0.5),
                    "mid":    (0.25, 0.5, 0.75),
                    "late":   (0.5, 0.75, 1.0),
                },
            },
            # I4: Shoulder/Hombro - funciones trapezoidales en los extremos
            "I4": {
                "div": {
                    "low":    (0.0, 0.0, 0.35),    # hombro izquierdo
                    "medium": (0.2, 0.5, 0.8),
                    "high":   (0.65, 1.0, 1.0),    # hombro derecho
                },
                "it": {
                    "early":  (0.0, 0.0, 0.35),    # hombro izquierdo
                    "mid":    (0.2, 0.5, 0.8),
                    "late":   (0.65, 1.0, 1.0),    # hombro derecho
                },
            },
        }
        if input_set not in INPUT_SETS:
            raise ValueError(f"input_set='{input_set}' no definido. Sets disponibles: {list(INPUT_SETS.keys())}")
        
        return INPUT_SETS[input_set]["div"], INPUT_SETS[input_set]["it"]

    def _build_w_mfs(self, w_set):
        W_SETS ={
            "A": {
                "high":   (0.50, 0.75, 1.0),  # 
                "medium": (0.25, 0.5, 0.75),  # 
                "low":    (0.00, 0.25, 0.50),  #  
            },
            #"B": {
            #    "high":   (0.50, 0.75, 0.75),  # 
            #    "medium": (0.25, 0.5, 0.75),  # 
            #    "low":    (0.25, 0.25, 0.50),  # 
            #},
            #"C": {
            #    "high":   (0.60, 0.75, 0.90),  # 
            #    "medium": (0.35, 0.5, 0.65),  # 
            #    "low":    (0.10, 0.25, 0.40),  #     
            #},
            #"D": {
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
        WEA2026: 6 variantes de bases de reglas 3×3 (9 reglas cada una).
        Rows = diversity (low, medium, high), Columns = progress (early, mid, late).
        
        R1: Baseline - explore early, exploit late, diversity-reactive
        R2: Exploitation-dominant - aggressive low w bias
        R3: Exploration-dominant - aggressive high w bias
        R4: Diversity-reactive - w depends ONLY on diversity (progress-agnostic)
        R5: Progress-dominant - w depends ONLY on progress (diversity-agnostic)
        R6: Inverse - opposite of R1 (exploit early, explore late)
        """
        RULE_SETS = {
            # R1: Baseline (current system from OLA2026/CLEI2026)
            "R1": {
                ("low",    "early"): "high",
                ("medium", "early"): "high",
                ("high",   "early"): "high",
                ("low",    "mid"):   "low",
                ("medium", "mid"):   "medium",
                ("high",   "mid"):   "high",
                ("low",    "late"):  "low",
                ("medium", "late"):  "low",
                ("high",   "late"):  "medium",
            },
            # R2: Exploitation-dominant
            "R2": {
                ("low",    "early"): "medium",
                ("medium", "early"): "medium",
                ("high",   "early"): "high",
                ("low",    "mid"):   "low",
                ("medium", "mid"):   "low",
                ("high",   "mid"):   "medium",
                ("low",    "late"):  "low",
                ("medium", "late"):  "low",
                ("high",   "late"):  "low",
            },
            # R3: Exploration-dominant
            "R3": {
                ("low",    "early"): "high",
                ("medium", "early"): "high",
                ("high",   "early"): "high",
                ("low",    "mid"):   "high",
                ("medium", "mid"):   "high",
                ("high",   "mid"):   "high",
                ("low",    "late"):  "medium",
                ("medium", "late"):  "high",
                ("high",   "late"):  "high",
            },
            # R4: Diversity-reactive (progress-agnostic)
            "R4": {
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
            # R5: Progress-dominant (diversity-agnostic)
            "R5": {
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
            # R6: Inverse (opposite of R1)
            "R6": {
                ("low",    "early"): "low",
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

        # Escalamiento a [wMin, wMax]
        w = self.wMin + w_norm * (self.wMax - self.wMin)
        w = float(np.clip(w, self.wMin, self.wMax))
        self.w_history.append(w)
        return w


def get_fuzzy_controller(w_set, num_labels=3, input_set="I1", rule_set="R1"):
    """
    Factory function para obtener el controller fuzzy apropiado.
    
    Args:
        w_set: 'A', 'B' (configuración de MFs de salida)
        num_labels: 3 o 5 (etiquetas lingüísticas)
        input_set: 'I1', 'I2', 'I3', 'I4' (configuración de MFs de entrada, CLEI2026)
        rule_set: 'R1'-'R6' (base de reglas, WEA2026)
    
    Returns:
        FuzzyInertiaController (3 labels) o FuzzyInertiaController_5labels (5 labels)
    """
    if num_labels == 3:
        return FuzzyInertiaController(w_set, input_set=input_set, rule_set=rule_set)
    elif num_labels == 5:
        from FUZZY.fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
        return FuzzyInertiaController_5labels(w_set, input_set=input_set, rule_set=rule_set)
    else:
        raise ValueError(f"num_labels={num_labels} no soportado. Usa 3 o 5.")
