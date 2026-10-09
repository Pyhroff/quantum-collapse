# Quantum Collapse

[![License: MIT](https://img.shields.io/badge/License-MIT-violet.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white)](backend/requirements.txt)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi&logoColor=white)](backend/requirements.txt)
[![D3.js](https://img.shields.io/badge/D3.js-v7-f9a03c?logo=d3.js&logoColor=white)](frontend/index.html)

A scenario simulator for systemic risk during the post-quantum transition:
*what breaks, and in what order, when a cryptographically-relevant quantum
computer (CRQC) defeats RSA/ECC across interdependent infrastructure?*

It is **not** a forecast. It is a tool for exploring how failure cascades through
a dependency graph under stated, documented assumptions - and how fast
post-quantum migration contains the damage.

> **Two-project arc.**
> Quantum Collapse asks *"what breaks when CRQC arrives?"*
> [QEC Lab](https://github.com/Pyhroff/qec-lab) answers *"what does a fault-tolerant quantum computer actually need to run Shor's?"*

---

## Features

- **17-node infrastructure dependency graph** - Certificate Authorities, banks, payment networks, cloud providers, telcos, hospitals, emergency services
- **BFS cascade propagation** - failure flows downstream; nodes survive only if their PQC migration % clears the threshold
- **Staggered animation** - cascade unfolds level-by-level with CSS keyframe animations (no rAF dependency)
- **Migration sensitivity analysis** - sweep 0 → 100 % migration rate and watch the failure count curve
- **Monte Carlo risk bands** - seeded simulations report p05/p50/p95 and dispersion under explicit bounded uncertainty assumptions
- **PQC Scanner bridge** - import SARIF 2.1.0 findings into a separate finding-weighted scenario without inventing dependency edges
- **Mosca's Inequality calculator** - interactive X/Y/Z sliders with live "LATE BY N YEARS" verdict
- **Cascade timeline** - per-level failure sequence rendered after each run
- **4 scenario presets** - Tier-1 CA, Dual CA, Cloud Cascade, Payment Collapse
- **Risk heat map toggle** - recolor nodes by individual risk score instead of sector

---

## Architecture

```
backend/
  quantum_collapse/
    topology.py    # 17-node NetworkX DiGraph with crypto + criticality metadata
    cascade.py     # BFS propagation engine
    risk.py        # per-node risk scoring from crypto-vulnerability assumptions
    uncertainty.py # seeded Monte Carlo sensitivity percentiles
    pqc_scanner_integration.py # SARIF evidence-to-scenario bridge
  server.py        # FastAPI - /api/graph · /api/cascade · /api/sensitivity · /api/monte-carlo
  demo.py          # CLI demo, no server needed

frontend/
  index.html       # standalone - D3 v7 force graph + full control sidebar

docs/
  DESIGN.md        # documented assumptions behind every number
```

**Model limitations:** All coefficients and migration percentages are illustrative scenario parameters, not empirical forecasts or compliance assessments. The model is not a cryptographic implementation and does not estimate the date a CRQC will arrive. Standardized labels use ML-KEM (FIPS 203), ML-DSA (FIPS 204), and SLH-DSA (FIPS 205); legacy Kyber/Dilithium/SPHINCS+ labels are accepted for backwards-compatible scenarios. HQC is a selected candidate for future standardization, not a finalized FIPS standard in this model. See [the current NIST PQC standards status](https://csrc.nist.gov/Projects/Post-Quantum-Cryptography) and [NIST crypto-agility guidance](https://csrc.nist.gov/pubs/cswp/39/upd1/considerations-for-achieving-crypto-agility/final).

**API safety:** The backend only allows configured browser origins; by default, serve `frontend/` locally (for example, `python -m http.server 8080`) and set `QUANTUM_COLLAPSE_ALLOWED_ORIGINS` if using another local origin. Do not expose the development server to an untrusted network.

**Composite risk formula** (post-cascade):
- Failed node contributes `criticality / 5` (full crypto exposure)
- Survived node contributes its pre-computed `risk` score

---

## Run it

**Interactive dashboard**

```bash
cd backend
pip install -r requirements.txt
uvicorn server:app --reload
```

In a second terminal from the repository root, serve the frontend with `python -m http.server 8080`, then open `http://localhost:8080/frontend/` in your browser. The page connects to `http://localhost:8000`. The API allows these local origins by default; set `QUANTUM_COLLAPSE_ALLOWED_ORIGINS` if you choose another origin. No frontend build step is needed.

**CLI demo** (no server needed)

```bash
cd backend
python demo.py
```

Compromises GlobalCA, prints a sensitivity sweep to stdout, writes `cascade.png`.

**Monte Carlo API:** `GET /api/monte-carlo?trials=1000&seed=2026&migration_uncertainty_pp=10&vulnerability_uncertainty=0.1` returns reproducible mean/stddev and p05/p50/p95 scenario sensitivity percentiles. These are **not empirical confidence intervals**: the inputs are bounded uniform perturbations around illustrative assumptions.

**Connect PQC Scanner findings:** generate a SARIF report with `pqc-scan scan /path/to/source --format sarif --output findings.sarif`, then from `backend/` run:

```bash
python -m quantum_collapse.pqc_scanner_integration /path/to/findings.sarif --migration-pct 0 --output scenario.json
```

The JSON keeps static source findings in `observed_evidence` and model-derived values in `modeled_scenario`. Only mapped quantum-broken findings become risk nodes; classically broken findings remain separate evidence. No dependency edges are inferred, so the result is a finding-weighted scenario—not a systemic-risk forecast. Migration percentage and criticality mapping are explicit assumptions.

---

## Decision thresholds

| Score | Colour | Meaning |
|-------|--------|---------|
| < 0.30 | green | low systemic exposure |
| 0.30 – 0.59 | amber | moderate - migration urgency increasing |
| ≥ 0.60 | red | critical - cascade probable under partial CRQC capability |

---

## Why the numbers aren't made up

Crypto vulnerabilities are keyed to the public consensus behind NIST's PQC
standards (FIPS 203/204/205, 2024). Migration percentages and criticality scores
are **illustrative knobs** - the project's point is sensitivity analysis *over*
those knobs, not false precision. See [docs/DESIGN.md](docs/DESIGN.md).

---

## License

[MIT](LICENSE) © 2026 Pyhroff


## Reproducibility and interpretation

The Monte Carlo endpoint is deterministic for a fixed graph, parameter set, and seed. Its percentiles summarize the specified model perturbations only; they do not quantify real-world uncertainty without empirical calibration data. Record the seed and assumptions when comparing runs.


## Reproducible migration sensitivity experiment

From the repository root:

```bash
PYTHONPATH=backend python -m quantum_collapse.scenario_sweep \
  --migration-rates 0,25,50,75,100 \
  --trials 1000 --seed 2026 --output migration-sweep.json
```

The JSON manifest captures the revision, environment, migration-rate grid, random seeds, trial count, uncertainty assumptions, runtime, mean/standard deviation, and p05/p50/p95 bands. The built-in 17-node topology and all risk coefficients remain illustrative. These bands quantify sensitivity to assumed inputs; they are not empirical confidence intervals or measured infrastructure risk.


### Versioned scanner integration contract

The bridge output contract is defined in `docs/schemas/pqc-scenario-bridge-output-1.0.schema.json` and validated in CI. It deliberately separates `observed_evidence` (static scanner findings) from `modeled_scenario` (risk nodes generated using explicit assumptions). No dependency edges are inferred from file paths. Bump the schema version when changing the contract incompatibly.


### CI migration-sensitivity snapshot

The full 5-point grid ran with 1,000 trials per migration rate, base seed 2026, migration uncertainty ±10 percentage points, and absolute vulnerability-score uncertainty ±0.1.

| Assumed migration | Baseline score | Simulated mean | Std. dev. | p05–p95 |
|---:|---:|---:|---:|---:|
| 0% | 0.777 | 0.7054 | 0.0085 | 0.6911–0.7193 |
| 25% | 0.583 | 0.5575 | 0.0117 | 0.5383–0.5757 |
| 50% | 0.389 | 0.3713 | 0.0119 | 0.3523–0.3903 |
| 75% | 0.194 | 0.1856 | 0.0109 | 0.1675–0.2033 |
| 100% | 0.000 | 0.0370 | 0.0054 | 0.0283–0.0458 |

These are reproducible sensitivity results for the illustrative 17-node model, not observed infrastructure risk. At 100% baseline migration, the sampled mean remains above zero because the experiment explicitly perturbs migration by ±10 percentage points; the baseline and simulated mean answer different questions.
