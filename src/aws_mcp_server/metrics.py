"""Lightweight metrics collection with Prometheus exposition format.

Implemented without external dependencies so the server has zero extra runtime
requirements for basic observability. The exposition output is compatible with
Prometheus scrapers.
"""

import threading
import time
from collections import defaultdict
from typing import Dict, List, Tuple

# Histogram buckets in seconds (Prometheus convention, upper bounds).
_DEFAULT_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)

# A label set is a sorted tuple of (key, value) pairs so it can be a dict key.
LabelSet = Tuple[Tuple[str, str], ...]


def _labels(labels: Dict[str, str]) -> LabelSet:
    return tuple(sorted(labels.items()))


class MetricsCollector:
    """Collects counters and histograms and renders Prometheus text format."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: Dict[str, Dict[LabelSet, float]] = defaultdict(dict)
        self._histograms: Dict[str, Dict[LabelSet, List[float]]] = defaultdict(dict)
        self._start_time = time.time()

    def inc_counter(self, name: str, value: float = 1.0, **labels: str) -> None:
        """Increment a counter metric."""
        key = _labels(labels)
        with self._lock:
            current = self._counters[name].get(key, 0.0)
            self._counters[name][key] = current + value

    def observe(self, name: str, value: float, **labels: str) -> None:
        """Record an observation for a histogram metric (e.g. latency)."""
        key = _labels(labels)
        with self._lock:
            self._histograms[name].setdefault(key, []).append(value)

    def render(self) -> str:
        """Render all metrics in Prometheus text exposition format."""
        lines: List[str] = []
        with self._lock:
            lines.append("# HELP aws_mcp_uptime_seconds Server uptime in seconds.")
            lines.append("# TYPE aws_mcp_uptime_seconds gauge")
            lines.append(f"aws_mcp_uptime_seconds {time.time() - self._start_time:.3f}")

            for name, series in self._counters.items():
                lines.append(f"# TYPE {name} counter")
                for labelset, value in series.items():
                    lines.append(f"{name}{self._fmt_labels(labelset)} {value}")

            for name, series in self._histograms.items():
                lines.append(f"# TYPE {name} histogram")
                for labelset, values in series.items():
                    lines.extend(self._render_histogram(name, labelset, values))

        return "\n".join(lines) + "\n"

    def _render_histogram(
        self, name: str, labelset: LabelSet, values: List[float]
    ) -> List[str]:
        out: List[str] = []
        count = len(values)
        total = sum(values)
        for bound in _DEFAULT_BUCKETS:
            le_count = sum(1 for v in values if v <= bound)
            bucket_labels = labelset + (("le", str(bound)),)
            out.append(f"{name}_bucket{self._fmt_labels(bucket_labels)} {le_count}")
        inf_labels = labelset + (("le", "+Inf"),)
        out.append(f"{name}_bucket{self._fmt_labels(inf_labels)} {count}")
        out.append(f"{name}_sum{self._fmt_labels(labelset)} {total:.6f}")
        out.append(f"{name}_count{self._fmt_labels(labelset)} {count}")
        return out

    @staticmethod
    def _fmt_labels(labelset: LabelSet) -> str:
        if not labelset:
            return ""
        inner = ",".join(f'{k}="{v}"' for k, v in labelset)
        return "{" + inner + "}"

    def snapshot(self) -> Dict[str, object]:
        """Return a JSON-friendly snapshot of current metrics."""
        with self._lock:
            return {
                "uptime_seconds": round(time.time() - self._start_time, 3),
                "counters": {
                    name: {dict(k).__repr__(): v for k, v in series.items()}
                    for name, series in self._counters.items()
                },
                "histograms": {
                    name: {
                        dict(k).__repr__(): {
                            "count": len(v),
                            "sum": round(sum(v), 6),
                            "avg": round(sum(v) / len(v), 6) if v else 0.0,
                        }
                        for k, v in series.items()
                    }
                    for name, series in self._histograms.items()
                },
            }


# A module-level default collector for convenience.
default_collector = MetricsCollector()
