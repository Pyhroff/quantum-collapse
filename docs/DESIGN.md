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

## Standards and model maintenance

Use standardized algorithm names in new scenario data: ML-KEM (FIPS 203), ML-DSA (FIPS 204), and SLH-DSA (FIPS 205). Legacy labels such as Kyber, Dilithium, and SPHINCS+ remain for backward compatibility only. HQC was selected for future standardization, but should not be described as a finalized FIPS standard until NIST publishes the final specification. The model's scores are illustrative parameters, not algorithm security proofs or real-world risk measurements.

The backend validates migration percentages, criticality, seed nodes, and thresholds; API outputs are sorted for reproducibility. Browser origins are allowlisted instead of using wildcard CORS.

## The line (NOT V1)

Neo4j, Postgres, GDP/economic engine, year-by-year timeline engine, AI policy
advisor, country simulation, auth/multi-user. When the five V1 boxes in the
README are checked, **freeze and ship.** Everything above is V2+.

## Next steps after V1 ships

1. Sensitivity sweep surfaced as a UI slider (migration rate -> nodes down, GDP-ish proxy).
2. React Flow front-end that animates the red cascade — the demo-video moment.
3. Bridge to Quantum OS: replace the hand-set "RSA broken" flag with a real
   resource-estimate gate (qubits + time to break RSA-2048, cf. Gidney–Ekerå).


## Monte Carlo sensitivity bands

`GET /api/monte-carlo` samples each node's base vulnerability and migration percentage from independent bounded uniform ranges around the configured values. Criticality is held fixed. The API reports the deterministic baseline, mean, population standard deviation, and p05/p50/p95 percentiles. These percentiles are **scenario sensitivity bands, not empirical confidence intervals**; no measured infrastructure distribution is available. A fixed seed and identical parameters reproduce the same output.

## PQC Scanner evidence bridge

`quantum_collapse.pqc_scanner_integration` consumes SARIF 2.1.0 emitted by PQC Scanner. It preserves file, line, algorithm, bucket, severity, and message as observed static-analysis evidence. It maps supported `quantum_broken` public-key findings to isolated scenario nodes and keeps classical weaknesses in the evidence summary rather than reclassifying them as quantum vulnerabilities. It does not infer runtime reachability or dependency edges. The migration percentage, severity-to-criticality mapping, and risk coefficients are scenario assumptions, and the resulting score is finding-weighted—not a systemic risk estimate.
