r"""
Stabilizer-based Error Detection and Post-Selection for Bell States.

SCIENTIFIC SCOPE & TERMINOLOGY DISTINCTION:
------------------------------------------
This module implements STABILIZER-BASED QUANTUM ERROR DETECTION WITH POST-SELECTION.
It is explicitly NOT a full, fault-tolerant quantum error correction (QEC) protocol.
In full QEC, syndrome measurement is followed by active recovery operations that restore
the corrupted state without discarding experimental runs. In this protocol, errors are
DETECTED via stabilizer syndrome measurement, and corrupted runs are POST-SELECTED OUT
(discarded), yielding an error-suppressed sub-population at the cost of experimental yield.

MATHEMATICAL BASIS:
-------------------
The maximally entangled Bell state |Phi+> = (|00> + |11>) / sqrt(2) is the unique +1 eigenstate
of the commuting 2-qubit stabilizer group S = <S_ZZ, S_XX>:
    S_ZZ = Z (x) Z = +1
    S_XX = X (x) X = +1
    (S_YY = -Y (x) Y = -1, since S_YY = -(S_ZZ * S_XX) * (-1) = +1 in projective representation)

ERROR DETECTION MECHANISM:
--------------------------
1. ZZ Parity Check (Bit-Flip / X-Error Detection):
   Ancilla a_ZZ initialized in |0>.
   CX(data_0, a_ZZ), CX(data_1, a_ZZ).
   Measuring a_ZZ:
     - Outcome 0 -> ZZ = +1 eigenstate (even parity, NO bit-flip).
     - Outcome 1 -> ZZ = -1 eigenstate (odd parity, bit-flip X on either data qubit DETECTED).

2. XX Parity Check (Phase-Flip / Z-Error Detection):
   Ancilla a_XX initialized in |+> (via H).
   CX(a_XX, data_0), CX(a_XX, data_1), followed by H(a_XX).
   Measuring a_XX:
     - Outcome 0 -> XX = +1 eigenstate (NO phase-flip).
     - Outcome 1 -> XX = -1 eigenstate (phase-flip Z on either data qubit DETECTED).

Combined Syndrome:
A shot is ACCEPTED if and only if syndrome = (0, 0).
Any single-qubit Pauli error (X, Y = iXZ, or Z) on either data qubit produces a non-trivial
syndrome bit (1) and is successfully discarded during post-selection.
"""

from dataclasses import dataclass
from typing import Dict, Tuple, Any
from qiskit import QuantumCircuit, ClassicalRegister


@dataclass
class ProtectedMeasurementSummary:
    """
    Holds measurement metrics for a protected post-selected experiment.
    """
    total_shots: int
    accepted_shots: int
    rejected_shots: int
    survival_yield: float
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
        """Convert to JSON serializable dictionary."""
        return {
            "total_shots": self.total_shots,
            "accepted_shots": self.accepted_shots,
            "rejected_shots": self.rejected_shots,
            "survival_yield": round(self.survival_yield, 6),
            "survival_yield_percent": round(self.survival_yield * 100.0, 2),
            "accepted_counts": {
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


def build_protected_bell_circuit(basis: str = "ZZ") -> QuantumCircuit:
    """
    Construct a 4-qubit circuit for protected Bell-state preparation,
    syndrome extraction (ZZ and XX parity checks), and basis measurement.

    Register Layout:
        Qubit 0: Data qubit 0
        Qubit 1: Data qubit 1
        Qubit 2: Syndrome ancilla for ZZ parity check
        Qubit 3: Syndrome ancilla for XX parity check

        Clbit 0: ZZ syndrome measurement outcome
        Clbit 1: XX syndrome measurement outcome
        Clbit 2: Data qubit 0 measurement outcome
        Clbit 3: Data qubit 1 measurement outcome

    Parameters:
        basis: Tomography observable ('XX', 'YY', 'ZZ').

    Returns:
        QuantumCircuit: 4-qubit, 4-clbit circuit.
    """
    basis_str = basis.upper()
    if basis_str not in {"XX", "YY", "ZZ"}:
        raise ValueError(f"Invalid basis '{basis}'. Must be 'XX', 'YY', or 'ZZ'.")

    qc = QuantumCircuit(4, 4, name=f"protected_bell_{basis_str.lower()}")

    # 1. Prepare target Bell state |Phi+> on data qubits 0 and 1
    qc.h(0)
    qc.cx(0, 1)

    # 2. Stabilizer ZZ parity check on ancilla qubit 2
    qc.cx(0, 2)
    qc.cx(1, 2)
    qc.measure(2, 0)  # Classical bit 0 = ZZ syndrome

    # 3. Stabilizer XX parity check on ancilla qubit 3
    qc.h(3)
    qc.cx(3, 0)
    qc.cx(3, 1)
    qc.h(3)
    qc.measure(3, 1)  # Classical bit 1 = XX syndrome

    # 4. Tomography basis rotation on data qubits 0 and 1
    if basis_str == "XX":
        qc.h(0)
        qc.h(1)
    elif basis_str == "YY":
        qc.sdg(0)
        qc.h(0)
        qc.sdg(1)
        qc.h(1)
    elif basis_str == "ZZ":
        pass  # Computational basis

    # 5. Measure data qubits
    qc.measure(0, 2)  # Classical bit 2 = Data 0
    qc.measure(1, 3)  # Classical bit 3 = Data 1

    return qc


def classify_and_postselect_counts(
    raw_counts: Dict[str, int]
) -> Tuple[Dict[str, int], int, int, float]:
    """
    Classify shots into accepted (trivial syndrome 00) and rejected (error syndrome).
    Extract measurement bitstring counts on data qubits for accepted shots.

    Parameters:
        raw_counts: Dictionary of {bitstring: count} from simulator.

    Returns:
        Tuple:
            - accepted_data_counts: Dict[str, int] of 2-bit outcomes on data qubits
            - accepted_shots: Total count of accepted shots
            - rejected_shots: Total count of rejected shots
            - survival_yield: accepted_shots / total_shots
    """
    accepted_data_counts: Dict[str, int] = {}
    accepted_shots = 0
    rejected_shots = 0

    for bitstr, count in raw_counts.items():
        clean_str = bitstr.replace(" ", "")
        if len(clean_str) < 4:
            raise ValueError(f"Expected at least 4 classical bits in bitstring, got '{bitstr}'")

        # In Qiskit standard ordering, index -1 is clbit 0, index -2 is clbit 1, etc.
        syn_zz = clean_str[-1]  # clbit 0
        syn_xx = clean_str[-2]  # clbit 1
        data_0 = clean_str[-3]  # clbit 2
        data_1 = clean_str[-4]  # clbit 3

        # Post-selection rule: accept only if both syndrome bits are '0'
        if syn_zz == "0" and syn_xx == "0":
            accepted_shots += count
            key = f"{data_1}{data_0}"
            accepted_data_counts[key] = accepted_data_counts.get(key, 0) + count
        else:
            rejected_shots += count

    total_shots = accepted_shots + rejected_shots
    survival_yield = (accepted_shots / total_shots) if total_shots > 0 else 0.0

    return accepted_data_counts, accepted_shots, rejected_shots, survival_yield
