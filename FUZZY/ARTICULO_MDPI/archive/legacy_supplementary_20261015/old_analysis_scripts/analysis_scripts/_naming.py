"""Shared naming conventions for the MDPI manuscript artefacts.

Decision D17: a configuration is reported as FCS-<n>-R<k> in the body of the paper.
The long identifiers (PSO_FCS:G3:I1:R1:O1) stay in the raw data artefacts only.
The input and output partition families are I1 and O1 for every configuration,
so they carry no information in the label.

Landscape classes follow the experimental design; the internal key "composed"
is rendered as "fixed-dimensional" to avoid a fourth name for the same class.
"""
from __future__ import annotations

import re

_CONFIG_RE = re.compile(r"G(\d+).*?:(R\d+)")


def short_name(mh_raw: str) -> str:
    """PSO_FCS:G3:I1:R1:O1 -> FCS-3-R1. The baseline stays PSO."""
    if not isinstance(mh_raw, str) or mh_raw == "PSO":
        return "PSO"
    m = _CONFIG_RE.search(mh_raw)
    return f"FCS-{m.group(1)}-{m.group(2)}" if m else mh_raw


CLASS_LABEL = {
    "unimodal": "Unimodal (F1-F7)",
    "multimodal": "Scalable multimodal (F8-F13)",
    "composed": "Fixed-dimensional (F14-F23)",
}

CLASS_SHORT = {
    "unimodal": "Unimodal",
    "multimodal": "Scalable multimodal",
    "composed": "Fixed-dimensional",
}

SUBSET_LABEL = {
    "S1": "S1: scalable functions (F1-F13)",
    "S2": "S2: fixed-dimensional functions (F14-F23)",
}
