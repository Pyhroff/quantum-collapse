"""Cascade engine: propagate failure through the dependency graph.

Model (V1 — deliberately simple and explainable):
  * A ``seed`` entity is compromised (e.g. its crypto is broken by a CRQC).
  * Failure flows along edge direction (provider -> dependent).
  * A node *resists* the cascade if it is sufficiently migrated to PQC, i.e.
    ``migration_pct >= resist_threshold``. A resistant node fails-safe and does
    NOT propagate failure onward.

The ``resist_threshold`` knob is what makes the migration-rate sensitivity
slider meaningful: lower it and more entities survive, containing the cascade.
"""

from collections import deque

import networkx as nx


def cascade(g: nx.DiGraph, seeds, resist_threshold: int = 100) -> set:
    """Return the set of failed nodes after compromising ``seeds``.

    ``resist_threshold`` = minimum migration_pct a node needs to survive an
    upstream failure. Default 100 means "only fully-migrated nodes survive".
    """
    failed = set(seeds)
    queue = deque(seeds)

    while queue:
        node = queue.popleft()
        for dependent in g.successors(node):
            if dependent in failed:
                continue
            if g.nodes[dependent]["migration_pct"] >= resist_threshold:
                continue  # migrated: survives and stops the cascade here
            failed.add(dependent)
            queue.append(dependent)
    return failed
