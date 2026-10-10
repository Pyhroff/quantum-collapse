"""Monte Carlo sensitivity bands for explicitly illustrative risk assumptions.

These are scenario sensitivity bands under user-selected bounded uniform
perturbations, not confidence intervals derived from observed infrastructure data.
"""
from __future__ import annotations

import math
import random
from statistics import fmean, pstdev

from .risk import QUANTUM_VULNERABILITY, _UNKNOWN_CRYPTO_VULNERABILITY, global_risk, node_risk, node_vulnerability


def _finite_range(value: float, name: str, low: float, high: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}")


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if not sorted_values:
        return 0.0
    position = (len(sorted_values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] * (1.0 - fraction) + sorted_values[upper] * fraction


def monte_carlo_risk(
    graph,
    *,
    trials: int = 1000,
    seed: int = 0,
    migration_uncertainty_pp: float = 10.0,
    vulnerability_uncertainty: float = 0.1,
) -> dict:
    """Estimate model-score sensitivity under reproducible bounded perturbations.

    Migration is sampled uniformly within +/- percentage points of each node's
    configured migration. Base vulnerability is sampled uniformly within +/- the
    configured absolute score delta and clipped to [0, 1]. Criticality stays fixed.
    """
    if isinstance(trials, bool) or not isinstance(trials, int) or not 100 <= trials <= 10000:
        raise ValueError("trials must be an integer between 100 and 10000")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    _finite_range(migration_uncertainty_pp, "migration_uncertainty_pp", 0.0, 100.0)
    _finite_range(vulnerability_uncertainty, "vulnerability_uncertainty", 0.0, 1.0)

    nodes = sorted(graph.nodes, key=str)
    # Validate model inputs before drawing samples; invalid data must not be hidden.
    for node in nodes:
        node_vulnerability(graph, node)
        node_risk(graph, node)

    baseline = global_risk(graph)
    if not nodes:
        scores = [0.0] * trials
    else:
        rng = random.Random(seed)
        scores = []
        for _ in range(trials):
            node_scores = []
            for node in nodes:
                attrs = graph.nodes[node]
                base = QUANTUM_VULNERABILITY.get(
                    attrs["crypto"], _UNKNOWN_CRYPTO_VULNERABILITY
                )
                migration = float(attrs["migration_pct"])
                criticality = float(attrs["criticality"])
                sampled_base = rng.uniform(
                    max(0.0, base - vulnerability_uncertainty),
                    min(1.0, base + vulnerability_uncertainty),
                )
                sampled_migration = rng.uniform(
                    max(0.0, migration - migration_uncertainty_pp),
                    min(100.0, migration + migration_uncertainty_pp),
                )
                node_scores.append(
                    (criticality / 5.0) * sampled_base * (1.0 - sampled_migration / 100.0)
                )
            scores.append(fmean(node_scores))

    ordered = sorted(scores)
    return {
        "baseline_risk": baseline,
        "mean": fmean(scores),
        "stddev": pstdev(scores),
        "p05": _percentile(ordered, 0.05),
        "p50": _percentile(ordered, 0.50),
        "p95": _percentile(ordered, 0.95),
        "minimum": ordered[0],
        "maximum": ordered[-1],
        "trials": trials,
        "seed": seed,
        "band_type": "scenario_sensitivity_percentiles_not_empirical_confidence_interval",
        "assumptions": {
            "sampling": "independent uniform perturbations per node and trial",
            "migration_uncertainty_percentage_points": migration_uncertainty_pp,
            "absolute_base_vulnerability_uncertainty": vulnerability_uncertainty,
            "criticality": "held fixed at configured scenario value",
            "source_data": "illustrative model inputs, not measured infrastructure data",
        },
    }
