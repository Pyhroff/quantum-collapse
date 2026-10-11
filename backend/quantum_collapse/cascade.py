"""Deterministic cascade propagation with validated scenario inputs."""
from collections import deque
import math
from collections.abc import Iterable

import networkx as nx


def cascade(g: nx.DiGraph, seeds: Iterable[str], resist_threshold: int = 100) -> set[str]:
    """Return failed nodes; migration >= threshold resists upstream failure."""
    if isinstance(resist_threshold, bool) or not isinstance(resist_threshold, int) or not 0 <= resist_threshold <= 100:
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
        for dependent in sorted(g.successors(node)):
            if dependent in failed:
                continue
            migration = g.nodes[dependent].get("migration_pct", 0)
            if isinstance(migration, bool) or not isinstance(migration, (int, float)) or not math.isfinite(migration) or not 0 <= migration <= 100:
                raise ValueError(f"migration_pct for {dependent!r} must be a finite number between 0 and 100")
            if migration >= resist_threshold:
                continue
            failed.add(dependent)
            queue.append(dependent)
    return failed
