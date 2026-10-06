"""
Unit tests for stabilizer-based error detection and post-selection logic.
"""

import pytest
import math
from src.protection.stabilizer_check import (
    build_protected_bell_circuit,
    classify_and_postselect_counts,
)
from src.protection.overhead import compute_protection_overhead


def test_build_protected_bell_circuit_structure():
    """Verify 4-qubit, 4-clbit circuit structure and gate counts."""
    for basis in ["XX", "YY", "ZZ"]:
        qc = build_protected_bell_circuit(basis)
        assert qc.num_qubits == 4
        assert qc.num_clbits == 4

        ops = qc.count_ops()
        # 4 measurements: 2 syndrome + 2 data
        assert ops.get("measure") == 4
        # Bell prep (1 cx) + ZZ check (2 cx) + XX check (2 cx) = 5 cx gates
        assert ops.get("cx") == 5

    # Check basis rotations
    ops_zz = build_protected_bell_circuit("ZZ").count_ops()
    assert ops_zz.get("h") == 3  # 1 from bell, 2 from XX check ancilla

    ops_xx = build_protected_bell_circuit("XX").count_ops()
    assert ops_xx.get("h") == 5  # 1 bell + 2 ancilla XX + 2 data basis rotation

    ops_yy = build_protected_bell_circuit("YY").count_ops()
    assert ops_yy.get("sdg") == 2
    assert ops_yy.get("h") == 5


def test_classify_and_postselect_counts():
    """Test classification of accepted vs rejected shots."""
    # Bitstring format: 'd1 d0 syn_xx syn_zz'
    # '0000': d1=0, d0=0, syn_xx=0, syn_zz=0 -> ACCEPTED (key '00')
    # '1100': d1=1, d0=1, syn_xx=0, syn_zz=0 -> ACCEPTED (key '11')
    # '0101': d1=0, d0=1, syn_xx=0, syn_zz=1 -> REJECTED (ZZ error detected)
    # '1010': d1=1, d0=0, syn_xx=1, syn_zz=0 -> REJECTED (XX error detected)
    # '0011': d1=0, d0=0, syn_xx=1, syn_zz=1 -> REJECTED (both errors)
    raw_counts = {
        "0000": 400,
        "1100": 400,
        "0101": 100,
        "1010": 50,
        "0011": 50,
    }

    acc_counts, acc_shots, rej_shots, yld = classify_and_postselect_counts(raw_counts)

    assert acc_shots == 800
    assert rej_shots == 200
    assert math.isclose(yld, 0.80)
    assert acc_counts == {"00": 400, "11": 400}


def test_compute_protection_overhead():
    """Test protection overhead quantification."""
    baseline_routing = {
        "swap_count": 2,
        "native_cx_count": 7,
        "depth_2q_native": 4,
        "total_depth_native": 5,
    }
    protected_routing = {
        "swap_count": 3,
        "native_cx_count": 14,
        "depth_2q_native": 11,
        "total_depth_native": 14,
    }

    ov = compute_protection_overhead(
        baseline_routing=baseline_routing,
        protected_routing=protected_routing,
        rejected_shots=2870,
        total_shots=20000,
        survival_yield=0.8565,
    )

    assert ov.additional_swaps == 1
    assert ov.additional_native_cxs == 7
    assert ov.additional_depth_2q == 7
    assert ov.additional_total_depth == 9
    assert ov.additional_measurements == 2
    assert ov.rejected_shots == 2870
    assert ov.total_shots == 20000
    assert math.isclose(ov.survival_yield, 0.8565)
