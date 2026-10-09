"""Reproducible migration-rate sensitivity sweep for Quantum Collapse.

Outputs scenario sensitivity bands under explicit model assumptions. These are
not empirical confidence intervals and do not represent measured infrastructure.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from .topology import build_world
from .uncertainty import monte_carlo_risk

DEFAULT_MIGRATION_RATES = (0, 25, 50, 75, 100)


def build_sweep_report(
    *,
    migration_rates: list[float] | tuple[float, ...] = DEFAULT_MIGRATION_RATES,
    trials: int = 1000,
    seed: int = 2026,
    migration_uncertainty_pp: float = 10.0,
    vulnerability_uncertainty: float = 0.1,
    code_revision: str | None = None,
) -> dict:
    if not migration_rates:
        raise ValueError("migration_rates must not be empty")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    started = time.perf_counter()
    rows = []
    for index, rate in enumerate(migration_rates):
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or not 0 <= rate <= 100:
            raise ValueError("each migration rate must be between 0 and 100")
        graph = build_world()
        for node in graph.nodes:
            graph.nodes[node]["migration_pct"] = float(rate)
        result = monte_carlo_risk(
            graph,
            trials=trials,
            seed=seed + index,
            migration_uncertainty_pp=migration_uncertainty_pp,
            vulnerability_uncertainty=vulnerability_uncertainty,
        )
        rows.append({
            "migration_pct": float(rate),
            "baseline_risk": result["baseline_risk"],
            "mean": result["mean"],
            "stddev": result["stddev"],
            "p05": result["p05"],
            "p50": result["p50"],
            "p95": result["p95"],
            "minimum": result["minimum"],
            "maximum": result["maximum"],
            "trials": result["trials"],
            "seed": result["seed"],
            "band_type": result["band_type"],
        })

    return {
        "schema_version": "1.0",
        "experiment": "quantum-collapse-migration-sensitivity",
        "measurement_type": "scenario_sensitivity_not_empirical_estimate",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_revision": code_revision or os.getenv("GITHUB_SHA", "unknown"),
        "environment": {"python": sys.version.split()[0], "platform": platform.platform()},
        "parameters": {
            "migration_rates_pct": list(migration_rates),
            "trials_per_rate": trials,
            "base_seed": seed,
            "migration_uncertainty_pp": migration_uncertainty_pp,
            "vulnerability_uncertainty": vulnerability_uncertainty,
        },
        "assumptions": {
            "topology": "built-in illustrative 17-node scenario",
            "criticality": "held at topology defaults",
            "sampling": "independent uniform perturbations per node and trial",
            "interpretation": "percentile bands quantify model-input sensitivity, not empirical confidence intervals",
        },
        "result_count": len(rows),
        "runtime_seconds": round(time.perf_counter() - started, 6),
        "results": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--migration-rates", default=",".join(map(str, DEFAULT_MIGRATION_RATES)))
    parser.add_argument("--trials", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--migration-uncertainty-pp", type=float, default=10.0)
    parser.add_argument("--vulnerability-uncertainty", type=float, default=0.1)
    parser.add_argument("--revision", default=None)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        report = build_sweep_report(
            migration_rates=[float(value) for value in args.migration_rates.split(",") if value.strip()],
            trials=args.trials,
            seed=args.seed,
            migration_uncertainty_pp=args.migration_uncertainty_pp,
            vulnerability_uncertainty=args.vulnerability_uncertainty,
            code_revision=args.revision,
        )
    except ValueError as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
