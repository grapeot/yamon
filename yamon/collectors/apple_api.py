"""Apple Silicon metrics from powermetrics (root) or IOReport (unprivileged)."""

import os
import platform
import plistlib
import re
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class AppleMetrics:
    cpu_power: Optional[float] = None  # W
    gpu_power: Optional[float] = None  # W
    ane_power: Optional[float] = None  # W
    dram_power: Optional[float] = None  # W
    system_power: Optional[float] = None  # W, SMC PSTR only
    pcpu_freq_mhz: Optional[float] = None
    ecpu_freq_mhz: Optional[float] = None
    pcpu_max_freq_mhz: Optional[float] = None
    ecpu_max_freq_mhz: Optional[float] = None
    gpu_usage: Optional[float] = None  # GPU hardware active residency, 0-100
    gpu_freq_mhz: Optional[float] = None
    ane_usage: Optional[float] = None


def _number(value):
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def _cpu_mhz(value):
    frequency = _number(value)
    return frequency / 1_000_000 if frequency is not None else None


def _watts_from_milliwatts(value):
    amount = _number(value)
    return amount / 1000 if amount is not None else None


class AppleAPICollector:
    def __init__(self, debug=False):
        self._debug = debug
        self._is_apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
        self._ioreport = None
        self._smc = None
        if self._is_apple_silicon:
            self._init_smc()
            self._init_ioreport()

    def _init_smc(self):
        try:
            from yamon.collectors.smc import SMC
            self._smc = SMC(debug=self._debug)
        except Exception:
            self._smc = None

    def _init_ioreport(self):
        try:
            from yamon.collectors.ioreport import IOReport
            self._ioreport = IOReport(debug=self._debug)
            self._ioreport.create_subscription([("Energy Model", None)])
        except Exception:
            self._ioreport = None

    def collect(self) -> Optional[AppleMetrics]:
        if not self._is_apple_silicon:
            return None
        # powermetrics supplies a full one-second power interval and GPU
        # residency when already running as root. IOReport remains sudo-free.
        if os.geteuid() == 0:
            result = self._collect_via_powermetrics()
            if result is not None and any(
                value is not None for value in
                (result.cpu_power, result.gpu_power, result.ane_power)
            ):
                return result
        return self._collect_via_ioreport()

    def _system_power(self):
        if self._smc is None:
            return None
        try:
            return self._smc.get_system_power()
        except Exception:
            return None

    def _collect_via_ioreport(self) -> Optional[AppleMetrics]:
        if self._ioreport is None:
            return None
        try:
            values = self._ioreport.get_power_metrics(total_ms=1000, samples=1)
            return AppleMetrics(
                cpu_power=values.get("cpu_power"),
                gpu_power=values.get("gpu_power"),
                ane_power=values.get("ane_power"),
                dram_power=values.get("dram_power"),
                system_power=self._system_power(),
            )
        except Exception:
            return None

    def _collect_via_powermetrics(self) -> Optional[AppleMetrics]:
        try:
            result = subprocess.run(
                ["/usr/bin/powermetrics", "-i", "1000", "-n", "1", "-s",
                 "cpu_power,gpu_power,ane_power", "-f", "plist"],
                capture_output=True, timeout=6, check=True,
            )
            samples = [part for part in result.stdout.split(b"\0") if part.strip()]
            if not samples:
                return None
            return self._parse_powermetrics_plist(plistlib.loads(samples[-1]))
        except (OSError, subprocess.SubprocessError, ValueError, plistlib.InvalidFileException):
            return None

    def _parse_powermetrics_plist(self, sample: dict) -> AppleMetrics:
        processor = sample.get("processor") or {}
        gpu = sample.get("gpu") or {}
        metrics = AppleMetrics(
            cpu_power=_watts_from_milliwatts(processor.get("cpu_power")),
            gpu_power=_watts_from_milliwatts(processor.get("gpu_power")),
            ane_power=_watts_from_milliwatts(processor.get("ane_power")),
            system_power=self._system_power(),
        )
        clusters = processor.get("clusters") or []
        for kind, prefix in (("P", "pcpu"), ("E", "ecpu")):
            matching = [c for c in clusters if str(c.get("name", "")).startswith(kind)]
            frequencies = [_cpu_mhz(c.get("freq_hz")) for c in matching]
            frequencies = [f for f in frequencies if f is not None]
            if frequencies:
                setattr(metrics, f"{prefix}_freq_mhz", sum(frequencies) / len(frequencies))
            maximums = [_number(state.get("freq")) for c in matching for state in c.get("dvfm_states", [])]
            maximums = [f for f in maximums if f is not None]
            if maximums:
                setattr(metrics, f"{prefix}_max_freq_mhz", max(maximums))
        idle_ratio = _number(gpu.get("idle_ratio"))
        if idle_ratio is not None and 0 <= idle_ratio <= 1:
            metrics.gpu_usage = (1 - idle_ratio) * 100
        # The observed macOS plist GPU field is already numerically in MHz,
        # despite its freq_hz name (784.108 in a 784 MHz sample).
        metrics.gpu_freq_mhz = _number(gpu.get("freq_hz"))
        # No documented ANE utilization field exists in this sample.
        return metrics

    @staticmethod
    def _parse_powermetrics_text(text: str) -> AppleMetrics:
        """Parse explicit units if a caller has text samples from older macOS."""
        metrics = AppleMetrics()
        for name, attribute in (("CPU", "cpu_power"), ("GPU", "gpu_power"),
                                ("ANE", "ane_power"), ("System", "system_power")):
            match = re.search(rf"(?im)^\s*{name} Power:\s*([\d.]+)\s*(mW|W)\b", text)
            if match:
                value = float(match.group(1))
                setattr(metrics, attribute, value / 1000 if match.group(2).lower() == "mw" else value)
        active = re.search(r"(?im)^\s*GPU HW active residency:\s*([\d.]+)%", text)
        if active:
            metrics.gpu_usage = float(active.group(1))
        return metrics

    def is_available(self) -> bool:
        return self._is_apple_silicon and (self._ioreport is not None or os.geteuid() == 0)
