import json
from types import SimpleNamespace

import pytest

from yamon.api.payload import metric_payload
from yamon.collectors.collector import SystemMetrics
from yamon.summary import SummaryStore


def test_gpu_payload_identifies_corrected_utilization(monkeypatch):
    monkeypatch.setattr("yamon.api.payload.cpu_types", lambda _: None)
    metrics = SystemMetrics(
        cpu_percent=10, cpu_per_core=[10], cpu_count=1,
        memory_total=100, memory_used=50, memory_available=50, memory_percent=50,
        swap_total=0, swap_used=0, network_sent=0, network_recv=0,
        network_sent_rate=0, network_recv_rate=0, gpu_usage=30,
    )
    payload = metric_payload(metrics)
    assert payload["gpu_usage"] == 30
    assert payload["gpu_usage_source"] == "frequency_weighted_residency"
    metrics.gpu_usage = None
    assert metric_payload(metrics)["gpu_usage_source"] is None


def test_gpu_summary_weights_valid_seconds_and_preserves_older_metrics(tmp_path, monkeypatch):
    clock = {"time": 1_800_000_000.0}
    monkeypatch.setattr("yamon.summary.time.time", lambda: clock["time"])
    path = tmp_path / "summary.jsonl"
    legacy = {"schema": 3, "ts": 1_799_999_900, "cpu_s": 800, "cpu_n": 10,
              "mem_s": 10 * 2**30, "mem_n": 10, "pwr_s": 100, "pwr_n": 10,
              "temp_s": 500, "temp_n": 10}
    path.write_text(json.dumps(legacy) + "\n")
    store = SummaryStore(path)
    try:
        old = store.get_windows([3600])["windows"][0]
        assert old["gpu_usage"] is None
        assert old["gpu_samples"] == 0

        def sample(usage):
            return SimpleNamespace(cpu_percent=20, memory_used=2**30, system_power=10,
                                   cpu_temp_c=60, gpu_temp_c=40,
                                   gpu_usage=usage, sampled_at=clock["time"])

        store.tick(sample(30))  # one second
        clock["time"] += 2
        store.tick(sample(60))  # two seconds
        for invalid in (None, float("nan"), float("inf"), -1, 101):
            clock["time"] += 1
            store.tick(sample(invalid))
        store.flush()
        row = json.loads(path.read_text().splitlines()[-1])
        assert row["schema"] == 4
        assert row["gpu_s"] == 150
        assert row["gpu_n"] == 3
        result = store.get_windows([3600])
        window = result["windows"][0]
        assert window["gpu_usage"] == 50
        assert window["gpu_samples"] == 3
        assert window["samples"] == 18
        assert window["temperature_c"] == 50
        assert result["total_recorded_seconds"] == 18

        # A new minute containing genuine zero utilization still counts.
        clock["time"] += 1
        store.tick(sample(0))
        store.flush()
        reader = SummaryStore(path)
        try:
            reread = reader.get_windows([3600])["windows"][0]
            assert reread["gpu_usage"] == pytest.approx(37.5)
            assert reread["gpu_samples"] == 4
        finally:
            reader.release_writer_lock()
    finally:
        store.release_writer_lock()
