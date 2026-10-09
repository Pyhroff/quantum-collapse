"""Regression tests for the quantum-collapse model.

These tests validate implementation invariants, not real-world probability
estimates. The scenario coefficients remain illustrative assumptions.
"""

import networkx as nx
import pytest

from backend.quantum_collapse.cascade import cascade
from backend.quantum_collapse.risk import global_risk, node_risk, node_vulnerability
from backend.quantum_collapse.topology import build_world


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
