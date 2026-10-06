"""
Protection module for stabilizer-based error detection and post-selection.
"""

from .stabilizer_check import (
    build_protected_bell_circuit,
    classify_and_postselect_counts,
    ProtectedMeasurementSummary,
)
from .overhead import compute_protection_overhead, ProtectionOverhead

__all__ = [
    "build_protected_bell_circuit",
    "classify_and_postselect_counts",
    "ProtectedMeasurementSummary",
    "compute_protection_overhead",
    "ProtectionOverhead",
]
