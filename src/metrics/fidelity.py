"""
Bell State Fidelity via Pauli Correlation Expectation Values.

Theory:
For the Bell state |Phi+> = (|00> + |11>) / sqrt(2), the density matrix can be expanded
in the 2-qubit Pauli operator basis as:
    rho_{Phi+} = (1/4) * (I (x) I + X (x) X - Y (x) Y + Z (x) Z)

For an arbitrary 2-qubit state rho (ideal or noisy), its fidelity with |Phi+> is:
    F(Phi+) = <Phi+| rho |Phi+> = Tr(rho_{Phi+} * rho)
            = (1 + <XX> - <YY> + <ZZ>) / 4

where:
    <XX> = Tr((X (x) X) * rho)
    <YY> = Tr((Y (x) Y) * rho)
    <ZZ> = Tr((Z (x) Z) * rho)

For each observable O in {XX, YY, ZZ}, the measurement outcomes are mapped to eigenvalues:
    Outcome '00' -> (+1)*(+1) = +1
    Outcome '11' -> (-1)*(-1) = +1
    Outcome '01' -> (+1)*(-1) = -1
    Outcome '10' -> (-1)*(+1) = -1

Expectation value:
    <O> = (N_00 + N_11 - N_01 - N_10) / N_total

Standard error (shot noise):
    sigma_<O> = sqrt((1 - <O>^2) / N_total)
    sigma_F   = (1/4) * sqrt(sigma_XX^2 + sigma_YY^2 + sigma_ZZ^2)
"""

import math
from dataclasses import dataclass
from typing import Dict, Tuple, Any


@dataclass
class PauliMeasurementSummary:
    """
    Holds expectation values, shot counts, and calculated Bell fidelity.
    """
    shots: int
    counts_xx: Dict[str, int]
    counts_yy: Dict[str, int]
    counts_zz: Dict[str, int]
    exp_xx: float
    exp_yy: float
    exp_zz: float
    fidelity: float
    std_err_xx: float
    std_err_yy: float
    std_err_zz: float
    std_err_fidelity: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON reporting."""
        return {
            "shots": self.shots,
            "counts": {
                "XX": self.counts_xx,
                "YY": self.counts_yy,
                "ZZ": self.counts_zz,
            },
            "expectations": {
                "XX": round(self.exp_xx, 6),
                "YY": round(self.exp_yy, 6),
                "ZZ": round(self.exp_zz, 6),
            },
            "fidelity": round(self.fidelity, 6),
            "uncertainties": {
                "sigma_XX": round(self.std_err_xx, 6),
                "sigma_YY": round(self.std_err_yy, 6),
                "sigma_ZZ": round(self.std_err_zz, 6),
                "sigma_fidelity": round(self.std_err_fidelity, 6),
            },
        }


def compute_pauli_expectation(counts: Dict[str, int], total_shots: int) -> Tuple[float, float]:
    """
    Compute expectation value and standard error for a 2-qubit Pauli correlation
    from measurement bitstring counts.

    Parameters:
        counts: Dictionary of bitstrings and their occurrence counts.
                Bitstrings can be formatted with or without spaces (e.g. '00', '0 1').
        total_shots: Total shots executed.

    Returns:
        Tuple[float, float]: (expectation_value, standard_error)
    """
    if total_shots <= 0:
        raise ValueError(f"total_shots must be positive, got {total_shots}")

    weighted_sum = 0
    shots_counted = 0

    for bitstring, count in counts.items():
        # Remove whitespace or register separators
        clean_bits = bitstring.replace(" ", "")
        if len(clean_bits) < 2:
            raise ValueError(f"Expected at least 2 bits in measurement outcome, got '{bitstring}'")

        # Two measured bits:
        # In Qiskit, index -1 is bit 0, index -2 is bit 1
        b0 = int(clean_bits[-1])
        b1 = int(clean_bits[-2])

        # Eigenvalue is +1 if even parity (b0 == b1), -1 if odd parity (b0 != b1)
        eigenvalue = 1 if (b0 == b1) else -1
        weighted_sum += eigenvalue * count
        shots_counted += count

    effective_shots = shots_counted if shots_counted > 0 else total_shots
    exp_val = weighted_sum / effective_shots

    # Clamp expectation value to theoretical range [-1, 1] against numerical rounding
    exp_val = max(-1.0, min(1.0, exp_val))

    # Binomial / multinomial shot noise standard error
    variance = max(0.0, 1.0 - (exp_val ** 2))
    std_err = math.sqrt(variance / effective_shots)

    return exp_val, std_err


def compute_bell_fidelity(
    exp_xx: float,
    exp_yy: float,
    exp_zz: float,
    std_err_xx: float = 0.0,
    std_err_yy: float = 0.0,
    std_err_zz: float = 0.0,
) -> Tuple[float, float]:
    """
    Compute Bell state fidelity F(Phi+) = (1 + <XX> - <YY> + <ZZ>) / 4.

    Parameters:
        exp_xx: Expectation value <XX>
        exp_yy: Expectation value <YY>
        exp_zz: Expectation value <ZZ>
        std_err_xx: Standard error of <XX>
        std_err_yy: Standard error of <YY>
        std_err_zz: Standard error of <ZZ>

    Returns:
        Tuple[float, float]: (fidelity, std_err_fidelity)
    """
    # Strict implementation of formula: F = (1 + <XX> - <YY> + <ZZ>) / 4
    raw_fidelity = (1.0 + exp_xx - exp_yy + exp_zz) / 4.0

    # Physical clamping: 0.0 <= F <= 1.0
    fidelity = max(0.0, min(1.0, raw_fidelity))

    # Error propagation in quadrature
    variance_fid = (std_err_xx**2 + std_err_yy**2 + std_err_zz**2) / 16.0
    std_err_fid = math.sqrt(variance_fid)

    return fidelity, std_err_fid
