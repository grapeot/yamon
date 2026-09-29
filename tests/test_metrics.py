from types import SimpleNamespace
import plistlib

from yamon.api.payload import metric_payload
from yamon.collectors.apple_api import AppleAPICollector
from yamon.collectors.collector import SystemMetrics
from yamon.collectors.cpu_topology import cpu_group_percentages, parse_ioreg_cpu_types
from yamon.summary import SummaryStore


def test_interleaved_topology_and_contributions(monkeypatch):
    blocks = []
    kinds = {}
    for index in range(32):
        kind = "E" if index in {0, 1, 2, 3, 16, 17, 18, 19} else "P"
        blocks.append(f'    | +-o cpu{index}@0\n    |   "cluster-type" = <"{kind}">\n')
        kinds[index] = kind
    assert parse_ioreg_cpu_types("".join(blocks), 32) == kinds
    assert parse_ioreg_cpu_types("".join(blocks[:-1]), 32) is None
    p, e = cpu_group_percentages([100.0] * 32, kinds)
    assert (p, e) == (75.0, 25.0)

    monkeypatch.setattr("yamon.api.payload.cpu_types", lambda _: kinds)
    metrics = SystemMetrics(
        cpu_percent=100.0, cpu_per_core=[100.0] * 32, cpu_count=32,
        memory_total=100, memory_used=50, memory_available=50, memory_percent=50.0,
        swap_total=0, swap_used=0, network_sent=0, network_recv=0,
        network_sent_rate=0.0, network_recv_rate=0.0,
    )
    payload = metric_payload(metrics)
    assert payload["cpu_percent"] == payload["cpu_p_percent"] + payload["cpu_e_percent"]
    assert (payload["cpu_p_count"], payload["cpu_e_count"]) == (24, 8)


def test_plist_units_frequency_and_gpu_residency(monkeypatch):
    collector = AppleAPICollector.__new__(AppleAPICollector)
    collector._smc = None
    sample = {
        "processor": {
            "cpu_power": 58196.9, "gpu_power": 3967.44, "ane_power": 0,
            "clusters": [
                {"name": "E0-Cluster", "freq_hz": 1_800_000_000, "dvfm_states": [{"freq": 2568}]},
                {"name": "P0-Cluster", "freq_hz": 3_600_000_000, "dvfm_states": [{"freq": 4056}]},
                {"name": "E1-Cluster", "freq_hz": 1_700_000_000, "dvfm_states": [{"freq": 2568}]},
                {"name": "P1-Cluster", "freq_hz": 3_500_000_000, "dvfm_states": [{"freq": 4056}]},
            ],
        },
        "gpu": {"idle_ratio": 0.472149, "freq_hz": 784.108},
    }
    metrics = collector._parse_powermetrics_plist(sample)
    assert metrics.cpu_power == 58.1969
    assert metrics.gpu_power == 3.96744
    assert metrics.ane_power == 0.0
    assert metrics.ane_usage is None
    assert metrics.system_power is None
    assert (metrics.pcpu_freq_mhz, metrics.ecpu_freq_mhz) == (3550, 1750)
    assert round(metrics.gpu_usage, 3) == 52.785


def test_text_units_never_guessed_from_size():
    parse = AppleAPICollector._parse_powermetrics_text
    small = parse("CPU Power: 50 mW\nGPU Power: 50 mW\nANE Power: 50 mW")
    high = parse("CPU Power: 150 W\nGPU Power: 150 W\nANE Power: 150 W")
    assert (small.cpu_power, small.gpu_power, small.ane_power) == (0.05, 0.05, 0.05)
    assert (high.cpu_power, high.gpu_power, high.ane_power) == (150, 150, 150)
    assert parse("GPU HW active residency: 100.00%\nGPU HW active frequency: 500 MHz").gpu_usage == 100


def test_one_shot_powermetrics_plist_transport(monkeypatch):
    collector = AppleAPICollector.__new__(AppleAPICollector)
    collector._smc = None
    commands = []
    sample = {"processor": {"cpu_power": 50, "gpu_power": 0, "ane_power": 0},
              "gpu": {"idle_ratio": 1.0}}

    def run(command, **kwargs):
        commands.append(command)
        return SimpleNamespace(stdout=plistlib.dumps(sample) + b"\0")

    monkeypatch.setattr("yamon.collectors.apple_api.subprocess.run", run)
    result = collector._collect_via_powermetrics()
    assert result.cpu_power == 0.05
    assert result.gpu_power == 0.0
    assert result.gpu_usage == 0.0
    assert result.ane_usage is None
    assert commands == [["/usr/bin/powermetrics", "-i", "1000", "-n", "1", "-s",
                         "cpu_power,gpu_power,ane_power", "-f", "plist"]]


def test_summary_uses_elapsed_coverage_and_skips_legacy(tmp_path, monkeypatch):
    clock = {"time": 1_800_000_000.0, "mono": 10.0}
    monkeypatch.setattr("yamon.summary.time.time", lambda: clock["time"])
    monkeypatch.setattr("yamon.summary.time.monotonic", lambda: clock["mono"])
    path = tmp_path / "summary.jsonl"
    path.write_text('{"ts":1799999999,"cpu_s":200,"cpu_n":1,"mem_s":0,"mem_n":1,"pwr_s":0,"pwr_n":1}\n')
    store = SummaryStore(path=path, flush_interval=60)
    sample = SimpleNamespace(cpu_percent=20, memory_used=2**30, system_power=10, sampled_at=clock["time"])
    store.tick(sample)
    clock["time"] += 2
    clock["mono"] += 2
    store.tick(SimpleNamespace(
        cpu_percent=40, memory_used=2**30, system_power=None, sampled_at=clock["time"],
    ))
    store.flush()
    window = store.get_windows([3 * 86400])["windows"][0]
    assert window["samples"] == 3
    assert window["cpu_percent"] == 33.3
    assert window["system_power_w"] == 10
    assert window["pwr_samples"] == 1
    assert window["memory_used_gb"] == 1.0
    assert window["temperature_c"] is None


def test_temperature_average_and_legacy_summary_compatibility(tmp_path, monkeypatch):
    clock = {"time": 1_800_000_000.0, "mono": 10.0}
    monkeypatch.setattr("yamon.summary.time.time", lambda: clock["time"])
    monkeypatch.setattr("yamon.summary.time.monotonic", lambda: clock["mono"])
    path = tmp_path / "summary.jsonl"
    path.write_text(
        '{"schema":2,"ts":1799992800,"cpu_s":200,"cpu_n":2,'
        '"mem_s":2147483648,"mem_n":2,"pwr_s":40,"pwr_n":2}\n'
    )
    store = SummaryStore(path=path, flush_interval=60)

    def sample(cpu, cpu_temp, gpu_temp, power):
        return SimpleNamespace(
            cpu_percent=cpu, memory_used=2**30, system_power=power,
            cpu_temp_c=cpu_temp, gpu_temp_c=gpu_temp, sampled_at=clock["time"],
        )

    store.tick(sample(10, 60, 40, 10))  # 50°C for one observed second
    clock["time"] += 2
    clock["mono"] += 2
    store.tick(sample(40, 80, 60, None))  # 70°C for two observed seconds
    clock["time"] += 1
    clock["mono"] += 1
    store.tick(sample(30, None, 50, 30))  # excluded from temperature only
    store.flush()

    short, long = store.get_windows([3600, 3 * 86400])["windows"]
    assert (short["window_seconds"], long["window_seconds"]) == (3600, 3 * 86400)
    assert short["temperature_c"] == long["temperature_c"] == 63.3
    assert short["temp_samples"] == long["temp_samples"] == 3
    assert short["cpu_percent"] == 30.0
    assert short["samples"] == 4
    assert long["cpu_percent"] == 53.3  # schema 2 CPU stays in the long window
    assert long["samples"] == 6
    assert long["pwr_samples"] == 4
