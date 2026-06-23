"""Quantum Collapse V1 — FastAPI server.

Run from the backend/ directory:
    uvicorn server:app --reload
"""

from collections import deque
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from quantum_collapse.cascade import cascade as _cascade
from quantum_collapse.risk import global_risk, node_risk
from quantum_collapse.topology import build_world

app = FastAPI(title="Quantum Collapse", version="1.0.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
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
    seeds: List[str]
    resist_threshold: int = 100


@app.post("/api/cascade")
def cascade_endpoint(req: CascadeRequest):
    for s in req.seeds:
        if s not in _g.nodes:
            raise HTTPException(400, f"Unknown node: {s}")
    failed_set = _cascade(_g, req.seeds, req.resist_threshold)
    levels = _bfs_levels(req.seeds, failed_set)
    return {
        "failed": list(failed_set),
        "levels": levels,
        "failed_count": len(failed_set),
        "total": _g.number_of_nodes(),
    }


@app.get("/api/sensitivity")
def sensitivity(seed: str = "GlobalCA"):
    if seed not in _g.nodes:
        raise HTTPException(400, f"Unknown node: {seed}")
    return [
        {"threshold": thr, "failed": len(_cascade(_g, [seed], resist_threshold=thr))}
        for thr in range(0, 101, 5)
    ]


def _bfs_levels(seeds: list, failed: set) -> list:
    """Return failed nodes grouped by BFS depth for cascade animation."""
    visited = set(seeds)
    levels = [list(seeds)]
    queue = deque(seeds)
    depth = {s: 0 for s in seeds}

    while queue:
        node = queue.popleft()
        for dep in _g.successors(node):
            if dep in visited or dep not in failed:
                continue
            visited.add(dep)
            d = depth[node] + 1
            depth[dep] = d
            while len(levels) <= d:
                levels.append([])
            levels[d].append(dep)
            queue.append(dep)

    return levels
