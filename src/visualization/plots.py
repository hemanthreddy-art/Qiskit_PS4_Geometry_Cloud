"""
Publication-quality plotting for quantum architectures and benchmark results.
"""

import os
from typing import List, Dict, Any, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend
import matplotlib.pyplot as plt
import numpy as np


def visualize_topology_graphs(
    topologies: List[Any],
    output_path: str,
    figsize: tuple = (18, 6),
) -> str:
    """
    Render 2D graph visualizations of each quantum topology,
    highlighting the chosen remote qubit pairs and edge couplings.

    Parameters:
        topologies: List of topology objects (StarTTopology, HeavyHexTopology, HyperbolicTopology).
        output_path: Destination file path for PNG image.
        figsize: Matplotlib figure size tuple.

    Returns:
        str: Absolute path of saved figure.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    fig, axes = plt.subplots(1, len(topologies), figsize=figsize)
    if len(topologies) == 1:
        axes = [axes]

    titles = [
        "2016 Star/T (5 Qubits)\nYorktown Architecture",
        "Contemporary Heavy-Hex (27 Qubits)\nIBM Falcon/Montreal Style",
        "Finite Hyperbolic (21 Qubits)\nPoincaré Disk Tessellation",
    ]

    for ax, topo, title in zip(axes, topologies, titles):
        ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
        ax.set_aspect("equal")
        ax.axis("off")

        # Obtain coordinates
        if hasattr(topo, "get_layout_coordinates"):
            pos = topo.get_layout_coordinates()
        else:
            # Simple planar fallback for Star/T
            pos = {
                0: (-1.0, 1.0),
                1: (1.0, 1.0),
                2: (0.0, 0.5),
                3: (0.0, -0.5),
                4: (0.0, -1.5),
            }

        remote_pair = set(topo.get_remote_qubits())

        # Draw edges
        for u, v in topo.undirected_edges:
            x_vals = [pos[u][0], pos[v][0]]
            y_vals = [pos[u][1], pos[v][1]]
            ax.plot(x_vals, y_vals, color="#64748b", linewidth=1.8, zorder=1, alpha=0.85)

        # Draw nodes
        for node in range(topo.num_qubits):
            x, y = pos[node]
            is_remote = node in remote_pair
            node_color = "#ef4444" if is_remote else "#0284c7"
            edge_color = "#991b1b" if is_remote else "#0369a1"
            size = 360 if is_remote else 260

            ax.scatter(
                [x], [y],
                s=size,
                color=node_color,
                edgecolors=edge_color,
                linewidths=2.0,
                zorder=3,
            )
            ax.text(
                x, y,
                str(node),
                color="white",
                fontsize=9,
                fontweight="bold",
                ha="center",
                va="center",
                zorder=4,
            )

        # Legend / footnote
        rem_list = list(topo.get_remote_qubits())
        dist = topo.shortest_path_distance(*rem_list)
        ax.text(
            0.5, -0.12,
            f"Remote pair: {rem_list} | Distance: {dist} hops",
            transform=ax.transAxes,
            ha="center",
            fontsize=10,
            color="#334155",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#f8fafc", edgecolor="#cbd5e1"),
        )

    plt.tight_layout()
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return os.path.abspath(output_path)


def plot_comparison_metrics(
    comparison_data: List[Dict[str, Any]],
    output_dir: str,
) -> Dict[str, str]:
    """
    Generate the 3 required benchmark comparison figures:
    1. SWAP count by topology
    2. Native two-qubit gate depth by topology
    3. Ideal vs Noisy Bell fidelity by topology
    Plus a unified summary dashboard.

    Parameters:
        comparison_data: List of experiment result dictionaries.
        output_dir: Output directory for saving images.

    Returns:
        Dict[str, str]: Mapping of metric name to generated image path.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated_files = {}

    names = []
    swap_counts = []
    native_cxs = []
    depths_2q = []
    total_depths = []
    ideal_fids = []
    ideal_errs = []
    noisy_fids = []
    noisy_errs = []

    label_map = {
        "2016_5qubit_T": "Star/T (5Q)",
        "contemporary_ibm_heavy_hex_27q": "Heavy-Hex (27Q)",
        "finite_hyperbolic_poincare_21q": "Hyperbolic (21Q)",
    }

    for item in comparison_data:
        raw_name = item["topology"]["name"]
        names.append(label_map.get(raw_name, raw_name))
        swap_counts.append(item["routing"]["swap_count"])
        native_cxs.append(item["routing"]["native_cx_count"])
        depths_2q.append(item["routing"]["depth_2q_native"])
        total_depths.append(item["routing"]["total_depth_native"])

        comp = item["fidelity_comparison"]
        ideal_fids.append(comp["ideal_fidelity"])
        ideal_errs.append(comp["ideal_uncertainty"])
        noisy_fids.append(comp["noisy_fidelity"])
        noisy_errs.append(comp["noisy_uncertainty"])

    colors = ["#2563eb", "#d97706", "#7c3aed"]

    # -------------------------------------------------------------
    # Figure 1: SWAP count by topology
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(names, swap_counts, color=colors, width=0.55, edgecolor="#1e293b", linewidth=1.2)
    ax.set_ylabel("SWAP Gate Count", fontsize=11, fontweight="bold")
    ax.set_title("Routing Overhead: SWAP Count by Architecture", fontsize=12, fontweight="bold", pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for bar, val in zip(bars, swap_counts):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.15, str(val), ha="center", va="bottom", fontweight="bold", fontsize=11)
    ax.set_ylim(0, max(swap_counts) + 2)
    plt.tight_layout()
    f1_path = os.path.join(output_dir, "swap_count_by_topology.png")
    fig.savefig(f1_path, dpi=200)
    plt.close(fig)
    generated_files["swap_count"] = os.path.abspath(f1_path)

    # -------------------------------------------------------------
    # Figure 2: Native Two-Qubit Depth & CX Count by topology
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(names))
    width = 0.35
    b1 = ax.bar(x - width/2, depths_2q, width, label="Native 2Q Depth", color="#0284c7", edgecolor="#0f172a")
    b2 = ax.bar(x + width/2, native_cxs, width, label="Native CX Count", color="#f97316", edgecolor="#0f172a")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10, fontweight="bold")
    ax.set_ylabel("Circuit Gate Metric", fontsize=11, fontweight="bold")
    ax.set_title("Two-Qubit Depth & CX Gate Count by Architecture", fontsize=12, fontweight="bold", pad=12)
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for bar in list(b1) + list(b2):
        val = int(bar.get_height())
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.3, str(val), ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_ylim(0, max(native_cxs) + 3)
    plt.tight_layout()
    f2_path = os.path.join(output_dir, "two_qubit_depth_by_topology.png")
    fig.savefig(f2_path, dpi=200)
    plt.close(fig)
    generated_files["two_qubit_depth"] = os.path.abspath(f2_path)

    # -------------------------------------------------------------
    # Figure 3: Ideal vs Noisy Bell Fidelity by topology
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(names))
    width = 0.35
    b_ideal = ax.bar(x - width/2, ideal_fids, width, yerr=ideal_errs, capsize=4, label="Ideal Baseline", color="#10b981", edgecolor="#064e3b")
    b_noisy = ax.bar(x + width/2, noisy_fids, width, yerr=noisy_errs, capsize=4, label="Noisy Baseline (Aer)", color="#ef4444", edgecolor="#7f1d1d")
    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=10, fontweight="bold")
    ax.set_ylabel("Bell State Fidelity F(|Φ+⟩)", fontsize=11, fontweight="bold")
    ax.set_title("Bell State Fidelity Comparison: Ideal vs Noisy", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylim(0.0, 1.15)
    ax.legend(loc="lower left", frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)

    for bar, val in zip(b_ideal, ideal_fids):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.03, f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")
    for bar, val in zip(b_noisy, noisy_fids):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.03, f"{val:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    plt.tight_layout()
    f3_path = os.path.join(output_dir, "bell_fidelity_by_topology.png")
    fig.savefig(f3_path, dpi=200)
    plt.close(fig)
    generated_files["bell_fidelity"] = os.path.abspath(f3_path)

    # -------------------------------------------------------------
    # Figure 4: Multi-Panel Architecture Comparison Dashboard
    # -------------------------------------------------------------
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    # Panel 1: SWAP Count
    ax1.bar(names, swap_counts, color=colors, width=0.5, edgecolor="#0f172a")
    ax1.set_title("(a) SWAP Count", fontweight="bold", fontsize=11)
    ax1.set_ylabel("SWAP Operations")
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    for idx, val in enumerate(swap_counts):
        ax1.text(idx, val + 0.1, str(val), ha="center", va="bottom", fontweight="bold")

    # Panel 2: Native Two-Qubit Depth
    ax2.bar(names, depths_2q, color="#0284c7", width=0.5, edgecolor="#0f172a")
    ax2.set_title("(b) Native 2Q Gate Depth", fontweight="bold", fontsize=11)
    ax2.set_ylabel("Circuit 2Q Depth")
    ax2.grid(axis="y", linestyle="--", alpha=0.5)
    for idx, val in enumerate(depths_2q):
        ax2.text(idx, val + 0.2, str(val), ha="center", va="bottom", fontweight="bold")

    # Panel 3: Noisy Fidelity
    ax3.bar(names, noisy_fids, color="#ef4444", width=0.5, yerr=noisy_errs, capsize=4, edgecolor="#0f172a")
    ax3.set_title("(c) Noisy Bell Fidelity", fontweight="bold", fontsize=11)
    ax3.set_ylabel("F(|Φ+⟩)")
    ax3.set_ylim(0.5, 1.05)
    ax3.grid(axis="y", linestyle="--", alpha=0.5)
    for idx, val in enumerate(noisy_fids):
        ax3.text(idx, val + 0.02, f"{val:.4f}", ha="center", va="bottom", fontweight="bold")

    plt.suptitle("Architecture Comparison: Star/T vs Heavy-Hex vs Hyperbolic", fontsize=14, fontweight="bold", y=1.03)
    plt.tight_layout()
    f4_path = os.path.join(output_dir, "architecture_comparison_dashboard.png")
    fig.savefig(f4_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated_files["dashboard"] = os.path.abspath(f4_path)

    return generated_files


def generate_all_checkpoint3_figures(
    all_cases: List[Dict[str, Any]],
    protection_analysis: Dict[str, Any],
    output_dir: str,
) -> Dict[str, str]:
    """
    Generate the 8 required comparison figures for Checkpoint 3:
    1. SWAP count by topology
    2. Native two-qubit depth by topology
    3. Noisy fidelity by topology
    4. Protected fidelity by topology
    5. Fidelity improvement from protection
    6. Survival yield by topology
    7. Fidelity vs survival-yield trade-off
    8. Protection overhead comparison
    Plus a multi-panel 9-case dashboard.
    """
    os.makedirs(output_dir, exist_ok=True)
    generated = {}

    label_map = {
        "2016_5qubit_T": "Star/T (5Q)",
        "contemporary_ibm_heavy_hex_27q": "Heavy-Hex (27Q)",
        "finite_hyperbolic_poincare_21q": "Hyperbolic (21Q)",
    }
    ordered_topos = ["2016_5qubit_T", "contemporary_ibm_heavy_hex_27q", "finite_hyperbolic_poincare_21q"]
    topo_labels = [label_map[t] for t in ordered_topos]
    colors = ["#2563eb", "#d97706", "#7c3aed"]

    # Extract noisy and protected metrics
    case_map = {(c["topology"], c["condition"]): c for c in all_cases}

    swaps_noisy = [case_map[(t, "noisy")]["swap_count"] for t in ordered_topos]
    swaps_prot = [case_map[(t, "noisy_protection")]["swap_count"] for t in ordered_topos]

    depth_2q_noisy = [case_map[(t, "noisy")]["native_two_qubit_depth"] for t in ordered_topos]
    depth_2q_prot = [case_map[(t, "noisy_protection")]["native_two_qubit_depth"] for t in ordered_topos]

    cx_noisy = [case_map[(t, "noisy")]["native_two_qubit_gate_count"] for t in ordered_topos]
    cx_prot = [case_map[(t, "noisy_protection")]["native_two_qubit_gate_count"] for t in ordered_topos]

    fid_noisy = [protection_analysis[t]["noisy_fidelity"] for t in ordered_topos]
    fid_prot = [protection_analysis[t]["protected_fidelity"] for t in ordered_topos]
    fid_imp = [protection_analysis[t]["fidelity_improvement"] for t in ordered_topos]
    yields = [protection_analysis[t]["survival_yield_percent"] for t in ordered_topos]

    extra_cxs = [protection_analysis[t]["overhead"]["circuit_overhead"]["additional_native_cxs"] for t in ordered_topos]
    extra_d2q = [protection_analysis[t]["overhead"]["circuit_overhead"]["additional_depth_2q"] for t in ordered_topos]
    rej_shots = [protection_analysis[t]["rejected_shots"] for t in ordered_topos]

    # -------------------------------------------------------------
    # 1. SWAP count by topology
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(topo_labels))
    w = 0.35
    b1 = ax.bar(x - w/2, swaps_noisy, w, label="Baseline Noisy", color="#3b82f6", edgecolor="#1e3a8a")
    b2 = ax.bar(x + w/2, swaps_prot, w, label="Protected Circuit", color="#8b5cf6", edgecolor="#4c1d95")
    ax.set_xticks(x)
    ax.set_xticklabels(topo_labels, fontweight="bold")
    ax.set_ylabel("SWAP Gate Count", fontweight="bold")
    ax.set_title("1. SWAP Count by Architecture (Baseline vs Protected)", fontweight="bold", pad=12)
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.15, str(int(b.get_height())), ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, max(swaps_prot) + 2)
    p1 = os.path.join(output_dir, "swap_count_by_topology.png")
    fig.savefig(p1, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["swap_count"] = os.path.abspath(p1)

    # -------------------------------------------------------------
    # 2. Native two-qubit depth by topology
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    b1 = ax.bar(x - w/2, depth_2q_noisy, w, label="Baseline Noisy 2Q Depth", color="#0284c7", edgecolor="#082f49")
    b2 = ax.bar(x + w/2, depth_2q_prot, w, label="Protected 2Q Depth", color="#f97316", edgecolor="#7c2d12")
    ax.set_xticks(x)
    ax.set_xticklabels(topo_labels, fontweight="bold")
    ax.set_ylabel("Native Two-Qubit Depth (CX)", fontweight="bold")
    ax.set_title("2. Native Two-Qubit Depth by Architecture", fontweight="bold", pad=12)
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b in list(b1) + list(b2):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.3, str(int(b.get_height())), ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, max(depth_2q_prot) + 3)
    p2 = os.path.join(output_dir, "native_two_qubit_depth_by_topology.png")
    fig.savefig(p2, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["native_two_qubit_depth"] = os.path.abspath(p2)

    # -------------------------------------------------------------
    # 3. Noisy fidelity by topology
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(topo_labels, fid_noisy, color=colors, width=0.5, edgecolor="#0f172a")
    ax.set_ylabel("Noisy Bell Fidelity F(|Φ+⟩)", fontweight="bold")
    ax.set_title("3. Unmitigated Noisy Fidelity by Architecture", fontweight="bold", pad=12)
    ax.set_ylim(0.5, 1.0)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b, val in zip(bars, fid_noisy):
        ax.text(b.get_x() + b.get_width()/2, val + 0.01, f"{val:.4f}", ha="center", va="bottom", fontweight="bold")
    p3 = os.path.join(output_dir, "noisy_fidelity_by_topology.png")
    fig.savefig(p3, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["noisy_fidelity"] = os.path.abspath(p3)

    # -------------------------------------------------------------
    # 4. Protected fidelity by topology
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(topo_labels, fid_prot, color=["#16a34a", "#ca8a04", "#9333ea"], width=0.5, edgecolor="#0f172a")
    ax.set_ylabel("Protected Bell Fidelity F(|Φ+⟩)", fontweight="bold")
    ax.set_title("4. Protected (Post-Selected) Fidelity by Architecture", fontweight="bold", pad=12)
    ax.set_ylim(0.5, 1.0)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b, val in zip(bars, fid_prot):
        ax.text(b.get_x() + b.get_width()/2, val + 0.01, f"{val:.4f}", ha="center", va="bottom", fontweight="bold")
    p4 = os.path.join(output_dir, "protected_fidelity_by_topology.png")
    fig.savefig(p4, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["protected_fidelity"] = os.path.abspath(p4)

    # -------------------------------------------------------------
    # 5. Fidelity improvement from protection
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(topo_labels, fid_imp, color=["#22c55e", "#eab308", "#a855f7"], width=0.5, edgecolor="#0f172a")
    ax.set_ylabel("Fidelity Gain ΔF = F_prot - F_noisy", fontweight="bold")
    ax.set_title("5. Fidelity Gain from Stabilizer Post-Selection", fontweight="bold", pad=12)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b, val in zip(bars, fid_imp):
        ax.text(b.get_x() + b.get_width()/2, val + 0.002, f"+{val:.4f}", ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, max(fid_imp) * 1.25)
    p5 = os.path.join(output_dir, "fidelity_improvement_from_protection.png")
    fig.savefig(p5, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["fidelity_improvement"] = os.path.abspath(p5)

    # -------------------------------------------------------------
    # 6. Survival yield by topology
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(topo_labels, yields, color=["#38bdf8", "#fbbf24", "#c084fc"], width=0.5, edgecolor="#0f172a")
    ax.set_ylabel("Post-Selection Survival Yield (%)", fontweight="bold")
    ax.set_title("6. Post-Selection Survival Yield by Architecture", fontweight="bold", pad=12)
    ax.set_ylim(0, 105)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b, val in zip(bars, yields):
        ax.text(b.get_x() + b.get_width()/2, val + 1.5, f"{val:.1f}%", ha="center", va="bottom", fontweight="bold")
    p6 = os.path.join(output_dir, "survival_yield_by_topology.png")
    fig.savefig(p6, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["survival_yield"] = os.path.abspath(p6)

    # -------------------------------------------------------------
    # 7. Fidelity vs survival-yield trade-off
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 5))
    for t_idx, (name, yld, f_p, f_n) in enumerate(zip(topo_labels, yields, fid_prot, fid_noisy)):
        ax.scatter([yld], [f_p], s=260, color=colors[t_idx], edgecolors="#0f172a", linewidth=1.5, zorder=4, label=name)
        ax.text(yld, f_p + 0.003, f"{name}\nF={f_p:.4f} (ΔF=+{f_p-f_n:.3f})", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax.set_xlabel("Survival Yield (%) [Higher = Cheaper]", fontweight="bold")
    ax.set_ylabel("Protected Fidelity F(|Φ+⟩) [Higher = Better]", fontweight="bold")
    ax.set_title("7. Trade-off: Protected Fidelity vs Survival Yield", fontweight="bold", pad=12)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_xlim(65, 92)
    ax.set_ylim(0.90, 0.94)
    ax.legend(loc="lower left", frameon=True)
    p7 = os.path.join(output_dir, "fidelity_vs_survival_tradeoff.png")
    fig.savefig(p7, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["fidelity_vs_survival_tradeoff"] = os.path.abspath(p7)

    # -------------------------------------------------------------
    # 8. Protection overhead comparison
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    b_cx = ax.bar(x - w/2, extra_cxs, w, label="Additional Native CX Gates", color="#f43f5e", edgecolor="#881337")
    b_dep = ax.bar(x + w/2, extra_d2q, w, label="Additional 2Q Gate Depth", color="#6366f1", edgecolor="#312e81")
    ax.set_xticks(x)
    ax.set_xticklabels(topo_labels, fontweight="bold")
    ax.set_ylabel("Circuit Overhead Quantity", fontweight="bold")
    ax.set_title("8. Protection Hardware Overhead (Gates & Depth)", fontweight="bold", pad=12)
    ax.legend(frameon=True)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b in list(b_cx) + list(b_dep):
        ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.3, str(int(b.get_height())), ha="center", va="bottom", fontweight="bold")
    ax.set_ylim(0, max(extra_cxs) + 3)
    p8 = os.path.join(output_dir, "protection_overhead_comparison.png")
    fig.savefig(p8, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["protection_overhead"] = os.path.abspath(p8)

    # -------------------------------------------------------------
    # 9. Complete 9-Case Multi-Panel Overview Dashboard
    # -------------------------------------------------------------
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))

    # Panel (a): All 9 Cases Fidelity
    ax_a = axes[0, 0]
    cond_labels = ["Ideal", "Noisy", "Protected"]
    bar_w = 0.25
    x_pos = np.arange(len(topo_labels))
    f_ideal_vals = [case_map[(t, "ideal")]["bell_fidelity"] for t in ordered_topos]
    ax_a.bar(x_pos - bar_w, f_ideal_vals, bar_w, label="Ideal", color="#10b981", edgecolor="#064e3b")
    ax_a.bar(x_pos, fid_noisy, bar_w, label="Noisy", color="#ef4444", edgecolor="#7f1d1d")
    ax_a.bar(x_pos + bar_w, fid_prot, bar_w, label="Protected", color="#8b5cf6", edgecolor="#4c1d95")
    ax_a.set_xticks(x_pos)
    ax_a.set_xticklabels(topo_labels, fontweight="bold", fontsize=9)
    ax_a.set_title("(a) Bell Fidelity across all 9 Cases", fontweight="bold")
    ax_a.set_ylabel("F(|Φ+⟩)")
    ax_a.set_ylim(0.5, 1.1)
    ax_a.legend(loc="lower left", fontsize=8)
    ax_a.grid(axis="y", linestyle="--", alpha=0.5)

    # Panel (b): SWAP Gate Count
    ax_b = axes[0, 1]
    ax_b.bar(x_pos - bar_w/2, swaps_noisy, bar_w, label="Baseline", color="#3b82f6", edgecolor="#1e3a8a")
    ax_b.bar(x_pos + bar_w/2, swaps_prot, bar_w, label="Protected", color="#8b5cf6", edgecolor="#4c1d95")
    ax_b.set_xticks(x_pos)
    ax_b.set_xticklabels(topo_labels, fontweight="bold", fontsize=9)
    ax_b.set_title("(b) SWAP Routing Count", fontweight="bold")
    ax_b.set_ylabel("SWAPs")
    ax_b.legend(fontsize=8)
    ax_b.grid(axis="y", linestyle="--", alpha=0.5)

    # Panel (c): Native 2Q Depth
    ax_c = axes[0, 2]
    ax_c.bar(x_pos - bar_w/2, depth_2q_noisy, bar_w, label="Baseline", color="#0284c7", edgecolor="#082f49")
    ax_c.bar(x_pos + bar_w/2, depth_2q_prot, bar_w, label="Protected", color="#f97316", edgecolor="#7c2d12")
    ax_c.set_xticks(x_pos)
    ax_c.set_xticklabels(topo_labels, fontweight="bold", fontsize=9)
    ax_c.set_title("(c) Native 2Q Depth (CX)", fontweight="bold")
    ax_c.set_ylabel("2Q Depth")
    ax_c.legend(fontsize=8)
    ax_c.grid(axis="y", linestyle="--", alpha=0.5)

    # Panel (d): Fidelity Gain ΔF
    ax_d = axes[1, 0]
    ax_d.bar(topo_labels, fid_imp, color=["#22c55e", "#eab308", "#a855f7"], width=0.5, edgecolor="#0f172a")
    ax_d.set_title("(d) Protection Fidelity Gain ΔF", fontweight="bold")
    ax_d.set_ylabel("ΔF = F_prot - F_noisy")
    ax_d.grid(axis="y", linestyle="--", alpha=0.5)
    for b, val in zip(ax_d.patches, fid_imp):
        ax_d.text(b.get_x() + b.get_width()/2, val + 0.002, f"+{val:.4f}", ha="center", va="bottom", fontweight="bold", fontsize=9)
    ax_d.set_ylim(0, max(fid_imp) * 1.25)

    # Panel (e): Survival Yield
    ax_e = axes[1, 1]
    ax_e.bar(topo_labels, yields, color=["#38bdf8", "#fbbf24", "#c084fc"], width=0.5, edgecolor="#0f172a")
    ax_e.set_title("(e) Post-Selection Survival Yield", fontweight="bold")
    ax_e.set_ylabel("Survival Yield (%)")
    ax_e.grid(axis="y", linestyle="--", alpha=0.5)
    for b, val in zip(ax_e.patches, yields):
        ax_e.text(b.get_x() + b.get_width()/2, val + 1.5, f"{val:.1f}%", ha="center", va="bottom", fontweight="bold", fontsize=9)
    ax_e.set_ylim(0, 105)

    # Panel (f): Fidelity vs Survival Trade-off
    ax_f = axes[1, 2]
    for t_idx, (name, yld, f_p) in enumerate(zip(topo_labels, yields, fid_prot)):
        ax_f.scatter([yld], [f_p], s=200, color=colors[t_idx], edgecolors="#0f172a", linewidth=1.5, zorder=4)
        ax_f.text(yld, f_p + 0.002, name, ha="center", va="bottom", fontsize=8, fontweight="bold")
    ax_f.set_title("(f) Fidelity vs Yield Trade-off", fontweight="bold")
    ax_f.set_xlabel("Survival Yield (%)")
    ax_f.set_ylabel("Protected Fidelity")
    ax_f.grid(True, linestyle="--", alpha=0.5)
    ax_f.set_xlim(65, 92)
    ax_f.set_ylim(0.90, 0.94)

    plt.suptitle("PS4 Comprehensive 9-Case Benchmark Dashboard", fontsize=15, fontweight="bold", y=1.01)
    plt.tight_layout()
    p_dash = os.path.join(output_dir, "benchmark_9case_dashboard.png")
    fig.savefig(p_dash, dpi=200, bbox_inches="tight")
    plt.close(fig)
    generated["benchmark_9case_dashboard"] = os.path.abspath(p_dash)

    return generated
