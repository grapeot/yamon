"""One metric contract shared by HTTP, WebSocket, and recorded summaries."""

from dataclasses import asdict
from yamon.collectors.cpu_topology import cpu_group_percentages, cpu_types


def metric_payload(metrics):
    topology = cpu_types(metrics.cpu_count)
    p_percent, e_percent = cpu_group_percentages(metrics.cpu_per_core, topology)
    values = asdict(metrics)
    values.update({
        "cpu_p_percent": p_percent,
        "cpu_e_percent": e_percent,
        "cpu_p_count": sum(kind == "P" for kind in topology.values()) if topology else None,
        "cpu_e_count": sum(kind == "E" for kind in topology.values()) if topology else None,
        "gpu_usage_source": "active_residency" if metrics.gpu_usage is not None else None,
    })
    return values
