"""FIS Mamdani parametrico para PSO_FCS.

Todo se genera algorithmically desde config/fuzzy_partitions.json:
  - Particiones I/O: make_partition_uniform(n_labels, overlap, shoulders)
  - Reglas R1..R8: make_rule_matrix(pattern, n_labels) via modelo aditivo

No hay tripletes (a,b,c) hardcoded en codigo ni en JSON. El JSON solo declara
el scheme y sus parametros (overlap, shoulders, labels).
"""
import json
import math
import os
from functools import lru_cache

import numpy as np


# ---------------------------------------------------------------------------
# Triangular membership con soporte para hombros (a=b o b=c)
# ---------------------------------------------------------------------------
def tri(x, a, b, c):
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


# ---------------------------------------------------------------------------
# Carga de configuracion
# ---------------------------------------------------------------------------
_DEFAULT_PARTITIONS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config",
    "fuzzy_partitions.json",
)


@lru_cache(maxsize=1)
def _load_partitions(path=_DEFAULT_PARTITIONS_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Generadores parametricos de particiones
# ---------------------------------------------------------------------------
def make_partition_uniform(n, overlap=1.0, shoulders=False):
    """Genera n MFs triangulares en [0,1]. La posicion de los centros depende de 'shoulders':

    Caso A) shoulders=True (recomendado para OUTPUTS que deben saturar a 0 y 1):
      - Centros equiespaciados INCLUYENDO los bordes: c_i = i/(n-1)
      - distancia entre centros: d = 1/(n-1)
      - brazo: r = (d/2) * (1 + overlap)
      - MF[0] tiene a=b=0 (hombro izq), MF[n-1] tiene b=c=1 (hombro der)
      - Cobertura Ruspini Sum mu = 1 en TODO [0,1] cuando overlap=1

    Caso B) shoulders=False (recomendado para INPUTS, MFs visualmente completas):
      - Centros DESPLAZADOS al interior: c_i = s*(i+1), con s = 1/(n+overlap)
      - Brazo: r = (s/2)*(1+overlap) = s   (cuando overlap=1)
      - MF[0] = (0, s, 2s),  MF[n-1] = (1-2s, 1-s, 1)
      - Cobertura Ruspini Sum mu = 1 en [c_0, c_{n-1}]; en los bordes [0,c_0) y (c_{n-1},1]
        la suma decae a 0 (zona con solo 1 MF activa, no Ruspini)

    Parametros:
      n         : numero de etiquetas (>=2)
      overlap   : p in [0,inf) controla el brazo: r = (espacio/2)*(1+p)
      shoulders : bool - True para esquema con hombros, False para esquema con MFs internas

    Retorna: lista de tuplas (a, b, c), una por etiqueta, indexada 0..n-1.
    """
    if n < 2:
        raise ValueError("n must be >= 2")
    if overlap < 0:
        raise ValueError("overlap must be >= 0")

    if shoulders:
        d = 1.0 / (n - 1)
        half_arm = (d / 2.0) * (1.0 + overlap)
        mfs = []
        for i in range(n):
            c = i * d
            a = c - half_arm
            cc = c + half_arm
            if i == 0:
                a = c
            if i == n - 1:
                cc = c
            a = max(0.0, min(1.0, a))
            cc = max(0.0, min(1.0, cc))
            mfs.append((float(a), float(c), float(cc)))
        return mfs

    # shoulders == False : centros desplazados al interior
    s = 1.0 / (n + overlap)
    half_arm = (s / 2.0) * (1.0 + overlap)
    mfs = []
    for i in range(n):
        c = s + i * s  # c_0 = s, c_{n-1} = n*s = 1 - overlap*s
        # Cuando overlap=1: c_0 = 1/(n+1), c_{n-1} = n/(n+1)
        a = c - half_arm
        cc = c + half_arm
        a = max(0.0, min(1.0, a))
        cc = max(0.0, min(1.0, cc))
        mfs.append((float(a), float(c), float(cc)))
    return mfs


# ---------------------------------------------------------------------------
# Modelo aditivo de reglas R1..R8
# ---------------------------------------------------------------------------
_PROG_EFFECT = {
    "decreasing": lambda p, c: c - p,
    "increasing": lambda p, c: p - c,
    "agnostic":   lambda p, c: 0,
}

_DIV_EFFECT = {
    "following":    lambda d, c: d - c,
    "compensating": lambda d, c: c - d,
    "agnostic":     lambda d, c: 0,
}


def _output_idx_additive(s, n):
    """Mapping aditivo: bandas de 2 con banda central de tamano 1.
    Aplica cuando ambos efectos son no-agnostic (R5..R8)."""
    center = (n - 1) // 2
    if s > 0:
        return min(center + math.ceil(s / 2.0), n - 1)
    if s < 0:
        return max(center - math.ceil((-s) / 2.0), 0)
    return center


def make_rule_matrix(pattern_key, n_labels, partitions_path=_DEFAULT_PARTITIONS_PATH):
    """Genera dict {(div_label, it_label): out_label} para R1..R8 en n_labels arbitrario.

    Dos regimenes:
      * R1..R4 (un solo efecto activo): out_idx = center + effect  (identidad escalada)
      * R5..R8 (ambos efectos activos): out_idx = _output_idx_additive(prog+div, n)
    """
    cfg = _load_partitions(partitions_path)
    pat = cfg["rule_patterns"][pattern_key]
    prog_fn = _PROG_EFFECT[pat["prog"]]
    div_fn = _DIV_EFFECT[pat["div"]]
    prog_agn = pat["prog"] == "agnostic"
    div_agn = pat["div"] == "agnostic"
    center = (n_labels - 1) // 2

    div_labels = cfg["partitions"]["I1"]["labels_by_n"][str(n_labels)]
    it_labels = div_labels
    out_labels = cfg["partitions"]["O1"]["labels_by_n"][str(n_labels)]

    rules = {}
    for d_idx, d_lab in enumerate(div_labels):
        for p_idx, p_lab in enumerate(it_labels):
            p_eff = prog_fn(p_idx, center)
            d_eff = div_fn(d_idx, center)
            if prog_agn and not div_agn:
                out_idx = max(0, min(n_labels - 1, center + d_eff))
            elif div_agn and not prog_agn:
                out_idx = max(0, min(n_labels - 1, center + p_eff))
            else:
                out_idx = _output_idx_additive(p_eff + d_eff, n_labels)
            rules[(d_lab, p_lab)] = out_labels[int(out_idx)]
    return rules


# ---------------------------------------------------------------------------
# Controlador Mamdani parametrico
# ---------------------------------------------------------------------------
class FuzzyInertiaController_Auto:
    """FIS Mamdani generico parametrizado por config/fuzzy_partitions.json.

    Inputs: diversity_ratio, progress in [0,1]
    Output: w in [wMin, wMax]
    Inferencia: fuzzificacion triangular -> Mamdani (min) -> agregacion (max)
                -> defuzzificacion centroide -> rescalado [c_min, c_max] -> [wMin, wMax]
    """

    def __init__(self, w_set, num_labels=3, input_set="I1", rule_set="R1",
                 wMin=0.0, wMax=1.0, n_grid=501, partitions_path=_DEFAULT_PARTITIONS_PATH):
        self.wMin = float(wMin)
        self.wMax = float(wMax)
        self.w_set = str(w_set).upper()
        self.input_set = str(input_set).upper()
        self.rule_set = str(rule_set).upper()
        self.num_labels = int(num_labels)
        self.n_grid = int(n_grid)
        self.w_history = [self.wMax]

        cfg = _load_partitions(partitions_path)
        in_cfg = cfg["partitions"][self.input_set]
        out_cfg = cfg["partitions"][self.w_set]

        n_key = str(self.num_labels)
        div_labels = in_cfg["labels_by_n"][n_key]
        it_labels = div_labels
        out_labels = out_cfg["labels_by_n"][n_key]

        in_abc = make_partition_uniform(
            self.num_labels,
            overlap=float(in_cfg["overlap"]),
            shoulders=bool(in_cfg["shoulders"]),
        )
        out_abc = make_partition_uniform(
            self.num_labels,
            overlap=float(out_cfg["overlap"]),
            shoulders=bool(out_cfg["shoulders"]),
        )

        self.div_mf = {lab: abc for lab, abc in zip(div_labels, in_abc)}
        self.it_mf = {lab: abc for lab, abc in zip(it_labels, in_abc)}
        self.w_mf = {lab: abc for lab, abc in zip(out_labels, out_abc)}

        self.y = np.linspace(0.0, 1.0, self.n_grid)
        self._w_norm_min, self._w_norm_max = self._compute_centroid_bounds()

        self.rules = make_rule_matrix(self.rule_set, self.num_labels, partitions_path)

    def _compute_centroid_bounds(self):
        centroids = []
        for (a, b, c) in self.w_mf.values():
            mf_vals = np.array([tri(val, a, b, c) for val in self.y], dtype=float)
            den = np.trapz(mf_vals, self.y)
            if den > 1e-12:
                centroids.append(np.trapz(self.y * mf_vals, self.y) / den)
        if not centroids:
            return 0.0, 1.0
        return min(centroids), max(centroids)

    def compute_w(self, diversity_ratio, progress):
        eps = 1e-12
        d = float(np.clip(diversity_ratio, eps, 1.0 - eps))
        t = float(np.clip(progress, eps, 1.0 - eps))

        mu_d = {k: tri(d, *abc) for k, abc in self.div_mf.items()}
        mu_t = {k: tri(t, *abc) for k, abc in self.it_mf.items()}

        agg = np.zeros_like(self.y, dtype=float)
        for (d_lab, t_lab), out_lab in self.rules.items():
            firing = min(mu_d[d_lab], mu_t[t_lab])
            if firing <= 0.0:
                continue
            a, b, c = self.w_mf[out_lab]
            mf_out = np.array([tri(val, a, b, c) for val in self.y], dtype=float)
            agg = np.maximum(agg, np.minimum(firing, mf_out))

        den = np.trapz(agg, self.y)
        if den <= 1e-12:
            w_norm = 0.5
        else:
            w_norm = np.trapz(self.y * agg, self.y) / den

        span = self._w_norm_max - self._w_norm_min
        if span > 1e-12:
            w_norm = (w_norm - self._w_norm_min) / span
        w_norm = float(np.clip(w_norm, 0.0, 1.0))

        w = self.wMin + w_norm * (self.wMax - self.wMin)
        w = float(np.clip(w, self.wMin, self.wMax))
        self.w_history.append(w)
        return w
