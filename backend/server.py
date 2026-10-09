"""Local API for the Quantum Collapse scenario simulator.

This is an educational model, not an operational risk oracle. Bind locally and
configure allowed browser origins explicitly before exposing it on a network.
"""

import os
from collections import deque

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from quantum_collapse.cascade import cascade as _cascade
from quantum_collapse.risk import global_risk, node_risk
from quantum_collapse.topology import build_world
from quantum_collapse.uncertainty import monte_carlo_risk

app = FastAPI(title="Quantum Collapse", version="1.1.0")
_allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "QUANTUM_COLLAPSE_ALLOWED_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

_g = build_world()


@app.get("/api/graph")
def get_graph():
    nodes = [
        {
            "id": n,
            "sector": _g.nodes[n]["sector"],
            "crypto": _g.nodes[n]["crypto"],
            "criticality": _g.nodes[n]["criticality"],
            "migration_pct": _g.nodes[n]["migration_pct"],
            "risk": node_risk(_g, n),
        }
        for n in _g.nodes
    ]
    edges = [{"source": u, "target": v} for u, v in _g.edges]
    return {"nodes": nodes, "edges": edges, "global_risk": global_risk(_g)}


class CascadeRequest(BaseModel):
    seeds: list[str] = Field(min_length=1)
    resist_threshold: int = Field(default=100, ge=0, le=100)


@app.post("/api/cascade")
def cascade_endpoint(req: CascadeRequest):
    unknown = [seed for seed in req.seeds if seed not in _g]
    if unknown:
        raise HTTPException(400, f"Unknown node(s): {unknown}")
    try:
        failed_set = _cascade(_g, req.seeds, req.resist_threshold)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    levels = _bfs_levels(req.seeds, failed_set)
    return {
        "failed": sorted(failed_set),
        "levels": levels,
        "failed_count": len(failed_set),
        "total": _g.number_of_nodes(),
    }


@app.get("/api/sensitivity")
def sensitivity(seed: str = "GlobalCA"):
    if seed not in _g.nodes:
        raise HTTPException(400, f"Unknown node: {seed}")
    return [
        {"threshold": threshold, "failed": len(_cascade(_g, [seed], resist_threshold=threshold))}
        for threshold in range(0, 101, 5)
    ]


@app.get("/api/monte-carlo")
def monte_carlo_endpoint(
    trials: int = 1000,
    seed: int = 0,
    migration_uncertainty_pp: float = 10.0,
    vulnerability_uncertainty: float = 0.1,
):
    """Return reproducible sensitivity percentiles, not empirical confidence intervals."""
    try:
        return monte_carlo_risk(
            _g,
            trials=trials,
            seed=seed,
            migration_uncertainty_pp=migration_uncertainty_pp,
            vulnerability_uncertainty=vulnerability_uncertainty,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


def _bfs_levels(seeds: list[str], failed: set[str]) -> list[list[str]]:
    """Return failed nodes grouped by BFS depth in deterministic order."""
    seed_order = list(dict.fromkeys(seeds))
    visited = set(seed_order)
    levels = [sorted(seed_order)]
    queue = deque(seed_order)
    depth = {seed: 0 for seed in seed_order}

    while queue:
        node = queue.popleft()
        for dependent in sorted(_g.successors(node)):
            if dependent in visited or dependent not in failed:
                continue
            visited.add(dependent)
            next_depth = depth[node] + 1
            depth[dependent] = next_depth
            while len(levels) <= next_depth:
                levels.append([])
            levels[next_depth].append(dependent)
            queue.append(dependent)

    return [sorted(level) for level in levels]
