"""CEC 2017 functions and their AFCS problem adapter."""

from .functions import all_functions
from .problem import (
    CEC2017_DEPRECATED_FUNCTIONS,
    CEC2017_SUPPORTED_DIMENSIONS,
    CEC2017Problem,
    get_function,
)

__all__ = [
    "CEC2017_DEPRECATED_FUNCTIONS",
    "CEC2017_SUPPORTED_DIMENSIONS",
    "CEC2017Problem",
    "all_functions",
    "get_function",
]

