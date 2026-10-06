"""
Bell state preparation and Pauli measurement circuits.

Target State:
|Phi+> = (|00> + |11>) / sqrt(2)

Pauli Correlation Measurements:
- ZZ Basis: Standard computational basis measurement (eigenvalues: +1 for 00/11, -1 for 01/10).
- XX Basis: Pre-measurement H gates on both qubits rotate X eigenstates to computational Z basis.
- YY Basis: Pre-measurement S† (sdg) followed by H gates rotate Y eigenstates to computational Z basis.
"""

from typing import Tuple
from qiskit import QuantumCircuit, ClassicalRegister


def create_bell_pair_circuit() -> QuantumCircuit:
    """
    Construct an unmeasured 2-qubit circuit preparing the maximally entangled Bell state:
    |Phi+> = (|00> + |11>) / sqrt(2)

    Returns:
        QuantumCircuit: 2-qubit circuit with H(0) and CX(0, 1).
    """
    qc = QuantumCircuit(2, name="bell_phi_plus")
    qc.h(0)
    qc.cx(0, 1)
    return qc


def append_pauli_measurement(
    base_circuit: QuantumCircuit,
    basis: str,
    qubits: Tuple[int, int] = (0, 1)
) -> QuantumCircuit:
    """
    Create a copy of base_circuit, append single-qubit basis transformation gates
    for the requested Pauli observable (XX, YY, or ZZ), and measure into a new
    2-bit classical register.

    Parameters:
        base_circuit: The state preparation or routed circuit.
        basis: One of 'XX', 'YY', 'ZZ' (case-insensitive).
        qubits: Tuple of 2 qubit indices (physical or virtual) to measure.
                qubits[0] is measured into classical bit 0 (logical qubit 0).
                qubits[1] is measured into classical bit 1 (logical qubit 1).

    Returns:
        QuantumCircuit: New circuit with basis rotation and measurement.
    """
    basis_str = basis.upper()
    if basis_str not in {"XX", "YY", "ZZ"}:
        raise ValueError(f"Invalid Pauli basis '{basis}'. Supported bases are 'XX', 'YY', 'ZZ'.")

    q0, q1 = qubits
    qc = base_circuit.copy(name=f"{base_circuit.name}_{basis_str.lower()}")

    # Append basis rotation gates
    if basis_str == "XX":
        qc.h(q0)
        qc.h(q1)
    elif basis_str == "YY":
        # S-dagger followed by H transforms Y eigenbasis to computational Z basis:
        # H S† |+i> = |0>, H S† |-i> = |1>
        qc.sdg(q0)
        qc.h(q0)
        qc.sdg(q1)
        qc.h(q1)
    elif basis_str == "ZZ":
        # Computational basis measurement requires no rotation
        pass

    # Add a dedicated 2-bit classical register for Pauli correlation
    creg = ClassicalRegister(2, name="c_meas")
    qc.add_register(creg)

    # Qubit 0 -> classical bit 0, Qubit 1 -> classical bit 1
    qc.measure(q0, creg[0])
    qc.measure(q1, creg[1])

    return qc
