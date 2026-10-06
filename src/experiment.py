"""
End-to-end experiment pipeline for Checkpoint 1:
2016-inspired 5-qubit Star/T coupling graph Bell state experiment.
"""

import json
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import qiskit
import qiskit_aer
from qiskit_aer import AerSimulator

from src.topologies.star_t import StarTTopology
from src.circuits.bell_state import create_bell_pair_circuit, append_pauli_measurement
from src.routing.transpiler import route_bell_circuit
from src.noise.noise_models import (
    NoiseConfiguration,
    build_depolarizing_noise_model,
)
from src.metrics.fidelity import (
    compute_pauli_expectation,
    compute_bell_fidelity,
    PauliMeasurementSummary,
)


def run_pauli_tomography(
    circuit_base: qiskit.QuantumCircuit,
    measured_qubits: tuple,
    simulator: AerSimulator,
    shots: int = 20000,
    seed_simulator: int = 42,
) -> PauliMeasurementSummary:
    """
    Execute XX, YY, and ZZ basis circuits to determine Pauli correlation
    expectation values and Bell state fidelity.
    """
    counts_dict = {}
    exp_dict = {}
    err_dict = {}

    for basis in ["XX", "YY", "ZZ"]:
        meas_circuit = append_pauli_measurement(
            base_circuit=circuit_base,
            basis=basis,
            qubits=measured_qubits,
        )
        job = simulator.run(meas_circuit, shots=shots, seed_simulator=seed_simulator)
        result = job.result()
        counts = result.get_counts()
        counts_dict[basis] = counts

        exp, err = compute_pauli_expectation(counts, total_shots=shots)
        exp_dict[basis] = exp
        err_dict[basis] = err

    fidelity, fid_err = compute_bell_fidelity(
        exp_xx=exp_dict["XX"],
        exp_yy=exp_dict["YY"],
        exp_zz=exp_dict["ZZ"],
        std_err_xx=err_dict["XX"],
        std_err_yy=err_dict["YY"],
        std_err_zz=err_dict["ZZ"],
    )

    return PauliMeasurementSummary(
        shots=shots,
        counts_xx=counts_dict["XX"],
        counts_yy=counts_dict["YY"],
        counts_zz=counts_dict["ZZ"],
        exp_xx=exp_dict["XX"],
        exp_yy=exp_dict["YY"],
        exp_zz=exp_dict["ZZ"],
        fidelity=fidelity,
        std_err_xx=err_dict["XX"],
        std_err_yy=err_dict["YY"],
        std_err_zz=err_dict["ZZ"],
        std_err_fidelity=fid_err,
    )


def run_checkpoint1_experiment(
    variant: str = "t",
    shots: int = 20000,
    seed: int = 42,
    output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute the complete Checkpoint 1 experiment on the 2016-inspired Star/T topology.

    Parameters:
        variant: 't' for Yorktown T-topology, 'star' for pure star topology.
        shots: Number of measurement shots per Pauli basis.
        seed: Random seed for routing and Aer simulation reproducibility.
        output_dir: Directory where results JSON should be saved.

    Returns:
        Dict[str, Any]: Structured results dictionary.
    """
    start_time = datetime.now(timezone.utc).isoformat()

    # 1. Topology Setup
    topology = StarTTopology(variant=variant)
    remote_pair = topology.get_remote_qubits()
    remote_distance = topology.shortest_path_distance(*remote_pair)

    # 2. Bell State Creation: |Phi+> = (|00> + |11>) / sqrt(2)
    bell_circuit = create_bell_pair_circuit()

    # 3. Topology-Constrained Routing
    routing_result = route_bell_circuit(
        bell_circuit=bell_circuit,
        coupling_map=topology.get_coupling_map(),
        initial_layout=list(remote_pair),
        seed=seed,
    )

    # 4. Ideal Simulation Baseline
    ideal_simulator = AerSimulator()
    ideal_summary = run_pauli_tomography(
        circuit_base=routing_result.native_circuit,
        measured_qubits=routing_result.final_physical_qubits,
        simulator=ideal_simulator,
        shots=shots,
        seed_simulator=seed,
    )

    # 5. Documented Realistic Superconducting Noise Model
    noise_cfg = NoiseConfiguration(
        model_name="superconducting_baseline_transmon",
        p_1q=0.001,       # 0.10% single-qubit error
        p_2q=0.015,       # 1.50% two-qubit error
        p_readout=0.015,  # 1.50% readout error
    )
    noise_model = build_depolarizing_noise_model(noise_cfg)
    noisy_simulator = AerSimulator(noise_model=noise_model)

    # 6. Noisy Simulation Baseline
    noisy_summary = run_pauli_tomography(
        circuit_base=routing_result.native_circuit,
        measured_qubits=routing_result.final_physical_qubits,
        simulator=noisy_simulator,
        shots=shots,
        seed_simulator=seed,
    )

    # 7. Comparative Metrics
    fid_drop = ideal_summary.fidelity - noisy_summary.fidelity
    rel_degradation_pct = (fid_drop / ideal_summary.fidelity) * 100.0 if ideal_summary.fidelity > 0 else 0.0

    # 8. Assemble Results Dictionary
    results: Dict[str, Any] = {
        "metadata": {
            "checkpoint": "CHECKPOINT_1",
            "problem_statement": "PS4 - Geometry-Aware Quantum Cloud: Routing, Noise, and Architecture Comparison",
            "timestamp_utc": start_time,
            "qiskit_version": qiskit.__version__,
            "qiskit_aer_version": qiskit_aer.__version__,
            "python_version": sys.version.split()[0],
            "hardware_status": "SIMULATED_AER_BENCHMARK (Explicitly distinguished from physical IBM hardware)",
        },
        "topology": {
            "name": topology.name,
            "variant": topology.variant,
            "num_qubits": topology.num_qubits,
            "edges": topology.undirected_edges,
            "remote_qubits": list(remote_pair),
            "graph_distance_hops": remote_distance,
            "description": topology.description,
        },
        "routing": {
            **routing_result.to_dict(),
            "routing_analysis": (
                f"Preparing |Phi+> between remote physical qubits {list(remote_pair)} "
                f"(distance {remote_distance} hops) required {routing_result.swap_count} SWAP operations "
                f"(decomposing into {routing_result.native_cx_count} native CX gates), "
                f"resulting in a two-qubit gate depth of {routing_result.depth_2q_native}."
            ),
        },
        "noise_model": noise_cfg.to_dict(),
        "measurements": {
            "shots_per_basis": shots,
            "seed": seed,
            "ideal_baseline": ideal_summary.to_dict(),
            "noisy_baseline": noisy_summary.to_dict(),
        },
        "fidelity_comparison": {
            "ideal_fidelity": round(ideal_summary.fidelity, 6),
            "ideal_uncertainty": round(ideal_summary.std_err_fidelity, 6),
            "noisy_fidelity": round(noisy_summary.fidelity, 6),
            "noisy_uncertainty": round(noisy_summary.std_err_fidelity, 6),
            "fidelity_drop": round(fid_drop, 6),
            "relative_degradation_percent": round(rel_degradation_pct, 2),
        },
    }

    # 9. Save Machine-Readable Results
    if output_dir is None:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.join(project_root, "results")

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "checkpoint1_star_t_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    results["saved_to"] = out_file
    return results


def format_experiment_report(results: Dict[str, Any]) -> str:
    """
    Generate a clean, readable text report suitable for terminal presentation
    and technical judging verification.
    """
    meta = results["metadata"]
    topo = results["topology"]
    rout = results["routing"]
    noise = results["noise_model"]
    comp = results["fidelity_comparison"]
    ideal = results["measurements"]["ideal_baseline"]
    noisy = results["measurements"]["noisy_baseline"]

    lines = [
        "=" * 78,
        " IBM QISKIT FALL FEST 2026 - PS4 EXPERIMENT REPORT (CHECKPOINT 1)",
        "=" * 78,
        f"Problem Statement  : {meta['problem_statement']}",
        f"Execution Time     : {meta['timestamp_utc']}",
        f"Software Versions  : Qiskit {meta['qiskit_version']} | Qiskit Aer {meta['qiskit_aer_version']} | Python {meta['python_version']}",
        f"Hardware Nature    : {meta['hardware_status']}",
        "-" * 78,
        "TOPOLOGY & ROUTING METRICS:",
        f"  Topology         : {topo['name']} ({topo['description']})",
        f"  Coupling Graph   : {topo['num_qubits']} qubits, undirected edges: {topo['edges']}",
        f"  Remote Pair      : Qubits {topo['remote_qubits']} (Graph Distance: {topo['graph_distance_hops']} hops)",
        f"  Initial Layout   : {rout['initial_layout']}",
        f"  Final Locations  : {rout['final_physical_qubits']}",
        f"  SWAP Gate Count  : {rout['swap_count']}",
        f"  Native CX Count  : {rout['native_cx_count']}",
        f"  Two-Qubit Depth  : {rout['depth_2q_native']} (decomposed native) | {rout['depth_2q_routed']} (routed SWAP)",
        f"  Total Depth      : {rout['total_depth_native']}",
        "-" * 78,
        "NOISE MODEL SPECIFICATION (Documented Aer Simulator):",
        f"  Model Name       : {noise['model_name']}",
        f"  1-Qubit Error    : {noise['single_qubit_error_rate_p1q'] * 100:.2f}% (depolarizing on H, S_dag)",
        f"  2-Qubit Error    : {noise['two_qubit_error_rate_p2q'] * 100:.2f}% (depolarizing on CX)",
        f"  Readout Error    : {noise['readout_error_rate_pro'] * 100:.2f}% (assignment bit-flip)",
        "-" * 78,
        "BELL-STATE PAULI CORRELATIONS & FIDELITY:",
        f"  Formula: F(|Phi+>) = (1 + <XX> - <YY> + <ZZ>) / 4",
        "",
        f"  [1] IDEAL BASELINE (shots = {results['measurements']['shots_per_basis']}):",
        f"      <XX> = {ideal['expectations']['XX']:+.4f} (+/- {ideal['uncertainties']['sigma_XX']:.4f})",
        f"      <YY> = {ideal['expectations']['YY']:+.4f} (+/- {ideal['uncertainties']['sigma_YY']:.4f})",
        f"      <ZZ> = {ideal['expectations']['ZZ']:+.4f} (+/- {ideal['uncertainties']['sigma_ZZ']:.4f})",
        f"      Fidelity F_ideal = {comp['ideal_fidelity']:.4f} (+/- {comp['ideal_uncertainty']:.4f})",
        "",
        f"  [2] NOISY BASELINE (shots = {results['measurements']['shots_per_basis']}):",
        f"      <XX> = {noisy['expectations']['XX']:+.4f} (+/- {noisy['uncertainties']['sigma_XX']:.4f})",
        f"      <YY> = {noisy['expectations']['YY']:+.4f} (+/- {noisy['uncertainties']['sigma_YY']:.4f})",
        f"      <ZZ> = {noisy['expectations']['ZZ']:+.4f} (+/- {noisy['uncertainties']['sigma_ZZ']:.4f})",
        f"      Fidelity F_noisy = {comp['noisy_fidelity']:.4f} (+/- {comp['noisy_uncertainty']:.4f})",
        "",
        f"  COMPARISON SUMMARY:",
        f"      Absolute Fidelity Drop : {comp['fidelity_drop']:.4f}",
        f"      Relative Degradation   : {comp['relative_degradation_percent']:.2f}%",
        "-" * 78,
        f"Machine-readable output saved to: {results.get('saved_to', 'N/A')}",
        "=" * 78,
    ]
    return "\n".join(lines)
