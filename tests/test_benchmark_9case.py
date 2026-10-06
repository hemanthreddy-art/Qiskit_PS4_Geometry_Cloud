"""
Integration tests for the complete 9-case benchmark matrix execution and serialization.
"""

import os
import json
import math
import pytest
from src.benchmark_9case import run_full_9case_benchmark


def test_full_9case_benchmark_execution(tmp_path):
    output_dir = str(tmp_path)

    # Run with fast shots for testing
    benchmark_data = run_full_9case_benchmark(
        shots=1000,
        seed=42,
        output_dir=output_dir,
    )

    # 1. Verify 9 cases total
    cases = benchmark_data["benchmark_cases"]
    assert len(cases) == 9

    # 2. Verify all 3 architectures and 3 conditions are represented
    topologies = {"2016_5qubit_T", "contemporary_ibm_heavy_hex_27q", "finite_hyperbolic_poincare_21q"}
    conditions = {"ideal", "noisy", "noisy_protection"}

    found_combos = {(c["topology"], c["condition"]) for c in cases}
    expected_combos = {(t, cond) for t in topologies for cond in conditions}
    assert found_combos == expected_combos

    # 3. Check mathematical consistency of every single case
    for c in cases:
        xx = c["XX"]
        yy = c["YY"]
        zz = c["ZZ"]
        fid = c["bell_fidelity"]

        # Verify formula: F = (1 + <XX> - <YY> + <ZZ>) / 4
        expected_fid = max(0.0, min(1.0, (1.0 + xx - yy + zz) / 4.0))
        assert math.isclose(fid, expected_fid, abs_tol=1e-5), f"Fidelity mismatch in case {c['topology']} {c['condition']}"

        if c["condition"] == "ideal":
            assert fid > 0.98
        elif c["condition"] == "noisy_protection":
            assert c["survival_yield"] > 0.50
            assert c["survival_yield"] <= 1.0
            assert c["accepted_shots"] + c["rejected_shots"] == c["total_shots_all_bases"]

    # 4. Check protection analysis metrics
    prot_analysis = benchmark_data["protection_analysis"]
    for topo_name in topologies:
        pa = prot_analysis[topo_name]
        f_noisy = pa["noisy_fidelity"]
        f_prot = pa["protected_fidelity"]
        imp = pa["fidelity_improvement"]
        assert math.isclose(imp, f_prot - f_noisy, abs_tol=1e-5)

        # Check overhead fields
        ov = pa["overhead"]["circuit_overhead"]
        assert ov["additional_swaps"] >= 0
        assert ov["additional_native_cxs"] > 0
        assert ov["additional_measurements"] == 2

    # 5. Check JSON serialization
    json_path = benchmark_data["saved_to"]
    assert os.path.exists(json_path)
    with open(json_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert len(loaded["benchmark_cases"]) == 9

    # 6. Check that all generated figures exist
    figs = benchmark_data["generated_figures"]
    for fig_name, fig_path in figs.items():
        assert os.path.exists(fig_path), f"Figure {fig_name} missing at {fig_path}"
