"""Quantum Collapse V1 — FastAPI server. Run from backend/: uvicorn server:app --reload."""
from collections import deque
from typing import Annotated
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from quantum_collapse.cascade import cascade as _cascade
from quantum_collapse.risk import global_risk, node_risk
from quantum_collapse.topology import build_world

app = FastAPI(title="Quantum Collapse", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
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
    resist_threshold: Annotated[int, Field(ge=0, le=100)] = 100


@app.post("/api/cascade")
def cascade_endpoint(req: CascadeRequest):
    for seed in req.seeds:
        if seed not in _g:
            raise HTTPException(400, f"Unknown node: {seed}")
    failed_set = _cascade(_g, req.seeds, req.resist_threshold)
    levels = _bfs_levels(req.seeds, failed_set)
    return {
        "failed": sorted(failed_set),
        "levels": levels,
        "failed_count": len(failed_set),
        "total": _g.number_of_nodes(),
    }


@app.get("/api/sensitivity")
def sensitivity(seed: str = "GlobalCA"):
    if seed not in _g:
        raise HTTPException(400, f"Unknown node: {seed}")
    return [
        {"threshold": threshold, "failed": len(_cascade(_g, [seed], resist_threshold=threshold))}
        for threshold in range(0, 101, 5)
    ]


def _bfs_levels(seeds: list[str], failed: set) -> list[list[str]]:
    """Return failed nodes grouped by BFS depth for cascade animation."""
    visited = set(seeds)
    levels = [list(seeds)]
    queue = deque(seeds)
    depth = {seed: 0 for seed in seeds}
    while queue:
        node = queue.popleft()
        for dependent in _g.successors(node):
            if dependent in visited or dependent not in failed:
                continue
            visited.add(dependent)
            level = depth[node] + 1
            depth[dependent] = level
            while len(levels) <= level:
                levels.append([])
            levels[level].append(dependent)
            queue.append(dependent)
    return levels
