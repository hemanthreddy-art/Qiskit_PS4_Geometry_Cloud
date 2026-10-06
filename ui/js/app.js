/**
 * app.js - Controller for the PS4 Quantum Architecture Study Research Platform.
 * Implements simplified user experience, progressive disclosure, interactive
 * SVG topology visualizer, dynamic 9-case benchmark table, and raw tomography inspector.
 */

// Embedded fallback of actual verified benchmark results from results/checkpoint3_9case_benchmark.json
// Ensures full functionality offline or via file:// protocol.
const FALLBACK_BENCHMARK_DATA = {
  "metadata": {
    "software_versions": { "qiskit": "2.5.2", "qiskit_aer": "0.17.2", "python": "3.14.7" }
  },
  "benchmark_cases": [
    {
      "topology": "2016_5qubit_T", "condition": "ideal", "selected_physical_qubits": [0, 4],
      "graph_distance": 3, "swap_count": 2, "native_two_qubit_gate_count": 7, "native_two_qubit_depth": 4,
      "total_shots": 20000, "accepted_shots": 20000, "survival_yield": 1.0,
      "XX": 1.0, "YY": -1.0, "ZZ": 1.0, "sigma_XX": 0.0, "sigma_YY": 0.0, "sigma_ZZ": 0.0,
      "bell_fidelity": 1.0, "sigma_fidelity": 0.0,
      "counts": { "XX": { "11": 10077, "00": 9923 }, "YY": { "01": 10077, "10": 9923 }, "ZZ": { "11": 10077, "00": 9923 } }
    },
    {
      "topology": "2016_5qubit_T", "condition": "noisy", "selected_physical_qubits": [0, 4],
      "graph_distance": 3, "swap_count": 2, "native_two_qubit_gate_count": 7, "native_two_qubit_depth": 4,
      "total_shots": 20000, "accepted_shots": 20000, "survival_yield": 1.0,
      "XX": 0.8837, "YY": -0.8503, "ZZ": 0.8886, "sigma_XX": 0.00331, "sigma_YY": 0.003721, "sigma_ZZ": 0.003243,
      "bell_fidelity": 0.90565, "sigma_fidelity": 0.001486,
      "counts": { "XX": { "00": 9355, "11": 9482, "10": 583, "01": 580 }, "YY": { "10": 9193, "01": 9310, "00": 747, "11": 750 }, "ZZ": { "11": 9481, "00": 9405, "01": 568, "10": 546 } }
    },
    {
      "topology": "2016_5qubit_T", "condition": "noisy_protection", "selected_physical_qubits": [0, 4], "ancilla_physical_qubits": [1, 2],
      "graph_distance": 3, "swap_count": 3, "native_two_qubit_gate_count": 14, "native_two_qubit_depth": 11,
      "total_shots": 20000, "total_shots_all_bases": 60000, "accepted_shots": 51392, "rejected_shots": 8608, "survival_yield": 0.856533, "survival_yield_percent": 85.65,
      "XX": 0.904892, "YY": -0.88452, "ZZ": 0.893766, "sigma_XX": 0.003251, "sigma_YY": 0.003551, "sigma_ZZ": 0.003426,
      "bell_fidelity": 0.920794, "sigma_fidelity": 0.001472,
      "accepted_counts": { "XX": { "00": 8072, "11": 8261, "01": 427, "10": 396 }, "YY": { "01": 8056, "10": 8116, "00": 477, "11": 515 }, "ZZ": { "11": 8200, "00": 8031, "01": 424, "10": 494 } }
    },
    {
      "topology": "contemporary_ibm_heavy_hex_27q", "condition": "ideal", "selected_physical_qubits": [0, 14],
      "graph_distance": 7, "swap_count": 6, "native_two_qubit_gate_count": 19, "native_two_qubit_depth": 13,
      "total_shots": 20000, "accepted_shots": 20000, "survival_yield": 1.0,
      "XX": 1.0, "YY": -1.0, "ZZ": 1.0, "sigma_XX": 0.0, "sigma_YY": 0.0, "sigma_ZZ": 0.0,
      "bell_fidelity": 1.0, "sigma_fidelity": 0.0,
      "counts": { "XX": { "11": 10077, "00": 9923 }, "YY": { "01": 10077, "10": 9923 }, "ZZ": { "11": 10077, "00": 9923 } }
    },
    {
      "topology": "contemporary_ibm_heavy_hex_27q", "condition": "noisy", "selected_physical_qubits": [0, 14],
      "graph_distance": 7, "swap_count": 6, "native_two_qubit_gate_count": 19, "native_two_qubit_depth": 13,
      "total_shots": 20000, "accepted_shots": 20000, "survival_yield": 1.0,
      "XX": 0.7692, "YY": -0.709, "ZZ": 0.8525, "sigma_XX": 0.004518, "sigma_YY": 0.004986, "sigma_ZZ": 0.003697,
      "bell_fidelity": 0.832675, "sigma_fidelity": 0.001925,
      "counts": { "XX": { "11": 8876, "00": 8816, "01": 1145, "10": 1163 }, "YY": { "10": 8511, "01": 8579, "00": 1481, "11": 1429 }, "ZZ": { "11": 9323, "00": 9202, "10": 743, "01": 732 } }
    },
    {
      "topology": "contemporary_ibm_heavy_hex_27q", "condition": "noisy_protection", "selected_physical_qubits": [0, 14], "ancilla_physical_qubits": [1, 13],
      "graph_distance": 7, "swap_count": 11, "native_two_qubit_gate_count": 38, "native_two_qubit_depth": 23,
      "total_shots": 20000, "total_shots_all_bases": 60000, "accepted_shots": 43423, "rejected_shots": 16577, "survival_yield": 0.723717, "survival_yield_percent": 72.37,
      "XX": 0.906981, "YY": -0.893046, "ZZ": 0.901918, "sigma_XX": 0.003498, "sigma_YY": 0.003732, "sigma_ZZ": 0.003588,
      "bell_fidelity": 0.925485, "sigma_fidelity": 0.001477,
      "accepted_counts": { "XX": { "00": 6886, "11": 6924, "10": 344, "01": 328 }, "YY": { "01": 6845, "10": 6828, "00": 361, "11": 416 }, "ZZ": { "11": 6982, "00": 6806, "10": 382, "01": 328 } }
    },
    {
      "topology": "finite_hyperbolic_poincare_21q", "condition": "ideal", "selected_physical_qubits": [6, 13],
      "graph_distance": 4, "swap_count": 3, "native_two_qubit_gate_count": 10, "native_two_qubit_depth": 7,
      "total_shots": 20000, "accepted_shots": 20000, "survival_yield": 1.0,
      "XX": 1.0, "YY": -1.0, "ZZ": 1.0, "sigma_XX": 0.0, "sigma_YY": 0.0, "sigma_ZZ": 0.0,
      "bell_fidelity": 1.0, "sigma_fidelity": 0.0,
      "counts": { "XX": { "11": 10077, "00": 9923 }, "YY": { "01": 10077, "10": 9923 }, "ZZ": { "11": 10077, "00": 9923 } }
    },
    {
      "topology": "finite_hyperbolic_poincare_21q", "condition": "noisy", "selected_physical_qubits": [6, 13],
      "graph_distance": 4, "swap_count": 3, "native_two_qubit_gate_count": 10, "native_two_qubit_depth": 7,
      "total_shots": 20000, "accepted_shots": 20000, "survival_yield": 1.0,
      "XX": 0.8482, "YY": -0.8132, "ZZ": 0.8872, "sigma_XX": 0.003745, "sigma_YY": 0.004114, "sigma_ZZ": 0.003261,
      "bell_fidelity": 0.88715, "sigma_fidelity": 0.001596,
      "counts": { "XX": { "11": 9276, "00": 9206, "10": 767, "01": 751 }, "YY": { "10": 9140, "01": 8992, "00": 891, "11": 977 }, "ZZ": { "00": 9358, "11": 9514, "01": 525, "10": 603 } }
    },
    {
      "topology": "finite_hyperbolic_poincare_21q", "condition": "noisy_protection", "selected_physical_qubits": [6, 13], "ancilla_physical_qubits": [1, 3],
      "graph_distance": 4, "swap_count": 6, "native_two_qubit_gate_count": 23, "native_two_qubit_depth": 16,
      "total_shots": 20000, "total_shots_all_bases": 60000, "accepted_shots": 47152, "rejected_shots": 12848, "survival_yield": 0.785867, "survival_yield_percent": 78.59,
      "XX": 0.897537, "YY": -0.878661, "ZZ": 0.882151, "sigma_XX": 0.003518, "sigma_YY": 0.003805, "sigma_ZZ": 0.003759,
      "bell_fidelity": 0.914587, "sigma_fidelity": 0.0016,
      "accepted_counts": { "XX": { "00": 7396, "11": 7512, "10": 407, "01": 398 }, "YY": { "01": 7456, "10": 7330, "00": 472, "11": 483 }, "ZZ": { "11": 7448, "00": 7325, "01": 476, "10": 449 } }
    }
  ]
};

// Topology Presets for Quick Selection & Dropdowns
const TOPOLOGY_PRESETS = {
  star_t: {
    name: "Star / T (5Q)",
    benchmark: [0, 4],
    neighbor: [0, 2],
    furthest: [0, 4],
    num_qubits: 5
  },
  heavy_hex_27: {
    name: "Heavy-Hex Subgraph (27Q)",
    benchmark: [0, 14],
    neighbor: [0, 1],
    furthest: [0, 26],
    num_qubits: 27
  },
  hyperbolic: {
    name: "Finite Hyperbolic (21Q)",
    benchmark: [6, 13],
    neighbor: [0, 1],
    furthest: [19, 20],
    num_qubits: 21
  },
  heavy_hex_127: {
    name: "IBM 127Q Reference (FakeBrisbane)",
    benchmark: [0, 126],
    neighbor: [0, 1],
    furthest: [0, 126],
    num_qubits: 127
  }
};

// Global App State
let appData = {
  benchmark: FALLBACK_BENCHMARK_DATA,
  topologies: null,
  activeTopologyKey: "star_t",
  activeCondition: "ideal",
  currentPair: [0, 4],
  selectionStage: 0, // 0 = idle / ready for QA, 1 = QA selected, awaiting QB
  activeRouteResult: null,
  isRoutingInProgress: false
};

// On Load
document.addEventListener("DOMContentLoaded", async () => {
  setupPrimaryNav();
  setupSubNavs();
  setupCollapsible();
  setupFigureViewer();
  setupTableFilters();
  setupRoutingControls();
  setupConditionSelector();
  await loadData();
  renderBenchmarkTable();
  initTopologyPair(appData.activeTopologyKey);
});

// Primary Navigation (5 Main Sections) & Research Journey Stepper
function setupPrimaryNav() {
  const navBtns = document.querySelectorAll(".nav-btn");
  const stepperBtns = document.querySelectorAll(".stepper-step");

  function activateSection(secName, targetScrollId = null) {
    // 1. Update Primary Nav Buttons
    navBtns.forEach(b => {
      if (b.dataset.section === secName) {
        b.classList.add("active");
      } else {
        b.classList.remove("active");
      }
    });

    // 2. Show corresponding page section
    const secId = "sec-" + secName;
    document.querySelectorAll(".page-section").forEach(sec => sec.classList.remove("active"));
    const targetSec = document.getElementById(secId);
    if (targetSec) {
      targetSec.classList.add("active");
    }

    // 3. Scroll to target element or top
    if (targetScrollId) {
      // If target is inside a sub-view (like sub-visualizer), ensure sub-nav is active
      if (targetScrollId.startsWith("sub-")) {
        const subKey = targetScrollId.replace("sub-", "");
        const subBtn = document.querySelector(`.sub-btn[data-sub="${subKey}"]`);
        if (subBtn) subBtn.click();
      }
      setTimeout(() => {
        const scrollEl = document.getElementById(targetScrollId);
        if (scrollEl) {
          scrollEl.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 50);
      return;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  // Handle primary nav button clicks
  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const secName = btn.dataset.section;
      activateSection(secName);

      // Explicitly set active stepper button according to the target section
      const sectionToStepScroll = {
        overview: "sec-overview",
        architectures: "sec-architectures",
        results: "main-finding-hero",
        protection: "sec-protection",
        analysis: "decision-guide-card"
      };
      const targetScroll = sectionToStepScroll[secName];
      stepperBtns.forEach(sb => {
        if (sb.dataset.scroll === targetScroll) {
          sb.classList.add("active");
        } else {
          sb.classList.remove("active");
        }
      });
    });
  });

  // Handle research journey stepper button clicks
  stepperBtns.forEach(stepBtn => {
    stepBtn.addEventListener("click", () => {
      stepperBtns.forEach(b => b.classList.remove("active"));
      stepBtn.classList.add("active");

      const secName = stepBtn.dataset.section;
      const scrollTarget = stepBtn.dataset.scroll;
      activateSection(secName, scrollTarget);
    });
  });

  // Hero Guided CTA: "Start 2-Minute Walkthrough"
  const ctaWalkthrough = document.getElementById("cta-walkthrough");
  if (ctaWalkthrough) {
    ctaWalkthrough.addEventListener("click", () => {
      activateSection("architectures", "sec-architectures");
      stepperBtns.forEach(sb => {
        if (sb.dataset.scroll === "sec-architectures") {
          sb.classList.add("active");
        } else {
          sb.classList.remove("active");
        }
      });
    });
  }

  // Hero Guided CTA: "Explore Full Results"
  const ctaResults = document.getElementById("cta-results");
  if (ctaResults) {
    ctaResults.addEventListener("click", () => {
      activateSection("results", "main-finding-hero");
      stepperBtns.forEach(sb => {
        if (sb.dataset.scroll === "main-finding-hero") {
          sb.classList.add("active");
        } else {
          sb.classList.remove("active");
        }
      });
    });
  }
}

// Sub-Navigation Tabs inside Architectures and Results
function setupSubNavs() {
  const subBtns = document.querySelectorAll(".sub-btn");
  subBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const parent = btn.closest(".sub-nav-wrapper");
      if (!parent) return;

      parent.querySelectorAll(".sub-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      const targetSubId = "sub-" + btn.dataset.sub;
      parent.querySelectorAll(".sub-view").forEach(v => v.classList.remove("active"));
      const targetView = document.getElementById(targetSubId);
      if (targetView) targetView.classList.add("active");
    });
  });

  // Topology toolbar buttons
  const topoBtns = document.querySelectorAll(".btn-topo");
  topoBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      topoBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      initTopologyPair(btn.dataset.topo);
    });
  });

  // Close inspector button
  const closeInspectorBtn = document.getElementById("close-inspector-btn");
  if (closeInspectorBtn) {
    closeInspectorBtn.addEventListener("click", () => {
      document.getElementById("tomography-inspector").classList.remove("active");
    });
  }
}

// Collapsible Technical Specs on Landing Page & Reproducibility Drawer
function setupCollapsible() {
  const toggleBtn = document.getElementById("toggle-tech-specs");
  const content = document.getElementById("tech-specs-content");
  if (toggleBtn && content) {
    toggleBtn.addEventListener("click", () => {
      const isActive = content.classList.toggle("active");
      const icon = toggleBtn.querySelector(".toggle-icon");
      if (icon) icon.innerText = isActive ? "−" : "+";
    });
  }

  // Reproducibility drawer text toggle
  const reproDrawer = document.querySelector(".repro-drawer");
  const reproText = document.getElementById("repro-toggle-text");
  if (reproDrawer && reproText) {
    reproDrawer.addEventListener("toggle", () => {
      reproText.innerText = reproDrawer.open
        ? "Click to collapse formulas"
        : "Click to expand / collapse formulas";
    });
  }
}

// Data Fetching with Embedded Fallback
async function loadData() {
  try {
    const resBench = await fetch("/api/benchmark-9case");
    if (resBench.ok) {
      appData.benchmark = await resBench.json();
    }
  } catch (err) {
    console.info("Using embedded benchmark results data.");
  }

  try {
    const resTopo = await fetch("/api/topologies");
    if (resTopo.ok) {
      appData.topologies = await resTopo.json();
    }
  } catch (err) {
    console.info("Using embedded topology models.");
  }
}

// Dynamic 9-Case Benchmark Matrix
function renderBenchmarkTable() {
  const tbody = document.getElementById("benchmark-matrix-tbody");
  if (!tbody || !appData.benchmark || !appData.benchmark.benchmark_cases) return;

  const archFilter = document.getElementById("filter-arch") ? document.getElementById("filter-arch").value : "all";
  const condFilter = document.getElementById("filter-cond") ? document.getElementById("filter-cond").value : "all";

  tbody.innerHTML = "";

  appData.benchmark.benchmark_cases.forEach((item, index) => {
    if (archFilter !== "all" && item.topology !== archFilter) return;
    if (condFilter !== "all" && item.condition !== condFilter) return;

    const tr = document.createElement("tr");
    tr.dataset.index = index;

    const archLabel = friendlyArchName(item.topology);
    const condLabel = friendlyCondName(item.condition);
    const yieldPercent = (item.survival_yield * 100).toFixed(2) + "%";
    const fidelityStr = Number(item.bell_fidelity).toFixed(4);
    const sigmaStr = item.sigma_fidelity > 0 ? Number(item.sigma_fidelity).toFixed(4) : "0.0000";

    tr.innerHTML = `
      <td><strong>${archLabel}</strong></td>
      <td>${condLabel}</td>
      <td class="num">${item.graph_distance}</td>
      <td class="num">${item.swap_count}</td>
      <td class="num">${item.native_two_qubit_gate_count}</td>
      <td class="num">${item.native_two_qubit_depth}</td>
      <td class="num">${item.accepted_shots.toLocaleString()}</td>
      <td class="num highlight-green">${yieldPercent}</td>
      <td class="num">${item.XX !== undefined ? item.XX.toFixed(4) : "-"}</td>
      <td class="num">${item.YY !== undefined ? item.YY.toFixed(4) : "-"}</td>
      <td class="num">${item.ZZ !== undefined ? item.ZZ.toFixed(4) : "-"}</td>
      <td class="num highlight-cyan-bold">${fidelityStr}</td>
      <td class="num">&plusmn;${sigmaStr}</td>
    `;

    tr.addEventListener("click", () => {
      document.querySelectorAll("#benchmark-matrix-tbody tr").forEach(r => r.classList.remove("selected-row"));
      tr.classList.add("selected-row");
      inspectCase(index);
    });

    tbody.appendChild(tr);
  });
}

function setupTableFilters() {
  const archSelect = document.getElementById("filter-arch");
  const condSelect = document.getElementById("filter-cond");
  if (archSelect) archSelect.addEventListener("change", renderBenchmarkTable);
  if (condSelect) condSelect.addEventListener("change", renderBenchmarkTable);
}

// Tomography Inspector
function inspectCase(index) {
  const item = appData.benchmark.benchmark_cases[index];
  if (!item) return;

  const drawer = document.getElementById("tomography-inspector");
  const title = document.getElementById("inspector-title");
  const content = document.getElementById("inspector-content");

  drawer.classList.add("active");
  title.innerText = `Raw Shot Distribution: ${friendlyArchName(item.topology)} [${friendlyCondName(item.condition)}]`;

  const countsObj = item.accepted_counts || item.counts || {};

  const bases = [
    { label: "XX", val: item.XX, counts: countsObj.XX },
    { label: "YY", val: item.YY, counts: countsObj.YY },
    { label: "ZZ", val: item.ZZ, counts: countsObj.ZZ }
  ];

  let html = `<div class="tomo-grid">`;

  bases.forEach(b => {
    const corrStr = (b.val !== undefined && b.val !== null) ? Number(b.val).toFixed(4) : "—";
    html += `
      <div class="tomo-card">
        <div class="tomo-card-header">
          <span class="tomo-basis-title">Basis &lang;${b.label}&rang; Correlation:</span>
          <span class="tomo-corr-val">${corrStr}</span>
        </div>
        <table class="tomo-table">
          <thead>
            <tr>
              <th>Bitstring</th>
              <th>Counts</th>
              <th>Parity</th>
            </tr>
          </thead>
          <tbody>${renderCountRows(b.counts)}</tbody>
        </table>
      </div>
    `;
  });

  html += `</div>`;

  if (item.condition === "noisy_protection") {
    const total = item.total_shots_all_bases || 60000;
    const accepted = item.accepted_shots || 0;
    const yieldPct = (item.survival_yield * 100).toFixed(2);
    const rejected = item.rejected_shots ? item.rejected_shots : (total - accepted);

    html += `
      <div class="tomo-summary-card">
        <strong class="summary-title">Post-Selection Summary</strong>
        <p>Retained <strong>${accepted.toLocaleString()}</strong> of ${total.toLocaleString()} shots (<strong>${yieldPct}%</strong> survival yield). Discarded <strong>${rejected.toLocaleString()}</strong> corrupted runs.</p>
      </div>
    `;
  } else {
    const totalShots = item.total_shots ? (item.total_shots * 3) : 60000;
    const acceptedShots = item.accepted_shots ? (item.accepted_shots * 3) : totalShots;
    const condName = friendlyCondName(item.condition);
    html += `
      <div class="tomo-summary-card">
        <strong class="summary-title">${condName} Summary</strong>
        <p>All <strong>${acceptedShots.toLocaleString()}</strong> of ${totalShots.toLocaleString()} shots evaluated across 3 Pauli bases (100% accepted, no post-selection filter applied).</p>
      </div>
    `;
  }

  content.innerHTML = html;
}

function renderCountRows(basisCounts) {
  if (!basisCounts) return `<tr><td colspan="3" style="text-align: center; color: var(--text-muted); padding: 8px;">No counts recorded</td></tr>`;
  return Object.entries(basisCounts)
    .sort((a, b) => b[1] - a[1])
    .map(([bitstring, count]) => {
      const isParallel = (bitstring === "00" || bitstring === "11");
      const parity = isParallel ? "+1" : "-1";
      const parityClass = isParallel ? "parity-pos" : "parity-neg";
      return `
        <tr>
          <td><code>${bitstring}</code></td>
          <td>${Number(count).toLocaleString()}</td>
          <td class="${parityClass}">${parity}</td>
        </tr>
      `;
    }).join("");
}

// Dynamic Target Pair Selection & Live Routing Engine
function setupRoutingControls() {
  const selectA = document.getElementById("select-qubit-a");
  const selectB = document.getElementById("select-qubit-b");
  const btnRun = document.getElementById("btn-run-routing");

  const btnPresetBench = document.getElementById("preset-benchmark");
  const btnPresetNeighbor = document.getElementById("preset-neighbor");
  const btnPresetFurthest = document.getElementById("preset-furthest");

  if (selectA) {
    selectA.addEventListener("change", () => {
      const qa = parseInt(selectA.value);
      let qb = parseInt(selectB.value);
      if (qa === qb) {
        const numQubits = getTopologyNumQubits(appData.activeTopologyKey);
        qb = (qa + 1) % numQubits;
        selectB.value = qb;
      }
      appData.currentPair = [qa, qb];
      appData.selectionStage = 0;
      resetRoutingInstructionText();
      updatePresetButtonsState();
      fetchLiveRouting(appData.activeTopologyKey, qa, qb);
    });
  }

  if (selectB) {
    selectB.addEventListener("change", () => {
      let qa = parseInt(selectA.value);
      const qb = parseInt(selectB.value);
      if (qa === qb) {
        const numQubits = getTopologyNumQubits(appData.activeTopologyKey);
        qa = (qb + 1) % numQubits;
        selectA.value = qa;
      }
      appData.currentPair = [qa, qb];
      appData.selectionStage = 0;
      resetRoutingInstructionText();
      updatePresetButtonsState();
      fetchLiveRouting(appData.activeTopologyKey, qa, qb);
    });
  }

  if (btnRun) {
    btnRun.addEventListener("click", () => {
      const qa = parseInt(selectA.value);
      const qb = parseInt(selectB.value);
      fetchLiveRouting(appData.activeTopologyKey, qa, qb);
    });
  }

  if (btnPresetBench) {
    btnPresetBench.addEventListener("click", () => {
      const preset = TOPOLOGY_PRESETS[appData.activeTopologyKey]?.benchmark || [0, 1];
      applyPresetPair(preset, btnPresetBench);
    });
  }

  if (btnPresetNeighbor) {
    btnPresetNeighbor.addEventListener("click", () => {
      const preset = TOPOLOGY_PRESETS[appData.activeTopologyKey]?.neighbor || [0, 1];
      applyPresetPair(preset, btnPresetNeighbor);
    });
  }

  if (btnPresetFurthest) {
    btnPresetFurthest.addEventListener("click", () => {
      const preset = TOPOLOGY_PRESETS[appData.activeTopologyKey]?.furthest || [0, 1];
      applyPresetPair(preset, btnPresetFurthest);
    });
  }
}

function resetRoutingInstructionText() {
  const instrText = document.getElementById("routing-instruction-text");
  if (instrText) {
    instrText.innerHTML = `<strong>Interactive Canvas:</strong> Click any qubit in the graph to select Qubit A, then click a second qubit to select Qubit B. The Qiskit SABRE transpiler routes the Bell state circuit in real time.`;
  }
}

function applyPresetPair(pair, activeBtn) {
  const selectA = document.getElementById("select-qubit-a");
  const selectB = document.getElementById("select-qubit-b");
  if (selectA) selectA.value = pair[0];
  if (selectB) selectB.value = pair[1];
  appData.currentPair = [...pair];
  appData.selectionStage = 0;
  resetRoutingInstructionText();

  document.querySelectorAll(".btn-preset").forEach(b => b.classList.remove("active"));
  if (activeBtn) activeBtn.classList.add("active");

  fetchLiveRouting(appData.activeTopologyKey, pair[0], pair[1]);
}

function updatePresetButtonsState() {
  const current = appData.currentPair;
  const presets = TOPOLOGY_PRESETS[appData.activeTopologyKey];
  const btnPresetBench = document.getElementById("preset-benchmark");
  const btnPresetNeighbor = document.getElementById("preset-neighbor");
  const btnPresetFurthest = document.getElementById("preset-furthest");
  const statusTag = document.getElementById("pair-status-tag");

  document.querySelectorAll(".btn-preset").forEach(b => b.classList.remove("active"));
  if (!presets) return;

  const isMatch = (pair) => (pair[0] === current[0] && pair[1] === current[1]) || (pair[0] === current[1] && pair[1] === current[0]);

  if (presets.benchmark && isMatch(presets.benchmark) && btnPresetBench) {
    btnPresetBench.classList.add("active");
    if (statusTag) {
      statusTag.textContent = "Benchmark pair";
      statusTag.className = "pair-status-tag tag-benchmark";
    }
  } else if (presets.neighbor && isMatch(presets.neighbor) && btnPresetNeighbor) {
    btnPresetNeighbor.classList.add("active");
    if (statusTag) {
      statusTag.textContent = "Direct neighbor pair";
      statusTag.className = "pair-status-tag tag-preset";
    }
  } else if (presets.furthest && isMatch(presets.furthest) && btnPresetFurthest) {
    btnPresetFurthest.classList.add("active");
    if (statusTag) {
      statusTag.textContent = "Furthest pair";
      statusTag.className = "pair-status-tag tag-preset";
    }
  } else {
    if (statusTag) {
      statusTag.textContent = "Custom pair selected";
      statusTag.className = "pair-status-tag tag-custom";
    }
  }
}

function getTopologyNumQubits(topoKey) {
  if (appData.topologies && appData.topologies[topoKey]) {
    return appData.topologies[topoKey].num_qubits;
  }
  return TOPOLOGY_PRESETS[topoKey]?.num_qubits || 5;
}

function populateDropdowns(numQubits, selectedA, selectedB) {
  const selectA = document.getElementById("select-qubit-a");
  const selectB = document.getElementById("select-qubit-b");
  if (!selectA || !selectB) return;

  selectA.innerHTML = "";
  selectB.innerHTML = "";

  for (let i = 0; i < numQubits; i++) {
    const optA = document.createElement("option");
    optA.value = i;
    optA.textContent = `Qubit ${i}`;
    if (i === selectedA) optA.selected = true;
    selectA.appendChild(optA);

    const optB = document.createElement("option");
    optB.value = i;
    optB.textContent = `Qubit ${i}`;
    if (i === selectedB) optB.selected = true;
    selectB.appendChild(optB);
  }
}

function initTopologyPair(topoKey) {
  appData.activeTopologyKey = topoKey;
  appData.selectionStage = 0;
  resetRoutingInstructionText();

  const nameEl = document.getElementById("topo-info-name");
  if (nameEl) nameEl.innerText = friendlyArchName(topoKey);

  const note127 = document.getElementById("topo-127-short-note");
  if (note127) {
    if (topoKey === "heavy_hex_127") {
      note127.classList.add("active");
    } else {
      note127.classList.remove("active");
    }
  }

  const defaultPair = TOPOLOGY_PRESETS[topoKey]?.benchmark || [0, 1];
  appData.currentPair = [...defaultPair];
  const numQubits = getTopologyNumQubits(topoKey);

  populateDropdowns(numQubits, defaultPair[0], defaultPair[1]);
  updatePresetButtonsState();
  renderTopologySVG(topoKey, null, defaultPair);
  fetchLiveRouting(topoKey, defaultPair[0], defaultPair[1]);
}

function handleNodeClick(nodeId) {
  const selectA = document.getElementById("select-qubit-a");
  const selectB = document.getElementById("select-qubit-b");
  const instrText = document.getElementById("routing-instruction-text");

  if (appData.selectionStage === 0) {
    appData.currentPair[0] = nodeId;
    appData.selectionStage = 1;
    if (selectA) selectA.value = nodeId;
    const statusTag = document.getElementById("pair-status-tag");
    if (statusTag) {
      statusTag.textContent = "Selecting pair...";
      statusTag.className = "pair-status-tag tag-custom";
    }
    document.querySelectorAll(".btn-preset").forEach(b => b.classList.remove("active"));
    if (instrText) {
      instrText.innerHTML = `<strong>Qubit A set to Q${nodeId}</strong>. Now click target Qubit B in the diagram, or select it from the dropdown.`;
    }
    renderTopologySVG(appData.activeTopologyKey, null, [nodeId, appData.currentPair[1]]);
  } else {
    if (nodeId === appData.currentPair[0]) {
      appData.selectionStage = 0;
      resetRoutingInstructionText();
      renderTopologySVG(appData.activeTopologyKey, null, appData.currentPair);
      return;
    }

    appData.currentPair[1] = nodeId;
    appData.selectionStage = 0;
    if (selectB) selectB.value = nodeId;
    if (instrText) {
      instrText.innerHTML = `<strong>Interactive Canvas:</strong> Target pair <strong>(Q${appData.currentPair[0]}, Q${appData.currentPair[1]})</strong> selected. Running Qiskit SABRE transpiler...`;
    }
    updatePresetButtonsState();
    fetchLiveRouting(appData.activeTopologyKey, appData.currentPair[0], appData.currentPair[1]);
  }
}

async function fetchLiveRouting(topoKey, qa, qb) {
  const badge = document.getElementById("routing-engine-badge");
  const swapsEl = document.getElementById("topo-info-swaps");
  const cxEl = document.getElementById("topo-info-cx");
  const depthEl = document.getElementById("topo-info-depth");
  const distEl = document.getElementById("topo-info-dist");
  const pathEl = document.getElementById("topo-info-path");
  const pairEl = document.getElementById("topo-info-pair");
  const nameEl = document.getElementById("topo-info-name");

  if (badge) {
    badge.innerText = "Transpiling route via Qiskit SABRE...";
    badge.style.color = "var(--accent-blue)";
    badge.style.background = "var(--accent-blue-bg)";
    badge.style.borderColor = "var(--accent-blue-border)";
  }

  try {
    const res = await fetch(`/api/route?topology=${encodeURIComponent(topoKey)}&qubit_a=${qa}&qubit_b=${qb}`);
    if (res.ok) {
      const data = await res.json();
      appData.activeRouteResult = data;

      if (nameEl) nameEl.innerText = friendlyArchName(data.topology_name || topoKey);
      if (pairEl) pairEl.innerText = `(${data.qubit_a}, ${data.qubit_b})`;
      if (distEl) distEl.innerText = `${data.graph_distance} hop${data.graph_distance === 1 ? '' : 's'}`;
      if (swapsEl) swapsEl.innerText = `${data.swap_count} SWAP${data.swap_count === 1 ? '' : 's'}`;
      if (cxEl) cxEl.innerText = `${data.native_cx_count} CX`;
      if (depthEl) depthEl.innerText = `${data.depth_2q_native}`;
      if (pathEl) pathEl.innerText = data.shortest_path.join(" → ");

      updateConditionAndRoutingBanner();

      renderTopologySVG(topoKey, data.shortest_path, [data.qubit_a, data.qubit_b]);
      updateTopologyRecommendation(topoKey, data.qubit_a, data.qubit_b, data);
    } else {
      throw new Error("Route API error");
    }
  } catch (err) {
    console.warn("Live route fetch failed, using local graph routing fallback", err);
    updateConditionAndRoutingBanner();
    renderTopologySVG(topoKey, null, [qa, qb]);
    updateTopologyRecommendation(topoKey, qa, qb, null);
  } finally {
    if (badge) {
      badge.innerText = "Qiskit SABRE Transpiler Active";
      badge.style.color = "var(--accent-green)";
      badge.style.background = "var(--accent-green-bg)";
      badge.style.borderColor = "var(--accent-green-border)";
    }
  }
}

// Interactive SVG Topology Visualizer
function renderTopologySVG(topoKey, customPath = null, customPair = null) {
  const svg = document.getElementById("topology-svg");
  if (!svg) return;

  const fallbackTopos = {
    star_t: {
      name: "2016 Star/T (Yorktown 5Q)",
      remote_qubits: [0, 4],
      ancilla_qubits: [1, 2],
      shortest_path: [0, 2, 3, 4],
      edges: [[0, 2], [1, 2], [2, 3], [3, 4]],
      coords: { 0: [-100, -80], 1: [100, -80], 2: [0, -10], 3: [0, 60], 4: [0, 130] }
    },
    heavy_hex_27: {
      name: "Heavy-Hex Subgraph (Falcon 27Q)",
      remote_qubits: [0, 14],
      ancilla_qubits: [1, 13],
      shortest_path: [0, 1, 4, 7, 10, 12, 13, 14],
      edges: [
        [0, 1], [1, 2], [1, 4], [2, 3], [3, 5],
        [4, 7], [5, 8], [6, 7], [7, 10], [8, 9],
        [8, 11], [10, 12], [11, 14], [12, 13], [12, 15],
        [13, 14], [14, 16], [15, 18], [16, 19], [17, 18],
        [18, 21], [19, 20], [19, 22], [21, 23], [22, 25],
        [23, 24], [24, 25], [25, 26]
      ],
      coords: {
        0: [-160, -110], 1: [-110, -110], 2: [-60, -110], 3: [-10, -110], 5: [40, -110], 8: [90, -110], 9: [140, -110],
        4: [-110, -50], 11: [90, -50],
        6: [-160, 0], 7: [-110, 0], 10: [-60, 0], 12: [-10, 0], 13: [40, 0], 14: [90, 0], 16: [140, 0],
        15: [-10, 50], 19: [140, 50],
        17: [-110, 110], 18: [-60, 110], 21: [-10, 110], 23: [40, 110], 24: [90, 110], 25: [140, 110], 26: [170, 110],
        20: [170, 50], 22: [140, 80]
      }
    },
    hyperbolic: {
      name: "Finite Hyperbolic Poincaré Patch (21Q)",
      remote_qubits: [6, 13],
      ancilla_qubits: [1, 3],
      shortest_path: [6, 1, 0, 3, 13],
      edges: [
        [0, 1], [0, 2], [0, 3], [0, 4], [0, 5], [0, 6],
        [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 1],
        [1, 7], [1, 8], [2, 9], [2, 10], [3, 11], [3, 12],
        [4, 13], [4, 14], [5, 15], [5, 16], [6, 17], [6, 18],
        [7, 8], [9, 10], [11, 12], [13, 14], [15, 16], [17, 18],
        [8, 9], [10, 11], [12, 13], [14, 15], [16, 17], [18, 7],
        [7, 19], [11, 19], [13, 20], [17, 20]
      ],
      coords: generateHyperbolicCoords()
    },
    heavy_hex_127: {
      name: "IBM 127Q Eagle Reference Model (FakeBrisbane)",
      remote_qubits: [0, 126],
      ancilla_qubits: [],
      shortest_path: [0, 1, 2, 3, 4, 15, 22, 23, 24, 34, 43, 44, 45, 54, 64, 65, 66, 73, 85, 86, 87, 93, 106, 107, 108, 112, 126],
      edges: [],
      coords: generateEagle127Coords()
    }
  };

  const topo = (appData.topologies && appData.topologies[topoKey])
    ? transformServerTopo(appData.topologies[topoKey])
    : fallbackTopos[topoKey];

  if (!topo) return;

  const activePair = customPair || appData.currentPair || topo.remote_qubits;
  const activePath = customPath || (appData.activeRouteResult && appData.activeRouteResult.shortest_path) || topo.shortest_path;
  const isBenchmarkMatch = (topo.remote_qubits[0] === activePair[0] && topo.remote_qubits[1] === activePair[1]) ||
                          (topo.remote_qubits[0] === activePair[1] && topo.remote_qubits[1] === activePair[0]);

  // Edges
  const pathEdgeSet = new Set();
  if (activePath && activePath.length > 1) {
    for (let i = 0; i < activePath.length - 1; i++) {
      const u = activePath[i];
      const v = activePath[i + 1];
      pathEdgeSet.add(`${Math.min(u, v)}-${Math.max(u, v)}`);
    }
  }

  let svgContent = "";

  topo.edges.forEach(([u, v]) => {
    const p1 = topo.coords[u];
    const p2 = topo.coords[v];
    if (!p1 || !p2) return;

    const isPath = pathEdgeSet.has(`${Math.min(u, v)}-${Math.max(u, v)}`);
    const stroke = isPath ? "#15803d" : "#cbd5e1";
    const strokeWidth = isPath ? "2.6" : "1.2";
    const opacity = isPath ? "1.0" : "0.75";

    svgContent += `<line x1="${p1[0]}" y1="${p1[1]}" x2="${p2[0]}" y2="${p2[1]}" stroke="${stroke}" stroke-width="${strokeWidth}" stroke-opacity="${opacity}" />`;
  });

  // Nodes
  const remoteSet = new Set(activePair);
  const ancillaSet = isBenchmarkMatch ? new Set(topo.ancilla_qubits || []) : new Set();
  const pathSet = new Set(activePath || []);

  Object.entries(topo.coords).forEach(([idStr, [x, y]]) => {
    const id = parseInt(idStr);
    let fill = "#ffffff";
    let r = 8.5;
    let stroke = "#64748b";
    let strokeWidth = "1.5";
    let textColor = "#0f172a";
    const isSelectedQubitA = (appData.selectionStage === 1 && id === appData.currentPair[0]);

    if (remoteSet.has(id)) {
      fill = "#1e40af"; // Target Data Qubits: Deep Academic Blue
      r = 11;
      stroke = "#0f172a";
      strokeWidth = "2";
      textColor = "#ffffff";
    } else if (ancillaSet.has(id)) {
      fill = "#d97706"; // Syndrome Ancilla: Muted Amber
      r = 10;
      stroke = "#78350f";
      strokeWidth = "1.5";
      textColor = "#ffffff";
    } else if (pathSet.has(id)) {
      fill = "#16a34a"; // Routing Path Bridge: Muted Green
      r = 9.5;
      stroke = "#14532d";
      strokeWidth = "1.5";
      textColor = "#ffffff";
    }

    let extraRing = "";
    if (isSelectedQubitA) {
      extraRing = `<circle cx="${x}" cy="${y}" r="15" fill="none" stroke="#1e40af" stroke-width="1.8" stroke-dasharray="3 3" />`;
    }

    svgContent += `
      <g class="topo-node" data-node="${id}" style="cursor: pointer;">
        ${extraRing}
        <circle cx="${x}" cy="${y}" r="${r}" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}" />
        <text x="${x}" y="${y + 3}" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="${r > 9 ? 8 : 7}" font-weight="600" fill="${textColor}">${id}</text>
      </g>
    `;
  });

  svg.innerHTML = svgContent;

  // Tooltip & click event handling
  const tooltip = document.getElementById("topo-tooltip");
  svg.querySelectorAll(".topo-node").forEach(g => {
    const id = parseInt(g.dataset.node);

    g.addEventListener("mouseenter", (e) => {
      let role = "Lattice Qubit";
      if (id === activePair[0]) role = "Target Data Qubit A";
      else if (id === activePair[1]) role = "Target Data Qubit B";
      else if (ancillaSet.has(id)) role = "Syndrome Ancilla";
      else if (pathSet.has(id)) role = "Routing Path Bridge";

      if (tooltip) {
        tooltip.innerHTML = `<strong>Qubit ${id}</strong><br>${role}<br><span style="font-size:10px; color:var(--accent-blue);">Click to select</span>`;
        tooltip.style.display = "block";
        tooltip.style.left = (e.clientX - 80) + "px";
        tooltip.style.top = (e.clientY - 60) + "px";
      }
    });

    g.addEventListener("mouseleave", () => {
      if (tooltip) tooltip.style.display = "none";
    });

    g.addEventListener("click", () => {
      handleNodeClick(id);
    });
  });
}

function generateHyperbolicCoords() {
  const coords = { 0: [0, 0] };
  const r1 = 65;
  for (let i = 1; i <= 6; i++) {
    const angle = ((i - 1) * Math.PI) / 3;
    coords[i] = [Math.round(r1 * Math.cos(angle)), Math.round(r1 * Math.sin(angle))];
  }
  const r2 = 135;
  for (let j = 7; j <= 18; j++) {
    const angle = ((j - 7) * Math.PI) / 6;
    coords[j] = [Math.round(r2 * Math.cos(angle)), Math.round(r2 * Math.sin(angle))];
  }
  coords[19] = [-90, -130];
  coords[20] = [90, 130];
  return coords;
}

function generateEagle127Coords() {
  const coords = {};
  const cols = 14;
  for (let i = 0; i < 127; i++) {
    const col = i % cols;
    const row = Math.floor(i / cols);
    coords[i] = [Math.round((col - 6.5) * 24), Math.round((row - 4.5) * 28)];
  }
  return coords;
}

function transformServerTopo(serverTopo) {
  const coords = {};
  Object.entries(serverTopo.coordinates).forEach(([k, v]) => {
    coords[parseInt(k)] = [Math.round(v[0] * 38), Math.round(-v[1] * 38)];
  });
  return {
    name: serverTopo.name,
    num_qubits: serverTopo.num_qubits,
    remote_qubits: serverTopo.remote_qubits,
    ancilla_qubits: serverTopo.ancilla_qubits,
    shortest_path: serverTopo.shortest_path,
    edges: serverTopo.undirected_edges,
    coords: coords
  };
}

// Publication Figure Viewer
function setupFigureViewer() {
  const figBtns = document.querySelectorAll(".fig-nav-btn");
  const img = document.getElementById("active-figure-img");
  const caption = document.getElementById("active-figure-caption");

  const captions = {
    "benchmark_9case_dashboard.png": "Figure 1: Executive 9-Case Dashboard. Multi-panel comparative analysis of routing overhead, gate depth, Bell-state fidelity, and survival yield across all architectures.",
    "bell_fidelity_by_topology.png": "Figure 2: Bell-State Fidelity Progression. Demonstrates measured state fidelity F(Φ+) across Ideal, Noisy baseline, and Noisy + Protection conditions.",
    "fidelity_improvement_from_protection.png": "Figure 3: Absolute Fidelity Improvement (ΔF). Quantifies the net error suppression benefit delivered by stabilizer parity checking and post-selection.",
    "fidelity_vs_survival_tradeoff.png": "Figure 4: Fidelity vs. Post-Selection Survival Yield Trade-Off. Demonstrates the inverse correlation between noise purification and shot sampling efficiency.",
    "protection_overhead_comparison.png": "Figure 5: Circuit Protection Overhead. Compares baseline and protected native two-qubit gate counts (CX) and two-qubit gate depths.",
    "survival_yield_by_topology.png": "Figure 6: Post-Selection Survival Yield (%). Shows percentage of experimental shots surviving syndrome verification (s = '00').",
    "swap_count_by_topology.png": "Figure 7: Topology-Constrained SWAP Gate Operations. Measured routing cost for remote physical qubit pairs across evaluated architectures.",
    "native_two_qubit_depth_by_topology.png": "Figure 8: Native Two-Qubit Hardware Depth. Hardware execution depth under SABRE transpilation for baseline and protected circuits.",
    "topology_graphs.png": "Figure 9: Topological Coupling Graph Schematics. Visual representation of Star/T (5Q), Heavy-Hex (27Q), and Finite Hyperbolic (21Q) architectures."
  };

  figBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      figBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      const figName = btn.dataset.fig;
      img.src = "/figures/" + figName;
      caption.innerHTML = `<strong>${btn.innerText}:</strong> ${captions[figName] || ""}`;
    });
  });
}

// Utility Formatters
function friendlyArchName(arch) {
  if (!arch) return "Unknown";
  const s = String(arch).toLowerCase();
  if (s.includes("127") || s.includes("brisbane") || s.includes("eagle")) return "Heavy-Hex Reference (127Q)";
  if (s.includes("heavy_hex") || s.includes("heavyhex") || s.includes("27q")) return "Heavy-Hex (27Q)";
  if (s.includes("star") || s.includes("5qubit") || s.includes("star_t")) return "Star / T (5Q)";
  if (s.includes("hyperbolic") || s.includes("poincare") || s.includes("21q")) return "Hyperbolic (21Q)";
  return arch;
}

function friendlyCondName(cond) {
  if (cond === "ideal") return "Ideal Baseline";
  if (cond === "noisy") return "Noisy Baseline";
  if (cond === "noisy_protection") return "With Post-Selection";
  return cond;
}

// Experiment Condition Selector
function setupConditionSelector() {
  const condBtns = document.querySelectorAll(".btn-condition");
  condBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      condBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      appData.activeCondition = btn.dataset.condition || "ideal";
      updateConditionAndRoutingBanner();
    });
  });
}

function getBenchmarkCase(topoKey, condition) {
  if (!appData.benchmark || !appData.benchmark.benchmark_cases) return null;
  let targetTopo = topoKey;
  if (topoKey === "star_t") targetTopo = "2016_5qubit_T";
  else if (topoKey === "heavy_hex_27") targetTopo = "contemporary_ibm_heavy_hex_27q";
  else if (topoKey === "hyperbolic") targetTopo = "finite_hyperbolic_poincare_21q";

  let targetCond = condition;
  if (condition === "protected") targetCond = "noisy_protection";

  return appData.benchmark.benchmark_cases.find(c =>
    c.topology === targetTopo && c.condition === targetCond
  ) || null;
}

function updateConditionAndRoutingBanner() {
  const banner = document.getElementById("routing-verification-banner");
  const bannerBadge = banner ? banner.querySelector(".banner-badge") : null;
  const bannerText = document.getElementById("routing-banner-text");
  const explainerEl = document.getElementById("condition-explainer-text");

  const cond = appData.activeCondition || "ideal";
  const topoKey = appData.activeTopologyKey;
  const pair = appData.currentPair;
  const route = appData.activeRouteResult;

  // Update short explanation text near selector
  if (explainerEl) {
    if (cond === "ideal") {
      explainerEl.innerText = "Reference result without simulated hardware noise.";
    } else if (cond === "noisy") {
      explainerEl.innerText = "Result after simulated hardware noise is applied. Noise is applied during circuit execution.";
    } else if (cond === "protected") {
      explainerEl.innerText = "Result after error detection and post-selection. Error-checking keeps runs that pass the protection test.";
    }
  }

  if (!banner || !bannerBadge || !bannerText) return;

  const presets = TOPOLOGY_PRESETS[topoKey];
  const isBenchPair = presets && presets.benchmark &&
    ((pair[0] === presets.benchmark[0] && pair[1] === presets.benchmark[1]) ||
     (pair[0] === presets.benchmark[1] && pair[1] === presets.benchmark[0])) &&
    topoKey !== "heavy_hex_127";

  if (isBenchPair) {
    const bCase = getBenchmarkCase(topoKey, cond);
    if (bCase) {
      if (cond === "ideal") {
        banner.className = "routing-banner banner-benchmark banner-ideal";
        bannerBadge.innerText = "OFFICIAL BENCHMARK PAIR • IDEAL";
        bannerText.innerHTML = `Reference result without simulated hardware noise. Target Bell-state fidelity is <strong>1.0000</strong> (100% survival yield across 60,000 shots).`;
      } else if (cond === "noisy") {
        banner.className = "routing-banner banner-benchmark banner-noisy";
        bannerBadge.innerText = "OFFICIAL BENCHMARK PAIR • NOISY";
        bannerText.innerHTML = `Result after simulated hardware noise is applied. Noise is applied during circuit execution. Measured noisy baseline Bell-state fidelity: <strong>${Number(bCase.bell_fidelity).toFixed(4)}</strong> (no error detection applied, 100% accepted).`;
      } else if (cond === "protected") {
        banner.className = "routing-banner banner-benchmark banner-protected";
        bannerBadge.innerText = "OFFICIAL BENCHMARK PAIR • PROTECTED";
        const yieldPct = (bCase.survival_yield * 100).toFixed(2);
        const kept = bCase.accepted_shots.toLocaleString();
        const rejected = bCase.rejected_shots ? bCase.rejected_shots.toLocaleString() : (60000 - bCase.accepted_shots).toLocaleString();
        bannerText.innerHTML = `Result after error detection and post-selection. Error-checking keeps runs that pass the protection test. Measured protected Bell-state fidelity: <strong>${Number(bCase.bell_fidelity).toFixed(4)}</strong> with <strong>${yieldPct}% survival yield</strong> (${kept} of 60,000 shots kept; ${rejected} discarded corrupted runs).`;
      }
    }
  } else {
    // Non-benchmark target pair
    banner.className = "routing-banner banner-custom";
    bannerBadge.innerText = (topoKey === "heavy_hex_127") ? "127Q SCALING REFERENCE" : "LIVE ROUTING (UNMEASURED PAIR)";
    const swapCount = route ? route.swap_count : "-";
    const cxCount = route ? route.native_cx_count : "-";
    const depth = route ? route.depth_2q_native : "-";
    const dist = route ? route.graph_distance : "-";

    const note127Msg = (topoKey === "heavy_hex_127")
      ? ` <em>127Q is a structural/scaling reference only. The verified 60,000-shot benchmark uses the 27Q Heavy-Hex subgraph.</em>`
      : ` Verified benchmark fidelity was only measured on the official benchmark pair.`;

    bannerText.innerHTML = `<strong>Routing calculated live. No measured fidelity result is available for this pair.</strong><span style="display:block; margin-top: 4px; font-size: 12.5px; color: var(--text-body);">Dynamic circuit transpiled by Qiskit SABRE requires <strong>${swapCount} SWAPs</strong> (${cxCount} native CX gates, 2Q depth ${depth}) across ${dist} hops.${note127Msg}</span>`;
  }
}

// Target-Pair Topology Recommendation Engine (Part 2)
async function updateTopologyRecommendation(activeTopoKey, qa, qb, currentRoute) {
  const tableBody = document.getElementById("rec-table-body");
  const winnerCard = document.getElementById("rec-winner-card");
  const winnerName = document.getElementById("rec-winner-name");
  const winnerMetrics = document.getElementById("rec-winner-metrics");
  const winnerWhy = document.getElementById("rec-winner-why");
  const safetyBox = document.getElementById("rec-safety-box");

  if (!tableBody || !winnerCard) return;

  const candidateTopos = [
    { key: "star_t", name: "Star / T (5Q)", numQubits: 5, benchPair: [0, 4] },
    { key: "hyperbolic", name: "Finite Hyperbolic (21Q)", numQubits: 21, benchPair: [6, 13] },
    { key: "heavy_hex_27", name: "Heavy-Hex Subgraph (27Q)", numQubits: 27, benchPair: [0, 14] },
    { key: "heavy_hex_127", name: "Heavy-Hex Reference (127Q)", numQubits: 127, benchPair: [0, 126] }
  ];

  // Evaluate candidate architectures for this connection
  const results = await Promise.all(
    candidateTopos.map(async (t) => {
      const isCapacityOk = qa < t.numQubits && qb < t.numQubits;
      if (!isCapacityOk) {
        return {
          ...t,
          viable: false,
          reason: `Requires > ${t.numQubits} qubits`,
          distance: "N/A",
          swaps: "N/A",
          cx: "N/A",
          depth: "N/A"
        };
      }

      // If active topology and currentRoute is provided
      if (t.key === activeTopoKey && currentRoute) {
        return {
          ...t,
          viable: true,
          distance: currentRoute.graph_distance,
          swaps: currentRoute.swap_count,
          cx: currentRoute.native_cx_count,
          depth: currentRoute.depth_2q_native
        };
      }

      // Otherwise fetch live from route API
      try {
        const res = await fetch(`/api/route?topology=${t.key}&qubit_a=${qa}&qubit_b=${qb}`);
        if (res.ok) {
          const d = await res.json();
          return {
            ...t,
            viable: true,
            distance: d.graph_distance,
            swaps: d.swap_count,
            cx: d.native_cx_count,
            depth: d.depth_2q_native
          };
        }
      } catch (e) {
        // Fallback
      }

      return {
        ...t,
        viable: false,
        reason: "Route unavailable",
        distance: "N/A",
        swaps: "N/A",
        cx: "N/A",
        depth: "N/A"
      };
    })
  );

  // Filter viable topologies and sort by routing efficiency:
  // 1. Lower SWAP count
  // 2. Lower native CX count
  // 3. Lower 2Q depth
  const viable = results.filter(r => r.viable && typeof r.swaps === "number");
  viable.sort((a, b) => {
    if (a.swaps !== b.swaps) return a.swaps - b.swaps;
    if (a.cx !== b.cx) return a.cx - b.cx;
    return a.depth - b.depth;
  });

  const winner = viable.length > 0 ? viable[0] : null;

  // Render Table Rows
  tableBody.innerHTML = "";
  results.forEach(r => {
    const isWinner = winner && r.key === winner.key;
    const isActive = r.key === activeTopoKey;
    const tr = document.createElement("tr");
    if (isWinner) tr.classList.add("rec-row-winner");

    let statusHtml = "";
    if (isWinner) {
      statusHtml = '<span class="highlight-blue-bold">★ Recommended</span>';
    } else if (r.viable) {
      statusHtml = '<span class="highlight-green">Viable</span>';
    } else {
      statusHtml = `<span class="text-muted">${r.reason}</span>`;
    }

    let actionHtml = "";
    if (r.viable) {
      if (isActive) {
        actionHtml = '<span class="rec-active-badge">Active View</span>';
      } else {
        actionHtml = `<button class="btn-rec-switch" data-topo="${r.key}" title="View ${r.name} with pair (${qa}, ${qb})">View on topology &rarr;</button>`;
      }
    } else {
      actionHtml = '<span class="text-muted">—</span>';
    }

    tr.innerHTML = `
      <td><strong>${r.name}</strong> ${isActive ? '<span class="text-muted">(Active)</span>' : ''}</td>
      <td class="mono">${r.viable ? `(${qa}, ${qb})` : '—'}</td>
      <td class="mono">${r.viable ? `${r.distance} hop${r.distance === 1 ? '' : 's'}` : '—'}</td>
      <td class="mono">${r.viable ? `${r.swaps} SWAP${r.swaps === 1 ? '' : 's'}` : '—'}</td>
      <td class="mono">${r.viable ? `${r.cx} CX` : '—'}</td>
      <td class="mono">${r.viable ? `${r.depth}` : '—'}</td>
      <td>${statusHtml}</td>
      <td>${actionHtml}</td>
    `;
    tableBody.appendChild(tr);
  });

  // Attach action button click handlers to switch active topology preserving the pair
  tableBody.querySelectorAll(".btn-rec-switch").forEach(btn => {
    btn.addEventListener("click", () => {
      const targetTopo = btn.getAttribute("data-topo");
      switchTopologyPreservingPair(targetTopo, qa, qb);
    });
  });

  // Render Winner Card
  if (winner) {
    if (winnerName) winnerName.innerText = winner.name;
    if (winnerMetrics) {
      winnerMetrics.innerHTML = `
        <span><strong>${winner.swaps} SWAP${winner.swaps === 1 ? '' : 's'}</strong></span>
        <span class="sep">&bull;</span>
        <span><strong>${winner.cx} Native CX</strong></span>
        <span class="sep">&bull;</span>
        <span><strong>Depth ${winner.depth}</strong></span>
        <span class="sep">&bull;</span>
        <span>Distance: <strong>${winner.distance} hop${winner.distance === 1 ? '' : 's'}</strong></span>
      `;
    }
    if (winnerWhy) {
      let explanation = "";
      if (winner.swaps === 0) {
        explanation = `<strong>Why?</strong> On ${winner.name}, these qubits are directly adjacent physical neighbors (distance 1 hop), requiring zero SWAP operations and minimizing hardware noise exposure.`;
      } else {
        explanation = `<strong>Why?</strong> This topology requires fewer routing operations for this connection (${winner.swaps} SWAP${winner.swaps === 1 ? '' : 's'}, ${winner.cx} native CX, depth ${winner.depth}), reducing additional gate operations and minimizing expected exposure to noise.`;
      }
      winnerWhy.innerHTML = explanation;
    }

    // Winner action box for 1-click switch
    const winnerActionBox = document.getElementById("rec-winner-action-box");
    if (winnerActionBox) {
      if (winner.key !== activeTopoKey) {
        winnerActionBox.innerHTML = `
          <button class="btn-rec-switch btn-winner-switch" id="btn-winner-switch" data-topo="${winner.key}">
            View recommended ${winner.name} on canvas &rarr;
          </button>
        `;
        const btnWin = document.getElementById("btn-winner-switch");
        if (btnWin) {
          btnWin.addEventListener("click", () => {
            switchTopologyPreservingPair(winner.key, qa, qb);
          });
        }
      } else {
        winnerActionBox.innerHTML = "";
      }
    }

    // Scientific Fidelity Safety:
    // Check if the pair matches any verified benchmark case in appData.benchmark
    const benchmarkMatch = checkBenchmarkPairMatch(activeTopoKey, qa, qb);

    if (safetyBox) {
      if (benchmarkMatch) {
        safetyBox.innerHTML = `
          <strong class="highlight-green">Verified Benchmark Result:</strong>
          This connection matches the official 60,000-shot evaluated baseline on ${friendlyArchName(activeTopoKey)}:
          Uncorrected Fidelity: <strong>${benchmarkMatch.noisy.toFixed(4)}</strong> &rarr;
          Protected Fidelity: <strong>${benchmarkMatch.protected.toFixed(4)}</strong>
          (<strong>${benchmarkMatch.yield.toFixed(2)}%</strong> Shot Survival).
        `;
      } else {
        safetyBox.innerHTML = `
          <strong class="text-warn">Scientific Scope:</strong>
          No measured fidelity result is available for this custom connection.
          This recommendation is based on routing metrics (SWAP count, native CX count, 2Q depth) only.
        `;
      }
    }
  }
}

// Actionable Topology Switcher Preserving Selected Target Pair
function switchTopologyPreservingPair(topoKey, qa, qb) {
  if (!topoKey || !TOPOLOGY_PRESETS[topoKey]) return;

  appData.activeTopologyKey = topoKey;
  appData.selectionStage = 0;
  resetRoutingInstructionText();

  // Update topology toolbar buttons active state
  document.querySelectorAll(".btn-topo").forEach(btn => {
    if (btn.getAttribute("data-topo") === topoKey) {
      btn.classList.add("active");
    } else {
      btn.classList.remove("active");
    }
  });

  const nameEl = document.getElementById("topo-info-name");
  if (nameEl) nameEl.innerText = friendlyArchName(topoKey);

  const note127 = document.getElementById("topo-127-short-note");
  if (note127) {
    if (topoKey === "heavy_hex_127") {
      note127.classList.add("active");
    } else {
      note127.classList.remove("active");
    }
  }

  // Preserve the current target pair
  appData.currentPair = [qa, qb];
  const numQubits = getTopologyNumQubits(topoKey);

  populateDropdowns(numQubits, qa, qb);
  updatePresetButtonsState();

  // Execute live routing and render updated path on new topology
  fetchLiveRouting(topoKey, qa, qb);

  // Smooth scroll user to visualizer canvas
  const visualizerEl = document.getElementById("sub-visualizer");
  if (visualizerEl) {
    visualizerEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }
}

function checkBenchmarkPairMatch(topoKey, qa, qb) {
  const presets = TOPOLOGY_PRESETS[topoKey];
  if (!presets || !presets.benchmark || topoKey === "heavy_hex_127") return null;

  const isMatch = (qa === presets.benchmark[0] && qb === presets.benchmark[1]) ||
                  (qa === presets.benchmark[1] && qb === presets.benchmark[0]);
  if (!isMatch) return null;

  const noisyCase = getBenchmarkCase(topoKey, "noisy");
  const protCase = getBenchmarkCase(topoKey, "protected");

  if (noisyCase && protCase) {
    return {
      noisy: noisyCase.bell_fidelity,
      protected: protCase.bell_fidelity,
      yield: protCase.survival_yield_percent || (protCase.survival_yield * 100)
    };
  }
  return null;
}

