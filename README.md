# Geometry-Aware Quantum Cloud: Routing, Noise, and Architecture Comparison

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Qiskit 2.5.2](https://img.shields.io/badge/Qiskit-2.5.2-613FE8.svg)](https://qiskit.org/)
[![Qiskit Aer 0.17.2](https://img.shields.io/badge/Qiskit_Aer-0.17.2-purple.svg)](https://github.com/Qiskit/qiskit-aer)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests Passing](https://img.shields.io/badge/tests-38%20passed-success.svg)](#test-suite)

> **IBM Qiskit Fall Fest 2026** — *Problem Statement 4 (PS4)*  
> **Team Nexus AU**  
> An open-source scientific research platform and interactive visualizer investigating the direct impact of quantum processor coupling geometry on routing overhead, noise accumulation, circuit depth, and quantum state fidelity.

---

## 🔬 Executive Summary & Problem Formulation

Modern Noisy Intermediate-Scale Quantum (NISQ) processors do not feature all-to-all qubit connectivity due to physical layout constraints and frequency crowding. When a two-qubit gate is requested between non-adjacent physical qubits, compilers must insert sequences of SWAP gates to shuttle quantum information across the coupling graph.

This introduces the **Routing Penalty Cascade**:
$$\text{Distant Physical Qubits} \longrightarrow \text{SWAP Insertion} \longrightarrow \text{Circuit Depth Expansion} \longrightarrow \text{Decoherence \& Gate Noise} \longrightarrow \text{State Fidelity Collapse}$$

This platform provides a rigorous, reproducible framework and an interactive visualizer to quantify this trade-off across three distinct processor geometry paradigms under realistic noise models, comparing them against active stabilizer-based error detection protocols.

---

## 📐 Topologies Evaluated

| Architecture | Physical Qubits | Couplings (Edges) | Max Degree | Diameter | Key Physical Rationale |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **2016 Star / T** | 5 | 4 | 3 | 3 hops | 2016 IBM-inspired hub topology (Yorktown/ibmqx2 style) offering high centrality but severe bottlenecking at the central hub. |
| **Finite Hyperbolic** | 21 | 40 | 6 | 4 hops | Discrete approximation of negative curvature. Fast exponential coordinate expansion with low hop distance across distant nodes. |
| **Heavy-Hex Subgraph** | 27 | 28 | 3 | 7 hops | Contemporary IBM Falcon-style lattice. Restricts qubit degree to 2 or 3 to eliminate spectator crosstalk and frequency collisions, trading graph distance for low physical interference. |
| **Heavy-Hex Eagle Reference** | 127 | 144 | 3 | 26 hops | Contemporary 127-qubit IBM Eagle lattice used as an architectural scaling baseline. |

---

## 🧪 Scientific Methodology

### 1. Workload Circuit: Entangled Bell State
For each processor geometry, a maximally entangled Bell pair $|\Phi^+\rangle$ is synthesized across the maximally remote physical qubit pair:
$$|\Phi^+\rangle = \frac{|00\rangle + |11\rangle}{\sqrt{2}}$$

### 2. Geometry-Constrained Routing
Circuits are routed onto physical coupling graphs using Qiskit's heuristic SABRE transpiler. Each routed SWAP gate decomposes into $3$ native `CX` gates ($2$ forward, $1$ reverse), inflating the two-qubit gate count and circuit depth.

### 3. Rigorous Pauli Correlation Tomography
Bell-state fidelity is measured directly via Pauli correlation measurements across three orthogonal measurement bases ($XX$, $YY$, and $ZZ$ with $20{,}000$ shots per basis, totaling $60{,}000$ shots per benchmark case):
$$\mathcal{F}(|\Phi^+\rangle) = \frac{1 + \langle XX \rangle - \langle YY \rangle + \langle ZZ \rangle}{4}$$

Pauli expectations $\langle P \rangle$ and associated standard errors $\sigma_{\langle P \rangle}$ are calculated from projective bitstring counts:
$$\langle P \rangle = \frac{N_{\text{even}} - N_{\text{odd}}}{N_{\text{total}}}, \quad \sigma_{\langle P \rangle} = \sqrt{\frac{1 - \langle P \rangle^2}{N_{\text{total}}}}, \quad \sigma_{\mathcal{F}} = \frac{1}{4}\sqrt{\sigma_{XX}^2 + \sigma_{YY}^2 + \sigma_{ZZ}^2}$$

### 4. Noise Model (Superconducting Transmon Baseline)
Simulations are performed on Qiskit Aer using a documented depolarizing noise model:
- **1-Qubit Gate Error**: $0.10\%$ ($p_{1q} = 0.0010$ depolarizing channel on $H$, $S^\dagger$, $\sqrt{X}$, $X$, $R_z$)
- **2-Qubit Gate Error**: $1.50\%$ ($p_{2q} = 0.0150$ depolarizing channel on $CX$ and $SWAP$)
- **Readout Error**: $1.50\%$ ($p_{ro} = 0.0150$ symmetric bit-flip assignment error)

### 5. Stabilizer Parity Checking & Post-Selection
To mitigate noise accumulation during routing, an ancilla helper qubit performs a parity check on the entangled state. Runs where the syndrome detects an error are post-selected out:
- Purifies accepted state fidelity $\mathcal{F}_{\text{protected}} > \mathcal{F}_{\text{noisy}}$
- Yields an operational trade-off quantified by **Survival Yield**:
$$\text{Yield} = \frac{N_{\text{accepted}}}{N_{\text{total}}}$$

---

## 📊 Verified 9-Case Benchmark Matrix

The following data reflects the verified $60{,}000$-shot empirical benchmark stored in [`results/checkpoint3_9case_benchmark.json`](results/checkpoint3_9case_benchmark.json):

| Architecture | Remote Pair | Distance | Condition | SWAPs | Native CX | 2Q Depth | Bell Fidelity $\mathcal{F}$ | Post-Selection Yield |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **Star / T (5Q)** | $(0, 4)$ | 3 hops | **Ideal** | 2 | 7 | 4 | **1.0000** $\pm 0.0000$ | 100.0% |
| | | | **Noisy** | 2 | 7 | 4 | **0.9056** $\pm 0.0015$ | 100.0% |
| | | | **Protected** | 2 | 9 | 6 | **0.9575** $\pm 0.0011$ | **86.5%** |
| **Heavy-Hex (27Q)** | $(0, 14)$ | 7 hops | **Ideal** | 6 | 19 | 13 | **1.0000** $\pm 0.0000$ | 100.0% |
| | | | **Noisy** | 6 | 19 | 13 | **0.7719** $\pm 0.0022$ | 100.0% |
| | | | **Protected** | 6 | 21 | 15 | **0.8872** $\pm 0.0016$ | **69.7%** |
| **Hyperbolic (21Q)** | $(6, 13)$ | 4 hops | **Ideal** | 3 | 10 | 7 | **1.0000** $\pm 0.0000$ | 100.0% |
| | | | **Noisy** | 3 | 10 | 7 | **0.8687** $\pm 0.0018$ | 100.0% |
| | | | **Protected** | 3 | 12 | 9 | **0.9388** $\pm 0.0013$ | **82.4%** |

### Key Takeaways
1. **Distance Multiplier**: Heavy-Hex requires $7$ hops ($6$ SWAPs, $19$ native CX), resulting in a baseline noisy fidelity drop of $22.81\%$ ($0.7719$). In contrast, Hyperbolic requires only $4$ hops ($3$ SWAPs, $10$ native CX) achieving $0.8687$ fidelity.
2. **Error Detection Efficacy**: Active parity post-selection recovers $+11.53\%$ absolute fidelity on Heavy-Hex ($0.7719 \to 0.8872$) and $+7.01\%$ on Hyperbolic ($0.8687 \to 0.9388$).
3. **The Yield Trade-off**: Error detection incurs a yield penalty ($69.7\%$ on Heavy-Hex vs $82.4\%$ on Hyperbolic). Circuits experiencing higher routing noise discard more runs.

---

## 💻 Interactive Research Platform & Web UI

The project includes an interactive web interface powered by a lightweight, zero-dependency Python HTTP server (`serve_ui.py`):

- **Interactive Topology Visualizer**: Render and explore coupling graphs for Star/T (5Q), Heavy-Hex (27Q), Hyperbolic (21Q), and Eagle Reference (127Q).
- **Interactive Node Selection**: Click any two nodes to dynamically calculate shortest paths, SWAP counts, and circuit depth in real time.
- **Dynamic Recommendation Engine**: Automatically evaluates all candidate architectures for the selected pair and quantitatively recommends the optimal topology based on minimum SWAP and gate depth overhead.
- **REST Endpoints**:
  - `GET /api/benchmark-9case`: Returns verified 9-case benchmark results.
  - `GET /api/topologies`: Graph models, nodes, coordinates, and properties.
  - `GET /api/route?topology={key}&qubit_a={a}&qubit_b={b}`: Real-time SABRE routing telemetry.
  - `GET /api/health`: Health status.

---

## 📁 Repository Structure

```
Qiskit_PS4_Geometry_Cloud/
├── README.md                          # Project documentation and reproduction guide
├── requirements.txt                   # Pinned Python package dependencies
├── run_experiment.py                  # CLI experimental pipeline runner
├── serve_ui.py                        # Standalone HTTP server & REST API
├── src/                               # Core scientific engine
│   ├── circuits/                      # Bell state synthesis & basis rotations
│   │   └── bell_state.py
│   ├── noise/                         # Documented superconducting noise models
│   │   └── noise_models.py
│   ├── protection/                    # Parity checking & post-selection syndrome
│   │   ├── stabilizer_check.py
│   │   └── overhead.py
│   ├── routing/                       # SABRE transpiler & gate decomposition
│   │   └── transpiler.py
│   ├── topologies/                    # Architecture graphs & coordinate layouts
│   │   ├── star_t.py
│   │   ├── heavy_hex.py
│   │   └── hyperbolic.py
│   ├── visualization/                 # High-resolution figure generators
│   │   └── plots.py
│   ├── experiment.py                  # Checkpoint 1 experiment runner
│   ├── comparison.py                  # Checkpoint 2 multi-topology comparison
│   └── benchmark_9case.py             # Checkpoint 3 full 9-case matrix benchmark
├── tests/                             # Comprehensive test suite (38 unit & e2e tests)
│   ├── test_circuits.py
│   ├── test_fidelity.py
│   ├── test_routing.py
│   ├── test_topology.py
│   ├── test_heavy_hex.py
│   ├── test_hyperbolic.py
│   ├── test_protection.py
│   ├── test_comparison.py
│   ├── test_benchmark_9case.py
│   ├── test_validation.py
│   ├── test_end_to_end.py
│   └── test_ui_server.py
├── results/                           # Verified machine-readable experimental artifacts
│   ├── checkpoint1_star_t_results.json
│   ├── checkpoint2_architecture_comparison.json
│   ├── checkpoint3_9case_benchmark.json
│   └── figures/                       # Publication-quality benchmark charts
└── ui/                                # Research interface frontend
    ├── index.html                     # Semantic responsive web application
    ├── css/styles.css                 # Custom styling
    └── js/app.js                      # Reactive visualizer and recommendation engine
```

---

## 🚀 Getting Started & Reproduction Guide

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.14.7 64-bit)
- `pip` package manager

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/<owner>/<repo>.git
cd Qiskit_PS4_Geometry_Cloud
pip install -r requirements.txt
```

### 3. Run the Test Suite
Execute the 38 unit and integration tests:
```bash
pytest tests/
```
Output:
```
============================= 38 passed in 16.96s =============================
```

### 4. Reproduce Experiments via CLI

Execute the full 9-case matrix benchmark:
```bash
python run_experiment.py --benchmark-9case --shots 20000 --seed 42
```

Run a specific architecture comparison:
```bash
# Compare all 3 architectures
python run_experiment.py --topology all --shots 20000 --seed 42

# Star/T 5-qubit checkpoint
python run_experiment.py --topology star_t --variant t --shots 20000 --seed 42
```

### 5. Launch the Web Interface
Start the local server:
```bash
python serve_ui.py 8000
```
Open your browser and navigate to:
```
http://127.0.0.1:8000/
```

---

## 🛡️ License

This project is licensed under the [MIT License](LICENSE).
