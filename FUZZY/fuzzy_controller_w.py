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
    """

    def __init__(self, w_set, wMin=0.0, wMax=1.0, n_grid=501):
        self.wMin = float(wMin)
        self.wMax = float(wMax)
        self.w_set = str(w_set).upper()
        self.n_grid = int(n_grid)
        self.w_history = [self.wMax]  # Valor inicial: exploración máxima en iter=0


        # Universo de salida normalizado [0,1]
        self.y = np.linspace(0.0, 1.0, self.n_grid)

        # Entradas: triangulares estrictas (sin hombros)
        self.div_mf = {
            "low":    (0.0, 0.2, 0.4),
            "medium": (0.3, 0.5, 0.7),
            "high":   (0.6, 0.8, 1.0),
        }
        self.it_mf = {
            "early":  (0.0, 0.2, 0.4),
            "mid":    (0.3, 0.5, 0.7),
            "late":   (0.6, 0.8, 1.0),
        }

        # Salida w (set A estricta; set B con hombro)
        self.w_mf = self._build_w_mfs(self.w_set)

        # Reglas 3x3 completas. OJO FUNCIONA EL SISTEMA SOLO CON REGLAS DE 3 (mas adelante incluir 5 o 7)
        # Diversity, Iteration Rate y el valor de w
        self.rules = {
            ("low",    "early"): "high",
            ("medium", "early"): "high",
            ("high",   "early"): "high",

            ("low",    "mid"):   "low",
            ("medium", "mid"):   "medium",
            ("high",   "mid"):   "high",

            ("low",    "late"):  "low",
            ("medium", "late"):  "low",
            ("high",   "late"):  "medium",
        }

    def _build_w_mfs(self, w_set):
        W_SETS ={
            "A": {
                "high":   (0.50, 0.75, 1.0),  # 
                "medium": (0.25, 0.5, 0.75),  # 
                "low":    (0.00, 0.25, 0.50),  #  
            },
            "B": {
                "high":   (0.50, 0.75, 0.75),  # 
                "medium": (0.25, 0.5, 0.75),  # 
                "low":    (0.25, 0.25, 0.50),  # 
            },
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


def get_fuzzy_controller(w_set, num_labels=3):
    """
    Factory function para obtener el controller fuzzy apropiado.
    
    Args:
        w_set: 'A', 'B', 'C', o 'D'
        num_labels: 3 o 5 (etiquetas lingüísticas)
    
    Returns:
        FuzzyInertiaController (3 labels) o FuzzyInertiaController_5labels (5 labels)
    """
    if num_labels == 3:
        return FuzzyInertiaController(w_set)
    elif num_labels == 5:
        from FUZZY.fuzzy_controller_w_5labels import FuzzyInertiaController_5labels
        return FuzzyInertiaController_5labels(w_set)
    else:
        raise ValueError(f"num_labels={num_labels} no soportado. Usa 3 o 5.")
