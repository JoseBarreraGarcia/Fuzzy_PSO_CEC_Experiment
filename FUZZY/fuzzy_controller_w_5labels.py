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
    """

    def __init__(self, w_set, n_grid=501):
        self.wMin = 0.0
        self.wMax = 1.0
        self.w_set = str(w_set).upper()
        self.n_grid = int(n_grid)
        self.w_history = [self.wMax]  # Valor inicial: exploración máxima en iter=0

        # Universo de salida normalizado [0,1]
        self.y = np.linspace(0.0, 1.0, self.n_grid)

        # Entradas: 5 etiquetas triangulares distribuidas uniformemente
        self.div_mf = {
            "very_low": (0.0, 0.15, 0.30),
            "low":      (0.2, 0.35, 0.5),
            "medium":   (0.35, 0.5, 0.65),
            "high":     (0.5, 0.65, 0.80),
            "very_high":(0.7, 0.85, 1.0),
        }
        self.it_mf = {
            "very_early": (0.0, 0.15, 0.30),
            "early":      (0.2, 0.35, 0.5),
            "mid":        (0.35, 0.5, 0.65),
            "late":       (0.5, 0.65, 0.80),
            "very_late":  (0.7, 0.85, 1.0),
        }

        # Salida w (sets A, B, C, D con 5 etiquetas)
        self.w_mf = self._build_w_mfs(self.w_set)

        # Reglas 5x5 (25 reglas). Lógica: más diversidad/temprano → más exploración
        self.rules = self._build_rules_5x5()

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

    def _build_rules_5x5(self):
        """
        Construye matriz 5×5 de reglas Mamdani.
        
        Lógica:
        - Diversidad BAJA + iteración TEMPRANA → exploración (very_high)
        - Diversidad BAJA + iteración TARDÍA → explotación (very_low)
        - Diversidad ALTA + cualquier iteración → exploración (high/very_high)
        - Diversidad MEDIA → transición gradual
        """
        rules = {
            # Diversidad: very_low (población casi estancada, peligro)
            ("very_low", "very_early"): "very_high",  # Urgencia: explosión
            ("very_low", "early"):      "very_high",
            ("very_low", "mid"):        "high",        # Intentar escape
            ("very_low", "late"):       "high",      # Tarde para escape
            ("very_low", "very_late"):  "medium",         # 

            # Diversidad: low (población baja)
            ("low", "very_early"): "very_high",
            ("low", "early"):      "high",
            ("low", "mid"):        "high",
            ("low", "late"):       "medium",
            ("low", "very_late"):  "low",

            # Diversidad: medium (balanceado)
            ("medium", "very_early"): "high",
            ("medium", "early"):      "high",
            ("medium", "mid"):        "medium",
            ("medium", "late"):       "low",
            ("medium", "very_late"):  "very_low",

            # Diversidad: high (buena exploración)
            ("high", "very_early"): "high",
            ("high", "early"):      "medium",
            ("high", "mid"):        "medium",
            ("high", "late"):       "low",
            ("high", "very_late"):  "very_low",

            # Diversidad: very_high (excelente exploración)
            ("very_high", "very_early"): "medium",
            ("very_high", "early"):      "medium",
            ("very_high", "mid"):        "low",
            ("very_high", "late"):       "very_low",
            ("very_high", "very_late"):  "very_low",
        }
        return rules

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
