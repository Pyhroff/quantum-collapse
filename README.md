# Quantum Collapse

A scenario simulator for systemic risk during the post-quantum transition:
*what breaks, and in what order, when a cryptographically-relevant quantum
computer (CRQC) defeats RSA/ECC across interdependent infrastructure?*

It is **not** a forecast and **not** a Shor's-algorithm demo. It is a tool for
exploring how failure cascades through a dependency graph under stated,
documented assumptions — and how fast post-quantum migration contains it.

> Part 1 of a two-project arc. Part 2 (**Quantum OS**) models *how* RSA dies —
> fault-tolerant error correction (Stim + PyMatching) and a real RSA-2048
> resource estimate. Collapse asks "what breaks when RSA dies"; Quantum OS
> answers "how and when". Same thesis, two repos.

## Run it

```bash
cd backend
pip install -r requirements.txt
python demo.py
```

Compromises a Certificate Authority, propagates the failure downstream, prints
a migration-rate sensitivity sweep, and writes `cascade.png` (failed entities
in red).

## V1 scope — definition of done

V1 is **done** when these five things work end-to-end, and not before:

- [x] ~17–20 node infrastructure dependency graph (NetworkX)
- [x] Cascade propagation engine (failure flows along dependencies)
- [x] Risk engine from documented crypto-vulnerability assumptions
- [ ] Migration-rate **sensitivity** analysis surfaced in the UI
- [ ] Interactive visualization (React Flow / D3) — animate the cascade

### Explicitly NOT V1
Neo4j · Postgres · economic/GDP engine · timeline (2026→2045) engine ·
AI policy advisor · country-level simulation · multi-user. These come *after*
V1 ships, or never.

## Why the numbers aren't made up
Crypto vulnerabilities are keyed to the public consensus behind NIST's PQC
standards (FIPS 203/204/205, 2024). They are **illustrative knobs**, and the
project's whole point is sensitivity analysis *over* those knobs rather than
false precision. See [docs/DESIGN.md](docs/DESIGN.md).
