"""
Tests for Pauli expectation value and Bell fidelity calculations.
"""

import pytest
import numpy as np
from src.metrics.fidelity import compute_pauli_expectation, compute_bell_fidelity


def test_compute_pauli_expectation_even_parity():
    # Counts purely on 00 and 11 -> expectation must be +1.0
    counts = {"00": 500, "11": 500}
    exp, std_err = compute_pauli_expectation(counts, total_shots=1000)
    assert np.isclose(exp, 1.0)
    assert np.isclose(std_err, 0.0)


def test_compute_pauli_expectation_odd_parity():
    # Counts purely on 01 and 10 -> expectation must be -1.0
    counts = {"01": 300, "10": 700}
    exp, std_err = compute_pauli_expectation(counts, total_shots=1000)
    assert np.isclose(exp, -1.0)
    assert np.isclose(std_err, 0.0)


def test_compute_pauli_expectation_mixed():
    # Equal distribution -> expectation must be 0.0
    counts = {"00": 250, "01": 250, "10": 250, "11": 250}
    exp, std_err = compute_pauli_expectation(counts, total_shots=1000)
    assert np.isclose(exp, 0.0)
    assert std_err > 0.0


def test_compute_bell_fidelity_ideal():
    # For |Phi+>: <XX>=1, <YY>=-1, <ZZ>=1
    # F = (1 + 1 - (-1) + 1) / 4 = 1.0
    fid, fid_err = compute_bell_fidelity(exp_xx=1.0, exp_yy=-1.0, exp_zz=1.0)
    assert np.isclose(fid, 1.0)
    assert np.isclose(fid_err, 0.0)


def test_compute_bell_fidelity_maximally_mixed():
    # For maximally mixed state: <XX>=0, <YY>=0, <ZZ>=0
    # F = (1 + 0 - 0 + 0) / 4 = 0.25
    fid, fid_err = compute_bell_fidelity(exp_xx=0.0, exp_yy=0.0, exp_zz=0.0)
    assert np.isclose(fid, 0.25)


def test_compute_bell_fidelity_orthogonal():
    # For |Psi->: <XX>=-1, <YY>=1, <ZZ>=-1
    # Raw formula: (1 - 1 - 1 - 1)/4 = -0.5 -> Clamped to 0.0
    fid, fid_err = compute_bell_fidelity(exp_xx=-1.0, exp_yy=1.0, exp_zz=-1.0)
    assert np.isclose(fid, 0.0)


def test_invalid_shots():
    with pytest.raises(ValueError, match="total_shots must be positive"):
        compute_pauli_expectation({"00": 10}, total_shots=0)
