"""Deterministic cascade propagation over a directed dependency graph."""

from collections import deque
from collections.abc import Iterable

import networkx as nx


def cascade(g: nx.DiGraph, seeds: Iterable[str], resist_threshold: int = 100) -> set[str]:
    """Return failed nodes after compromising one or more seed nodes.

    Edges point provider -> dependent. A dependent survives and stops the
    cascade when its migration percentage meets the threshold. Seed nodes are
    considered compromised regardless of their own migration percentage.
    """
    if not isinstance(resist_threshold, int) or not 0 <= resist_threshold <= 100:
        raise ValueError("resist_threshold must be an integer between 0 and 100")

    seed_list = list(dict.fromkeys(seeds))
    if not seed_list:
        raise ValueError("at least one seed node is required")
    unknown = [node for node in seed_list if node not in g]
    if unknown:
        raise ValueError(f"unknown seed node(s): {unknown}")

    failed: set[str] = set(seed_list)
    queue = deque(seed_list)

    while queue:
        node = queue.popleft()
        for dependent in g.successors(node):
            if dependent in failed:
                continue
            migration = g.nodes[dependent].get("migration_pct")
            if not isinstance(migration, (int, float)) or not 0 <= migration <= 100:
                raise ValueError(
                    f"migration_pct for {dependent!r} must be between 0 and 100"
                )
            if migration >= resist_threshold:
                continue
            failed.add(dependent)
            queue.append(dependent)
    return failed
