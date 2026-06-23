# Quantum Collapse — Design (V1)

One page. The model, the assumptions, and the line we don't cross in V1.

## Model

**World** = a directed graph of infrastructure entities. Edge `A -> B` means
"B depends on A". Failure flows along edge direction.

**Node attributes** (illustrative): `sector`, `crypto` (dominant public-key
primitive), `criticality` 1–5, `migration_pct` 0–100.

**Cascade rule.** Compromise a seed node; failure propagates to every
dependent (BFS over descendants). A node *resists* if
`migration_pct >= resist_threshold` — it fails-safe and stops the cascade
through itself. The `resist_threshold` is the sensitivity knob.

**Risk.** `node_risk = (criticality / 5) x base_vulnerability(crypto) x (1 - migration)`.
Global risk = mean over nodes. A single headline number that moves as you
change assumptions.

## Honesty about the numbers

Crypto vulnerabilities (`risk.QUANTUM_VULNERABILITY`) are keyed to the public
consensus behind NIST's PQC standards (FIPS 203 ML-KEM / 204 ML-DSA /
205 SLH-DSA, 2024): Shor breaks RSA/ECC (~1.0); Grover only dents AES-256
(~0.1); lattice/hash PQC (~0.0). Topology numbers are hand-set placeholders.

These are **knobs, not measurements.** The deliverable is *sensitivity
analysis* — "under these assumptions, these outcomes emerge", and how
sensitive the outcome is to each input — not a claim about the real world.
That framing is what makes the project defensible in an interview.

Timeline grounding for later: Mosca's inequality (`X + Y > Z`) for *when*
migration must finish relative to CRQC arrival.

## The line (NOT V1)

Neo4j, Postgres, GDP/economic engine, year-by-year timeline engine, AI policy
advisor, country simulation, auth/multi-user. When the five V1 boxes in the
README are checked, **freeze and ship.** Everything above is V2+.

## Next steps after V1 ships

1. Sensitivity sweep surfaced as a UI slider (migration rate -> nodes down, GDP-ish proxy).
2. React Flow front-end that animates the red cascade — the demo-video moment.
3. Bridge to Quantum OS: replace the hand-set "RSA broken" flag with a real
   resource-estimate gate (qubits + time to break RSA-2048, cf. Gidney–Ekerå).
