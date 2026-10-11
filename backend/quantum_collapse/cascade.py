"""Cascade engine with bounded input validation and deterministic propagation."""
from collections import deque
import networkx as nx


def cascade(g: nx.DiGraph, seeds, resist_threshold: int = 100) -> set:
    """Return failed nodes; migration >= threshold resists upstream failure."""
    if not isinstance(resist_threshold, int) or isinstance(resist_threshold, bool):
        raise ValueError("resist_threshold must be an integer from 0 to 100")
    if not 0 <= resist_threshold <= 100:
        raise ValueError("resist_threshold must be between 0 and 100")

    seed_list = list(dict.fromkeys(seeds))
    unknown = [seed for seed in seed_list if seed not in g]
    if unknown:
        raise ValueError(f"Unknown seed node(s): {', '.join(map(str, unknown))}")

    failed = set(seed_list)
    queue = deque(seed_list)
    while queue:
        node = queue.popleft()
        for dependent in g.successors(node):
            if dependent in failed:
                continue
            if g.nodes[dependent].get("migration_pct", 0) >= resist_threshold:
                continue
            failed.add(dependent)
            queue.append(dependent)
    return failed
