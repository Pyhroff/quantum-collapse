"""Bridge PQC Scanner SARIF findings into a transparent scenario model.

Static findings are observed source-code evidence. Migration, criticality, and
risk coefficients remain explicit model assumptions; dependency edges are never
invented from file paths or scanner output.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import networkx as nx

from .risk import global_risk, node_risk


def _map_algorithm(algorithm: str) -> str | None:
    value = algorithm.lower()
    if "rsa" in value:
        return "RSA"
    if "ecdsa" in value or "ed25519" in value or "ed448" in value or "ecc" in value or value in {"ec", "x25519", "x448"}:
        return "ECC-P256"
    if "ecdh" in value or "diffie-hellman" in value or value == "dh":
        return "DH"
    if "dsa" in value:
        return "DSA"
    return None


def sarif_to_scenario(payload: dict, *, migration_pct: float = 0.0) -> dict:
    """Validate SARIF 2.1.0 and return evidence plus a finding-weighted scenario."""
    if not isinstance(payload, dict) or payload.get("version") != "2.1.0":
        raise ValueError("input must be a SARIF 2.1.0 object")
    if isinstance(migration_pct, bool) or not isinstance(migration_pct, (int, float)) or not math.isfinite(migration_pct) or not 0 <= migration_pct <= 100:
        raise ValueError("migration_pct must be a finite number between 0 and 100")
    runs = payload.get("runs")
    if not isinstance(runs, list):
        raise ValueError("SARIF runs must be a list")

    evidence = []
    by_bucket = {"quantum_broken": 0, "classically_broken": 0, "quantum_weakened": 0, "other": 0}
    graph = nx.DiGraph()
    unmapped = []
    seen = set()
    index = 0

    for run in runs:
        if not isinstance(run, dict):
            continue
        results = run.get("results", [])
        if not isinstance(results, list):
            raise ValueError("each SARIF run results field must be a list")
        for result in results:
            if not isinstance(result, dict):
                continue
            props = result.get("properties") or {}
            bucket = props.get("bucket", "other")
            if bucket not in by_bucket:
                bucket = "other"
            locations = result.get("locations") or []
            physical = (locations[0].get("physicalLocation") or {}) if locations else {}
            uri = (physical.get("artifactLocation") or {}).get("uri", "")
            line = (physical.get("region") or {}).get("startLine")
            algorithm = str(props.get("algorithm") or result.get("ruleId") or "unknown")
            level = result.get("level", "note")
            identity = (uri, line, algorithm, bucket)
            if identity in seen:
                continue
            seen.add(identity)
            by_bucket[bucket] += 1
            record = {
                "file": uri,
                "line": line,
                "algorithm": algorithm,
                "bucket": bucket,
                "severity": level,
                "message": (result.get("message") or {}).get("text", ""),
                "evidence_type": "static_source_code_finding",
            }
            evidence.append(record)

            # Only Shor-vulnerable public-key findings become quantum-risk nodes.
            # Classical hash/cipher findings stay in evidence and are not relabelled
            # as quantum vulnerabilities.
            if bucket != "quantum_broken":
                continue
            crypto = _map_algorithm(algorithm)
            if crypto is None:
                unmapped.append({"file": uri, "line": line, "algorithm": algorithm})
                continue
            index += 1
            criticality = {"error": 5, "warning": 3, "note": 1}.get(level, 1)
            node_id = f"finding-{index:04d}"
            graph.add_node(
                node_id,
                sector="Scanned source finding",
                crypto=crypto,
                criticality=criticality,
                migration_pct=float(migration_pct),
                evidence_file=uri,
                evidence_line=line,
                evidence_algorithm=algorithm,
            )

    scenario_risk = global_risk(graph) if graph.number_of_nodes() else None
    return {
        "schema_version": "1.0",
        "source": {"format": "SARIF", "version": "2.1.0", "tool": "pqc-scanner"},
        "observed_evidence": {
            "finding_count": len(evidence),
            "by_bucket": by_bucket,
            "findings": evidence,
        },
        "modeled_scenario": {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "finding_weighted_risk_score": scenario_risk,
            "nodes": [
                {
                    "id": node,
                    **graph.nodes[node],
                    "modeled_risk": node_risk(graph, node),
                }
                for node in sorted(graph.nodes)
            ],
            "unmapped_quantum_findings": unmapped,
            "assumptions": {
                "migration_pct": float(migration_pct),
                "criticality_by_sarif_level": {"error": 5, "warning": 3, "note": 1},
                "dependency_edges": "none inferred; scanner output does not establish dependency topology",
                "risk_score": "mean of modeled risk for mapped quantum-broken findings only",
                "risk_coefficients": "illustrative values from quantum_collapse.risk",
                "limitations": "static findings do not prove runtime reachability or deployed usage",
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Map PQC Scanner SARIF evidence into an explicitly assumed Quantum Collapse scenario.")
    parser.add_argument("sarif", type=Path, help="SARIF 2.1.0 report from pqc-scan")
    parser.add_argument("--migration-pct", type=float, default=0.0, help="Assumed migration percentage for scenario nodes (0..100)")
    parser.add_argument("--output", type=Path, help="Write JSON output here; stdout if omitted")
    args = parser.parse_args()
    payload = json.loads(args.sarif.read_text(encoding="utf-8"))
    result = sarif_to_scenario(payload, migration_pct=args.migration_pct)
    rendered = json.dumps(result, indent=2)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
