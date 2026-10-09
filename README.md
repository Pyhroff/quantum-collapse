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
  server.py        # FastAPI - /api/graph · /api/cascade · /api/sensitivity
  demo.py          # CLI demo, no server needed

frontend/
  index.html       # standalone - D3 v7 force graph + full control sidebar

docs/
  DESIGN.md        # documented assumptions behind every number
```

**Model limitations:** All coefficients and migration percentages are illustrative scenario parameters, not empirical forecasts or compliance assessments. The model is not a cryptographic implementation and does not estimate the date a CRQC will arrive. Standardized labels use ML-KEM (FIPS 203), ML-DSA (FIPS 204), and SLH-DSA (FIPS 205); legacy Kyber/Dilithium/SPHINCS+ labels are accepted for backwards-compatible scenarios. HQC is a selected candidate for future standardization, not a finalized FIPS standard in this model. See [the current NIST PQC standards status](https://csrc.nist.gov/Projects/Post-Quantum-Cryptography) and [NIST crypto-agility guidance](https://csrc.nist.gov/pubs/cswp/39/upd1/considerations-for-achieving-crypto-agility/final).\n\n**API safety:** The backend only allows configured browser origins; by default, serve `frontend/` locally (for example, `python -m http.server 8080`) and set `QUANTUM_COLLAPSE_ALLOWED_ORIGINS` if using another local origin. Do not expose the development server to an untrusted network.\n\n**Composite risk formula** (post-cascade):
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
