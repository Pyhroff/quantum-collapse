import networkx as nx
import pytest
from quantum_collapse.cascade import cascade


def sample_graph():
    graph = nx.DiGraph()
    graph.add_node("provider", migration_pct=0)
    graph.add_node("dependent", migration_pct=0)
    graph.add_node("resistant", migration_pct=100)
    graph.add_edges_from([("provider", "dependent"), ("dependent", "resistant")])
    return graph


def test_cascade_stops_at_resistant_node():
    assert cascade(sample_graph(), ["provider"], 100) == {"provider", "dependent"}


def test_threshold_zero_means_all_dependents_resist():
    assert cascade(sample_graph(), ["provider"], 0) == {"provider"}


@pytest.mark.parametrize("threshold", [-1, 101, 2.5, True])
def test_rejects_invalid_threshold(threshold):
    with pytest.raises(ValueError):
        cascade(sample_graph(), ["provider"], threshold)


def test_rejects_unknown_seed():
    with pytest.raises(ValueError, match="Unknown seed"):
        cascade(sample_graph(), ["missing"])


def test_duplicate_seeds_are_deduplicated():
    assert cascade(sample_graph(), ["provider", "provider"]) == {"provider", "dependent"}


def test_empty_seed_list_returns_no_failures():
    assert cascade(sample_graph(), []) == set()
