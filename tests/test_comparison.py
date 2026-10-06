"""
Tests for multi-topology comparison pipeline.
"""

import os
import json
import pytest
from src.comparison import run_all_topologies_comparison


def test_run_all_topologies_comparison(tmp_path):
    output_dir = str(tmp_path)
    report = run_all_topologies_comparison(
        shots=1000,
        seed=42,
        output_dir=output_dir,
    )

    # 1. Check all 3 architectures are evaluated
    architectures = report["architectures"]
    assert len(architectures) == 3

    arch_names = [a["topology"]["name"] for a in architectures]
    assert "2016_5qubit_T" in arch_names
    assert "contemporary_ibm_heavy_hex_27q" in arch_names
    assert "finite_hyperbolic_poincare_21q" in arch_names

    # 2. Check summary table integrity
    table = report["summary_table"]
    assert len(table) == 3
    for row in table:
        assert row["swap_count"] >= 1
        assert row["native_two_qubit_gate_count"] >= 4
        assert row["native_two_qubit_depth"] >= 2
        assert row["ideal_fidelity"] > 0.98
        assert row["noisy_fidelity"] < row["ideal_fidelity"]
        assert row["noisy_fidelity"] > 0.50

    # 3. Check JSON report saved
    json_path = report["saved_to"]
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert len(loaded["architectures"]) == 3

    # 4. Check generated figures exist on disk
    figs = report["generated_figures"]
    for fig_name, fig_path in figs.items():
        assert os.path.exists(fig_path), f"Figure {fig_name} missing at {fig_path}"
