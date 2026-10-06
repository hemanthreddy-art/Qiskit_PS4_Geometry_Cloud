"""
Tests for Bell state and Pauli basis measurement circuits.
"""

import numpy as np
import pytest
from qiskit.quantum_info import Statevector
from src.circuits.bell_state import create_bell_pair_circuit, append_pauli_measurement


def test_bell_pair_circuit_structure():
    qc = create_bell_pair_circuit()
    assert qc.num_qubits == 2
    assert qc.num_clbits == 0

    ops = qc.count_ops()
    assert ops.get("h") == 1
    assert ops.get("cx") == 1

    # Verify statevector is (|00> + |11>) / sqrt(2)
    sv = Statevector(qc)
    expected_sv = np.array([1 / np.sqrt(2), 0, 0, 1 / np.sqrt(2)])
    assert np.allclose(sv.data, expected_sv)


def test_append_pauli_measurement_gates():
    base = create_bell_pair_circuit()

    # ZZ basis: no extra rotation gates, just measurements
    qc_zz = append_pauli_measurement(base, "ZZ", qubits=(0, 1))
    assert qc_zz.num_clbits == 2
    ops_zz = qc_zz.count_ops()
    assert ops_zz.get("measure") == 2
    assert ops_zz.get("h") == 1  # only from bell prep

    # XX basis: 2 additional H gates
    qc_xx = append_pauli_measurement(base, "XX", qubits=(0, 1))
    ops_xx = qc_xx.count_ops()
    assert ops_xx.get("h") == 3  # 1 from bell + 2 basis rotation
    assert ops_xx.get("measure") == 2

    # YY basis: 2 sdg and 2 H gates
    qc_yy = append_pauli_measurement(base, "YY", qubits=(0, 1))
    ops_yy = qc_yy.count_ops()
    assert ops_yy.get("sdg") == 2
    assert ops_yy.get("h") == 3  # 1 from bell + 2 basis rotation
    assert ops_yy.get("measure") == 2


def test_invalid_basis():
    base = create_bell_pair_circuit()
    with pytest.raises(ValueError, match="Invalid Pauli basis"):
        append_pauli_measurement(base, "XZ")
