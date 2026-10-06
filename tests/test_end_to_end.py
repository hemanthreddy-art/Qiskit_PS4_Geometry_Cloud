"""
End-to-end integration test for Checkpoint 1 experiment.
"""

import os
import json
from src.experiment import run_checkpoint1_experiment


def test_checkpoint1_end_to_end(tmp_path):
    output_dir = str(tmp_path)
    results = run_checkpoint1_experiment(
        variant="t",
        shots=5000,
        seed=42,
        output_dir=output_dir,
    )

    # 1. Check metadata
    assert results["metadata"]["checkpoint"] == "CHECKPOINT_1"
    assert "qiskit_version" in results["metadata"]
    assert "qiskit_aer_version" in results["metadata"]

    # 2. Check topology
    assert results["topology"]["num_qubits"] == 5
    assert results["topology"]["graph_distance_hops"] == 3

    # 3. Check routing metrics
    assert results["routing"]["swap_count"] == 2
    assert results["routing"]["native_cx_count"] == 7
    assert results["routing"]["depth_2q_native"] == 4

    # 4. Check ideal baseline (Fidelity must be ~1.0 within finite-shot sampling error)
    comp = results["fidelity_comparison"]
    assert comp["ideal_fidelity"] > 0.99
    assert comp["ideal_uncertainty"] >= 0.0

    # 5. Check noisy baseline (Fidelity must degrade due to 7 CX gates and readout errors)
    assert comp["noisy_fidelity"] < comp["ideal_fidelity"]
    assert comp["noisy_fidelity"] > 0.50
    assert comp["fidelity_drop"] > 0.0

    # 6. Check machine-readable file output
    saved_file = results["saved_to"]
    assert os.path.exists(saved_file)
    with open(saved_file, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded["metadata"]["checkpoint"] == "CHECKPOINT_1"
    assert loaded["fidelity_comparison"]["ideal_fidelity"] == comp["ideal_fidelity"]
