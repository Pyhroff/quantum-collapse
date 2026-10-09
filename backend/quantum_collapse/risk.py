"""Transparent risk scoring from explicitly illustrative assumptions.

These scores are scenario parameters, not cryptographic security measurements.
FIPS 203/204/205 define ML-KEM, ML-DSA, and SLH-DSA respectively. Legacy
Kyber/Dilithium/SPHINCS+ labels remain accepted for existing graph data, but
new scenarios should use the standardized names. HQC is a selected candidate
for future standardization, not a finalized FIPS standard as of this model's
last standards review.
"""

QUANTUM_VULNERABILITY: dict[str, float] = {
    # Classical public-key cryptography susceptible to Shor's algorithm.
    "RSA-1024": 1.0,
    "RSA-2048": 1.0,
    "RSA-3072": 1.0,
    "RSA-4096": 0.95,
    "RSA": 1.0,
    "ECC-P256": 1.0,
    "ECC-P384": 1.0,
    "ECC-secp256k1": 1.0,
    "ECDSA": 1.0,
    "ECDH": 1.0,
    "DH": 1.0,
    "DSA": 1.0,
    # TLS exposure is a scenario assumption; actual risk depends on negotiated
    # key exchange, certificates, endpoints, and the full protocol deployment.
    "TLS-client": 0.9,
    # Symmetric/hash examples: Grover is a quadratic speedup, not a total break.
    "AES-128": 0.35,
    "AES-256": 0.1,
    "SHA-256": 0.1,
    # Hybrid models retain a classical component and are not zero-risk.
    "Hybrid-ML-KEM-768": 0.15,
    "Hybrid-Kyber": 0.15,  # legacy alias
    # Standardized PQC families (risk score remains an illustrative model input).
    "ML-KEM-512": 0.0,
    "ML-KEM-768": 0.0,
    "ML-KEM-1024": 0.0,
    "ML-KEM": 0.0,
    "Kyber": 0.0,  # legacy alias
    "ML-DSA-44": 0.0,
    "ML-DSA-65": 0.0,
    "ML-DSA-87": 0.0,
    "ML-DSA": 0.0,
    "Dilithium": 0.0,  # legacy alias
    "SLH-DSA": 0.0,
    "SPHINCS+": 0.0,  # legacy alias
    # Candidate label only; do not present this as a finalized standard.
    "HQC-candidate": 0.0,
}

_UNKNOWN_CRYPTO_VULNERABILITY = 0.8


def node_vulnerability(g, node) -> float:
    """Return modeled exposure after migration, validating input ranges."""
    crypto = g.nodes[node]["crypto"]
    migration = g.nodes[node]["migration_pct"]
    if not isinstance(migration, (int, float)) or not 0 <= migration <= 100:
        raise ValueError(f"migration_pct for {node!r} must be between 0 and 100")
    base = QUANTUM_VULNERABILITY.get(crypto, _UNKNOWN_CRYPTO_VULNERABILITY)
    return base * (1.0 - migration / 100.0)


def node_risk(g, node) -> float:
    """Criticality (1..5, normalized) times effective vulnerability."""
    crit = g.nodes[node]["criticality"]
    if not isinstance(crit, (int, float)) or not 1 <= crit <= 5:
        raise ValueError(f"criticality for {node!r} must be between 1 and 5")
    return round((crit / 5.0) * node_vulnerability(g, node), 3)


def global_risk(g) -> float:
    """Mean node risk; an empty graph has zero modeled risk."""
    scores = [node_risk(g, n) for n in g.nodes]
    return round(sum(scores) / len(scores), 3) if scores else 0.0
