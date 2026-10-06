"""
Calculation of quantum circuit and shot overhead introduced by protection.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class ProtectionOverhead:
    """
    Quantifies the exact overhead incurred by stabilizer error detection.
    """
    baseline_swaps: int
    protected_swaps: int
    additional_swaps: int

    baseline_native_cxs: int
    protected_native_cxs: int
    additional_native_cxs: int

    baseline_depth_2q: int
    protected_depth_2q: int
    additional_depth_2q: int

    baseline_total_depth: int
    protected_total_depth: int
    additional_total_depth: int

    baseline_measurements: int
    protected_measurements: int
    additional_measurements: int

    rejected_shots: int
    total_shots: int
    survival_yield: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON serializable dictionary."""
        return {
            "circuit_overhead": {
                "additional_swaps": self.additional_swaps,
                "additional_native_cxs": self.additional_native_cxs,
                "additional_depth_2q": self.additional_depth_2q,
                "additional_total_depth": self.additional_total_depth,
                "additional_measurements": self.additional_measurements,
            },
            "sampling_overhead": {
                "total_shots": self.total_shots,
                "rejected_shots": self.rejected_shots,
                "survival_yield": round(self.survival_yield, 6),
                "survival_yield_percent": round(self.survival_yield * 100.0, 2),
            },
            "absolute_metrics": {
                "baseline_swaps": self.baseline_swaps,
                "protected_swaps": self.protected_swaps,
                "baseline_native_cxs": self.baseline_native_cxs,
                "protected_native_cxs": self.protected_native_cxs,
                "baseline_depth_2q": self.baseline_depth_2q,
                "protected_depth_2q": self.protected_depth_2q,
            },
        }


def compute_protection_overhead(
    baseline_routing: Dict[str, Any],
    protected_routing: Dict[str, Any],
    rejected_shots: int,
    total_shots: int,
    survival_yield: float,
) -> ProtectionOverhead:
    """
    Compare baseline and protected routing metrics to extract exact overhead.
    """
    b_swaps = baseline_routing["swap_count"]
    p_swaps = protected_routing["swap_count"]

    b_cxs = baseline_routing["native_cx_count"]
    p_cxs = protected_routing["native_cx_count"]

    b_d2q = baseline_routing["depth_2q_native"]
    p_d2q = protected_routing["depth_2q_native"]

    b_tot_d = baseline_routing["total_depth_native"]
    p_tot_d = protected_routing["total_depth_native"]

    return ProtectionOverhead(
        baseline_swaps=b_swaps,
        protected_swaps=p_swaps,
        additional_swaps=p_swaps - b_swaps,
        baseline_native_cxs=b_cxs,
        protected_native_cxs=p_cxs,
        additional_native_cxs=p_cxs - b_cxs,
        baseline_depth_2q=b_d2q,
        protected_depth_2q=p_d2q,
        additional_depth_2q=p_d2q - b_d2q,
        baseline_total_depth=b_tot_d,
        protected_total_depth=p_tot_d,
        additional_total_depth=p_tot_d - b_tot_d,
        baseline_measurements=2,
        protected_measurements=4,
        additional_measurements=2,
        rejected_shots=rejected_shots,
        total_shots=total_shots,
        survival_yield=survival_yield,
    )
