"""Seed topology for the Quantum Collapse world model.

Nodes are real-world infrastructure entities. A directed edge ``A -> B`` means
"B depends on A" (A provides trust / connectivity / service to B), so a failure
at A can cascade *downstream* to B.

All numbers here are ILLUSTRATIVE modelling assumptions, not measurements:
  - ``crypto``        : the dominant public-key primitive the entity relies on.
  - ``criticality``   : 1 (low) .. 5 (systemic) — societal harm if it fails.
  - ``migration_pct`` : 0..100 — share of systems already moved to PQC.

The quantum vulnerability of each primitive is modelled in ``risk.py`` and is
grounded in the public consensus behind NIST's PQC standards
(FIPS 203 ML-KEM / 204 ML-DSA / 205 SLH-DSA, 2024).
"""

import networkx as nx


def build_world() -> nx.DiGraph:
    """Return the seed dependency graph (~17 nodes)."""
    g = nx.DiGraph()

    # (name, sector, crypto, criticality, migration_pct)
    nodes = [
        ("GlobalCA",    "Certificate Authority", "RSA-2048",      5, 5),
        ("RegionalCA",  "Certificate Authority", "ECC-P256",      4, 10),
        ("GovPKI",      "Government PKI",         "RSA-4096",      5, 15),
        ("BankA",       "Banking",               "RSA-2048",      4, 20),
        ("BankB",       "Banking",               "RSA-2048",      4, 10),
        ("BankC",       "Banking",               "ECC-P256",      3, 25),
        ("CardNetwork", "Payment Network",       "RSA-2048",      5, 15),
        ("RTGS",        "Payment Network",       "RSA-4096",      5, 20),
        ("CloudX",      "Cloud Provider",        "ECC-P256",      5, 40),
        ("CloudY",      "Cloud Provider",        "Hybrid-Kyber",  5, 70),
        ("Telco1",      "Telecom",               "RSA-2048",      4, 10),
        ("Hospital1",   "Healthcare",            "RSA-2048",      4, 5),
        ("Emergency",   "Emergency Services",    "RSA-2048",      5, 5),
        ("TaxPortal",   "Government Service",    "RSA-2048",      3, 15),
        ("Exchange1",   "Crypto Exchange",       "ECC-secp256k1", 3, 0),
        ("PowerGrid",   "Power Grid",            "RSA-2048",      5, 10),
        ("Consumers",   "Consumers",             "TLS-client",    2, 0),
    ]
    for name, sector, crypto, crit, mig in nodes:
        g.add_node(name, sector=sector, crypto=crypto,
                   criticality=crit, migration_pct=mig)

    # edges: provider -> dependent  ("dependent relies on provider")
    edges = [
        ("GlobalCA", "BankA"), ("GlobalCA", "BankB"), ("GlobalCA", "CardNetwork"),
        ("GlobalCA", "CloudX"), ("GlobalCA", "Telco1"),
        ("RegionalCA", "BankC"), ("RegionalCA", "TaxPortal"), ("RegionalCA", "Hospital1"),
        ("GovPKI", "TaxPortal"), ("GovPKI", "Emergency"), ("GovPKI", "PowerGrid"),
        ("BankA", "CardNetwork"), ("BankB", "CardNetwork"), ("BankC", "RTGS"),
        ("CardNetwork", "Consumers"), ("RTGS", "BankA"), ("RTGS", "BankB"),
        ("CloudX", "Hospital1"), ("CloudX", "TaxPortal"), ("CloudX", "Exchange1"),
        ("CloudY", "Emergency"), ("CloudY", "PowerGrid"),
        ("Telco1", "Emergency"), ("Telco1", "Consumers"),
        ("Hospital1", "Emergency"),
        ("PowerGrid", "Hospital1"), ("PowerGrid", "Telco1"),
        ("Exchange1", "Consumers"),
    ]
    g.add_edges_from(edges)
    return g
