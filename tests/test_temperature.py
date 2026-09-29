import struct
from types import SimpleNamespace

from yamon.collectors.apple_api import AppleAPICollector
from yamon.collectors.smc import SMC
from yamon.history import MetricsHistory


def test_smc_averages_only_valid_cpu_and_gpu_sensors(monkeypatch):
    smc = SMC.__new__(SMC)
    smc._conn = 1
    smc._io_kit = SimpleNamespace(IOServiceClose=lambda _: None)
    smc._temperature_keys = None
    names = ["Tp00", "Te00", "Tg00", "Tg01", "Ts00", "TAmb", "Tp01"]
    values = {"Tp00": 60.0, "Te00": 64.0, "Tg00": 55.0,
              "Tg01": float("nan"), "Ts00": 180.0, "Tp01": 58.0}

    def call_smc(data):
        name = names[data.data32]
        return SimpleNamespace(key=int.from_bytes(name.encode(), "big"))

    def read_key(name):
        if name == "#KEY":
            return len(names).to_bytes(4, "big")
        if name in values:
            return struct.pack("<f", values[name])
        return None

    monkeypatch.setattr(smc, "call_smc", call_smc)
    monkeypatch.setattr(smc, "read_key", read_key)
    monkeypatch.setattr(smc, "read_key_info", lambda name: SimpleNamespace(
        data_size=4, data_type=SMC.SMC_FLOAT_TYPE))
    assert smc.get_temperatures() == (60.666666666666664, 55.0)
    assert smc._temperature_keys == (["Tp00", "Te00", "Tp01"], ["Tg00"])
    values["Tg00"] = float("nan")
    assert smc.get_temperatures() == (60.666666666666664, None)


def test_temperature_remains_available_without_power(monkeypatch):
    collector = AppleAPICollector.__new__(AppleAPICollector)
    collector._is_apple_silicon = True
    collector._ioreport = None
    collector._smc = SimpleNamespace(get_temperatures=lambda: (62.5, 54.0))
    monkeypatch.setattr("yamon.collectors.apple_api.os.geteuid", lambda: 501)
    metrics = collector.collect()
    assert (metrics.cpu_temp_c, metrics.gpu_temp_c) == (62.5, 54.0)
    assert metrics.cpu_power is None


def test_history_keeps_missing_temperature_gaps():
    history = MetricsHistory(max_size=3)
    for cpu, gpu in [(60.0, None), (None, 53.0)]:
        history.add_metrics(SimpleNamespace(
            cpu_percent=1, cpu_per_core=[], memory_percent=1,
            network_sent_rate=0, network_recv_rate=0,
            cpu_power=None, gpu_power=None, ane_power=None, system_power=None,
            gpu_usage=None, ane_usage=None, cpu_temp_c=cpu, gpu_temp_c=gpu,
        ))
    assert history.cpu_temp_c.get_values() == [60.0, None]
    assert history.gpu_temp_c.get_values() == [None, 53.0]
