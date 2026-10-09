"""Regression tests for the quantum-collapse model.

These tests validate implementation invariants, not real-world probability
estimates. The scenario coefficients remain illustrative assumptions.
"""

import networkx as nx
import pytest

from backend.quantum_collapse.cascade import cascade
from backend.quantum_collapse.risk import global_risk, node_risk, node_vulnerability
from backend.quantum_collapse.topology import build_world
from backend.quantum_collapse.uncertainty import monte_carlo_risk
from backend.quantum_collapse.pqc_scanner_integration import sarif_to_scenario


def test_seed_failure_propagates_downstream_and_not_upstream():
    graph = nx.DiGraph()
    graph.add_node("provider", migration_pct=0, crypto="RSA-2048", criticality=5)
    graph.add_node("dependent", migration_pct=0, crypto="RSA-2048", criticality=4)
    graph.add_node("unrelated", migration_pct=0, crypto="RSA-2048", criticality=1)
    graph.add_edge("provider", "dependent")

    assert cascade(graph, ["provider"], 100) == {"provider", "dependent"}


def test_migrated_dependent_stops_cascade():
    graph = nx.DiGraph()
    graph.add_node("seed", migration_pct=0, crypto="RSA-2048", criticality=5)
    graph.add_node("migrated", migration_pct=100, crypto="ML-KEM-768", criticality=3)
    graph.add_node("downstream", migration_pct=0, crypto="RSA-2048", criticality=2)
    graph.add_edges_from([("seed", "migrated"), ("migrated", "downstream")])

    assert cascade(graph, ["seed"], 100) == {"seed"}


@pytest.mark.parametrize("threshold", [-1, 101, 1.5])
def test_invalid_resistance_threshold_rejected(threshold):
    graph = build_world()
    with pytest.raises(ValueError):
        cascade(graph, ["GlobalCA"], threshold)


@pytest.mark.parametrize("seeds", [[], ["not-a-node"]])
def test_invalid_seeds_rejected(seeds):
    with pytest.raises(ValueError):
        cascade(build_world(), seeds)


def test_standardized_pqc_labels_and_legacy_aliases_have_expected_model_score():
    graph = nx.DiGraph()
    for i, label in enumerate(("ML-KEM-768", "ML-DSA-65", "SLH-DSA", "Kyber", "Dilithium", "SPHINCS+")):
        graph.add_node(str(i), crypto=label, migration_pct=0, criticality=5)
    assert all(node_vulnerability(graph, node) == 0.0 for node in graph.nodes)


def test_hybrid_is_not_scored_as_zero_risk():
    graph = nx.DiGraph()
    graph.add_node("hybrid", crypto="Hybrid-ML-KEM-768", migration_pct=0, criticality=5)
    assert node_vulnerability(graph, "hybrid") > 0


def test_invalid_migration_and_criticality_rejected():
    graph = nx.DiGraph()
    graph.add_node("bad", crypto="RSA-2048", migration_pct=101, criticality=5)
    with pytest.raises(ValueError):
        node_vulnerability(graph, "bad")
    graph.nodes["bad"]["migration_pct"] = 0
    graph.nodes["bad"]["criticality"] = 0
    with pytest.raises(ValueError):
        node_risk(graph, "bad")


def test_empty_graph_global_risk_is_zero():
    assert global_risk(nx.DiGraph()) == 0.0


def test_seed_topology_is_valid_and_risk_is_bounded():
    graph = build_world()
    assert graph.number_of_nodes() == 17
    assert graph.number_of_edges() > 0
    risk = global_risk(graph)
    assert 0 <= risk <= 1



def test_monte_carlo_bands_are_reproducible_and_ordered():
    graph = build_world()
    first = monte_carlo_risk(graph, trials=300, seed=2026)
    second = monte_carlo_risk(graph, trials=300, seed=2026)
    assert first == second
    assert first["p05"] <= first["p50"] <= first["p95"]
    assert first["minimum"] <= first["mean"] <= first["maximum"]
    assert 0 <= first["p05"] <= first["p95"] <= 1
    assert first["band_type"] == "scenario_sensitivity_percentiles_not_empirical_confidence_interval"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"trials": 99},
        {"trials": 10001},
        {"trials": True},
        {"migration_uncertainty_pp": 101},
        {"vulnerability_uncertainty": -0.1},
        {"vulnerability_uncertainty": float("nan")},
    ],
)
def test_monte_carlo_rejects_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        monte_carlo_risk(build_world(), **kwargs)


def test_empty_graph_monte_carlo_is_reproducibly_zero():
    result = monte_carlo_risk(nx.DiGraph(), trials=100, seed=7)
    assert result["baseline_risk"] == 0.0
    assert result["p05"] == result["p95"] == 0.0


def test_sarif_bridge_separates_observed_findings_from_scenario_assumptions():
    sarif = {
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "pqc-scanner"}},
            "results": [
                {
                    "ruleId": "pqc.quantum_broken.rsa",
                    "level": "error",
                    "locations": [{"physicalLocation": {"artifactLocation": {"uri": "src/crypto.py"}, "region": {"startLine": 8}}}],
                    "properties": {"bucket": "quantum_broken", "algorithm": "RSA"},
                    "message": {"text": "RSA detected"},
                },
                {
                    "ruleId": "pqc.classically_broken.md5",
                    "level": "warning",
                    "locations": [{"physicalLocation": {"artifactLocation": {"uri": "src/hash.py"}, "region": {"startLine": 4}}}],
                    "properties": {"bucket": "classically_broken", "algorithm": "MD5"},
                    "message": {"text": "MD5 detected"},
                },
            ],
        }],
    }
    result = sarif_to_scenario(sarif, migration_pct=25)
    assert result["observed_evidence"]["finding_count"] == 2
    assert result["observed_evidence"]["by_bucket"]["quantum_broken"] == 1
    assert result["observed_evidence"]["by_bucket"]["classically_broken"] == 1
    scenario = result["modeled_scenario"]
    assert scenario["node_count"] == 1
    assert scenario["edge_count"] == 0
    assert scenario["nodes"][0]["evidence_file"] == "src/crypto.py"
    assert scenario["nodes"][0]["migration_pct"] == 25.0
    assert scenario["assumptions"]["dependency_edges"].startswith("none inferred")
    assert "not prove runtime reachability" in scenario["assumptions"]["limitations"]


@pytest.mark.parametrize("sarif,migration", [({}, 0), ({"version": "1.0.0", "runs": []}, 0), ({"version": "2.1.0", "runs": []}, 101)])
def test_sarif_bridge_rejects_invalid_inputs(sarif, migration):
    with pytest.raises(ValueError):
        sarif_to_scenario(sarif, migration_pct=migration)


def test_monte_carlo_and_sarif_scenario_risk_use_bounded_model_inputs():
    graph = nx.DiGraph()
    graph.add_node("rsa", crypto="RSA-2048", migration_pct=0, criticality=5)
    result = monte_carlo_risk(
        graph, trials=200, seed=5,
        migration_uncertainty_pp=0, vulnerability_uncertainty=0,
    )
    assert result["p05"] == pytest.approx(1.0)
    assert result["p95"] == pytest.approx(1.0)



def test_sarif_duplicate_results_do_not_inflate_bucket_counts():
    finding = {
        "ruleId": "pqc.quantum_broken.rsa",
        "level": "error",
        "locations": [{
            "physicalLocation": {
                "artifactLocation": {"uri": "src/crypto.py"},
                "region": {"startLine": 8},
            }
        }],
        "properties": {"bucket": "quantum_broken", "algorithm": "RSA"},
        "message": {"text": "RSA detected"},
    }
    result = sarif_to_scenario({
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "pqc-scanner"}}, "results": [finding, finding]}],
    })
    evidence = result["observed_evidence"]
    assert evidence["finding_count"] == 1
    assert sum(evidence["by_bucket"].values()) == evidence["finding_count"]



def test_migration_sweep_is_reproducible_and_records_assumptions():
    from backend.quantum_collapse.scenario_sweep import build_sweep_report

    kwargs = {
        "migration_rates": [0, 50, 100],
        "trials": 100,
        "seed": 20261009,
        "code_revision": "test-revision",
    }
    first = build_sweep_report(**kwargs)
    second = build_sweep_report(**kwargs)
    assert first["schema_version"] == "1.0"
    assert first["code_revision"] == "test-revision"
    assert first["measurement_type"] == "scenario_sensitivity_not_empirical_estimate"
    assert first["result_count"] == 3
    assert first["results"] == second["results"]
    assert all(row["trials"] == 100 for row in first["results"])
    assert all(row["p05"] <= row["p50"] <= row["p95"] for row in first["results"])
    assert all(row["stddev"] >= 0 for row in first["results"])


def test_migration_sweep_rejects_empty_or_out_of_range_grid():
    from backend.quantum_collapse.scenario_sweep import build_sweep_report

    with pytest.raises(ValueError):
        build_sweep_report(migration_rates=[])
    with pytest.raises(ValueError):
        build_sweep_report(migration_rates=[101], trials=100)
