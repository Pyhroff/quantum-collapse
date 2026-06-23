"""Quantum Collapse V1 — first runnable slice.

Build the world, break a Certificate Authority, watch the cascade, render it.

    cd backend
    pip install -r requirements.txt
    python demo.py
"""

import matplotlib.pyplot as plt
import networkx as nx

from quantum_collapse.cascade import cascade
from quantum_collapse.risk import global_risk
from quantum_collapse.topology import build_world


def main() -> None:
    g = build_world()
    seed = "GlobalCA"

    print(f"World: {g.number_of_nodes()} nodes, {g.number_of_edges()} dependencies")
    print(f"Global risk (pre-event): {global_risk(g)}")
    print(f"\nCompromising: {seed}\n")

    failed = cascade(g, [seed], resist_threshold=100)
    surviving = set(g.nodes) - failed
    print(f"FAILED   ({len(failed):2d}): {sorted(failed)}")
    print(f"SURVIVED ({len(surviving):2d}): {sorted(surviving)}")

    # quick sensitivity sweep over the migration resist-threshold
    print("\nSensitivity - entities down vs. PQC resist-threshold:")
    for thr in (100, 60, 40, 20, 10):
        n_down = len(cascade(g, [seed], resist_threshold=thr))
        print(f"  threshold {thr:3d}% migrated to survive -> {n_down:2d}/{g.number_of_nodes()} down")

    _render(g, seed, failed)


def _render(g, seed, failed) -> None:
    pos = nx.spring_layout(g, seed=42, k=0.9)
    colors = ["#c0392b" if n in failed else "#2e7d32" for n in g.nodes]
    plt.figure(figsize=(13, 9))
    nx.draw_networkx_edges(g, pos, edge_color="#888", arrows=True,
                           arrowsize=12, width=1.0, alpha=0.6)
    nx.draw_networkx_nodes(g, pos, node_color=colors, node_size=1500,
                           edgecolors="#222", linewidths=1.2)
    labels = {n: f"{n}\n{g.nodes[n]['crypto']}" for n in g.nodes}
    nx.draw_networkx_labels(g, pos, labels, font_size=7, font_color="white")
    plt.title(f"Quantum Collapse — '{seed}' compromised -> "
              f"{len(failed)}/{g.number_of_nodes()} entities down", fontsize=13)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig("cascade.png", dpi=130)
    print("\nSaved cascade.png")


if __name__ == "__main__":
    main()
