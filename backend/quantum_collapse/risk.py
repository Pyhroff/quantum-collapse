"""Risk scoring from documented (illustrative) assumptions.

``QUANTUM_VULNERABILITY`` is each primitive's breakability under a
cryptographically-relevant quantum computer (CRQC). These are modelling
assumptions grounded in the public consensus behind NIST's PQC programme
(FIPS 203 ML-KEM / 204 ML-DSA / 205 SLH-DSA, 2024):

  * RSA / ECC  -> ~1.0  (Shor's algorithm breaks them outright)
  * AES-256    -> ~0.1  (Grover only halves the security margin; still safe)
  * Kyber / Dilithium / SPHINCS+ -> ~0.0  (designed to resist quantum attack)

Every number here is a knob to be *justified and varied*, not a measured fact.
The project's value is sensitivity analysis over these knobs, not false
precision. See docs/DESIGN.md.
"""

QUANTUM_VULNERABILITY = {
    "RSA-1024":       1.0,
    "RSA-2048":       1.0,
    "RSA-4096":       0.95,
    "ECC-P256":       1.0,
    "ECC-secp256k1":  1.0,
    "TLS-client":     0.9,   # depends on negotiated suite; assume legacy
    "AES-256":        0.1,
    "Hybrid-Kyber":   0.15,  # classical half breakable, PQC half safe
    "Kyber":          0.0,
    "Dilithium":      0.0,
}


def node_vulnerability(g, node) -> float:
    """Effective vulnerability after migration buys down exposure."""
    base = QUANTUM_VULNERABILITY.get(g.nodes[node]["crypto"], 0.8)
    migration = g.nodes[node]["migration_pct"] / 100.0
    return base * (1.0 - migration)


def node_risk(g, node) -> float:
    """criticality (normalised) x effective vulnerability, in [0, 1]."""
    crit = g.nodes[node]["criticality"] / 5.0
    return round(crit * node_vulnerability(g, node), 3)


def global_risk(g) -> float:
    """Mean node risk across the world — a single headline number."""
    scores = [node_risk(g, n) for n in g.nodes]
    return round(sum(scores) / len(scores), 3)
