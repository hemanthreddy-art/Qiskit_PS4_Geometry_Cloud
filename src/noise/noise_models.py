r"""
Documented Qiskit Aer Noise Models.

DISCLAIMER / SCIENTIFIC CLARIFICATION:
--------------------------------------
All noisy simulations in this module are executed on local classical simulators
using Qiskit Aer's quantum noise engine. They emulate the noise channels of
superconducting quantum hardware but DO NOT represent live execution on IBM Quantum
physical quantum processors.

PHYSICAL NOISE CHANNELS & ASSUMPTIONS:
---------------------------------------
1. Single-Qubit Depolarizing Error (p_1q):
   Single-qubit control gates (H, S†, X, SX) suffer microwave drive fluctuations,
   imperfect pulse shaping, and local frequency jitter.
   Modeled as a symmetric single-qubit depolarizing channel:
       E(rho) = (1 - p_1q) rho + (p_1q / 3) * (X rho X + Y rho Y + Z rho Z)
   Nominal default: p_1q = 0.001 (0.10% gate error rate).

2. Two-Qubit Depolarizing Error (p_2q):
   Two-qubit entangling gates (CX) require microwave cross-resonance drives
   between coupled transmons, with gate durations (~200-400 ns) roughly an order
   of magnitude longer than single-qubit gates, incurring heightened decoherence
   and parasitic ZZ crosstalk.
   Modeled as a symmetric two-qubit depolarizing channel:
       E(rho) = (1 - p_2q) rho + (p_2q / 15) * sum_{P in {I,X,Y,Z}^2 \\ {II}} P rho P
   Nominal default: p_2q = 0.015 (1.50% gate error rate).

3. Measurement / Readout Assignment Error (p_ro):
   State discrimination via dispersive readout cavity transmission measurements
   suffers from state classification errors (P(0|1) and P(1|0)) due to thermal
   excitations and resonator ring-up time.
   Modeled via a classical readout error matrix:
       [[1 - p_ro, p_ro],
        [p_ro,     1 - p_ro]]
   Nominal default: p_ro = 0.015 (1.50% readout error rate).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from qiskit_aer.noise import NoiseModel, depolarizing_error, ReadoutError


@dataclass
class NoiseConfiguration:
    """
    Configuration parameters for parameterized superconducting quantum noise.
    """
    model_name: str = "superconducting_baseline_transmon"
    p_1q: float = 0.001          # 0.10% single-qubit depolarizing error
    p_2q: float = 0.015          # 1.50% two-qubit depolarizing error
    p_readout: float = 0.015     # 1.50% readout assignment error
    single_qubit_gates: List[str] = field(default_factory=lambda: ["h", "sdg", "sx", "x", "rz"])
    two_qubit_gates: List[str] = field(default_factory=lambda: ["cx", "swap"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert noise configuration to a documented dictionary."""
        return {
            "model_name": self.model_name,
            "hardware_type": "SIMULATED_AER_NOISE (Not physical IBM processor)",
            "single_qubit_error_rate_p1q": self.p_1q,
            "two_qubit_error_rate_p2q": self.p_2q,
            "readout_error_rate_pro": self.p_readout,
            "single_qubit_target_gates": self.single_qubit_gates,
            "two_qubit_target_gates": self.two_qubit_gates,
            "physical_assumptions": (
                "Symmetric depolarizing channel for 1Q and 2Q gates; "
                "symmetric bit-flip readout assignment error on all physical qubits."
            )
        }


def build_depolarizing_noise_model(config: Optional[NoiseConfiguration] = None) -> NoiseModel:
    """
    Construct a documented Qiskit Aer NoiseModel based on the specified parameters.

    Parameters:
        config: NoiseConfiguration instance (defaults to baseline superconducting transmon).

    Returns:
        NoiseModel: Configured Qiskit Aer noise model.
    """
    if config is None:
        config = NoiseConfiguration()

    noise_model = NoiseModel()

    # 1. Add single-qubit depolarizing errors
    if config.p_1q > 0:
        error_1q = depolarizing_error(config.p_1q, 1)
        noise_model.add_all_qubit_quantum_error(error_1q, config.single_qubit_gates)

    # 2. Add two-qubit depolarizing errors
    if config.p_2q > 0:
        error_2q = depolarizing_error(config.p_2q, 2)
        noise_model.add_all_qubit_quantum_error(error_2q, config.two_qubit_gates)

    # 3. Add readout assignment errors
    if config.p_readout > 0:
        p_ro = config.p_readout
        readout_matrix = [
            [1.0 - p_ro, p_ro],
            [p_ro, 1.0 - p_ro],
        ]
        ro_error = ReadoutError(readout_matrix)
        noise_model.add_all_qubit_readout_error(ro_error)

    return noise_model


def build_fake_yorktown_noise_model() -> NoiseModel:
    """
    Construct a noise model calibrated directly from historical IBM Yorktown calibration data
    using FakeYorktownV2.

    Returns:
        NoiseModel: Noise model derived from FakeYorktownV2.
    """
    from qiskit_ibm_runtime.fake_provider import FakeYorktownV2
    fake_backend = FakeYorktownV2()
    noise_model = NoiseModel.from_backend(fake_backend)
    return noise_model
