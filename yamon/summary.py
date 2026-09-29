"""Persistent summary recording.

Accumulates time-weighted metric sums, flushes a JSON line per minute, and
auto-rotates that file so disk usage stays bounded:

- time-based retention: rows older than RETENTION_DAYS are dropped
- hard size cap: if the file ever exceeds MAX_BYTES, oldest rows are dropped
- rotation is an atomic rewrite (temp file + os.replace)

The file is the only durable state; losing it loses nothing critical.
"""

import json
import os
import pwd
import threading
import time
from pathlib import Path
from typing import List, Optional, Sequence

RETENTION_DAYS = 21
MAX_BYTES = 20 * 1024 * 1024


def _default_data_dir() -> Path:
    """Data dir in the real user's home, even when running under sudo."""
    user = os.environ.get("SUDO_USER")
    home: Optional[str] = None
    if user:
        try:
            home = pwd.getpwnam(user).pw_dir
        except KeyError:
            home = None
    if home is None:
        home = Path.home()
    return Path(home) / "Library" / "Application Support" / "yamon"


def _round(x: float, nd: int = 3) -> float:
    return round(x, nd)


def _chown_to_invoking_user(path: Path) -> None:
    """Hand created paths back to the real user when running as root (sudo).

    Without this, a sudo run creates root-owned directory/file in the user's
    home and every later non-sudo run fails with PermissionError.
    """
    if os.geteuid() != 0:
        return
    user = os.environ.get("SUDO_USER")
    if not user:
        return
    try:
        pw = pwd.getpwnam(user)
        if path.stat().st_uid != pw.pw_uid:
            os.chown(path, pw.pw_uid, pw.pw_gid)
    except (KeyError, OSError):
        pass


def _parse_ts(line: str) -> Optional[int]:
    """Normalized integer ts of a valid row, or None for corrupt rows."""
    try:
        row = json.loads(line)
        ts = row["ts"]
        if isinstance(ts, bool) or not isinstance(ts, (int, float)):
            return None
        return int(ts)
    except (json.JSONDecodeError, ValueError, KeyError, TypeError):
        return None


class SummaryStore:
    """In-memory per-second accumulation, per-minute flush, auto-rotating file."""

    def __init__(self, path: Optional[Path] = None, flush_interval: float = 60.0):
        if path is None:
            env_dir = os.environ.get("YAMON_DATA_DIR")
            base = Path(env_dir) if env_dir else _default_data_dir()
            path = base / "summary.jsonl"
        self.path = Path(path)
        self.flush_interval = flush_interval
        self.retention_days = RETENTION_DAYS
        self.max_bytes = MAX_BYTES

        self._lock = threading.Lock()
        # per-minute accumulator
        self._cpu_s = 0.0
        self._cpu_n = 0
        self._mem_s = 0.0
        self._mem_n = 0
        self._pwr_s = 0.0
        self._pwr_n = 0
        self._last_sample_at: Optional[float] = None
        self._window_start: Optional[int] = None
        self._next_flush_at: Optional[float] = None
        self._last_rotate_check = time.monotonic()
        self._size = self._read_size()
        self._write_ok = True
        # read cache (key = mtime_ns + size; rows are never mutated after load)
        self._cache_key = None
        self._cache_rows: List[dict] = []

    def _read_size(self) -> int:
        try:
            return self.path.stat().st_size
        except OSError:
            return 0

    # ------------------------------------------------------------------ write

    def tick(self, metrics) -> None:
        """Accumulate observed awake time; never count a long sleep gap."""
        with self._lock:
            sampled_at = getattr(metrics, "sampled_at", None) or time.time()
            elapsed = sampled_at - self._last_sample_at if self._last_sample_at is not None else 1.0
            weight = elapsed if 0 < elapsed <= 3.0 else 1.0
            self._last_sample_at = sampled_at
            if self._window_start is None:
                self._window_start = int(sampled_at)
                self._next_flush_at = time.monotonic() + self.flush_interval
            self._cpu_s += float(metrics.cpu_percent) * weight
            self._cpu_n += weight
            self._mem_s += float(metrics.memory_used) * weight
            self._mem_n += weight
            if metrics.system_power is not None:
                self._pwr_s += float(metrics.system_power) * weight
                self._pwr_n += weight
            if time.monotonic() >= (self._next_flush_at or float("inf")):
                self._flush_locked()
            self._maybe_rotate_locked()

    def flush(self) -> None:
        """Force-flush the current partial minute (e.g. on shutdown)."""
        with self._lock:
            self._flush_locked()

    def _flush_locked(self) -> None:
        self._next_flush_at = time.monotonic() + self.flush_interval
        if self._cpu_n == 0 or self._window_start is None:
            return
        row = {
            "schema": 2,
            "ts": self._window_start,
            "cpu_s": _round(self._cpu_s),
            "cpu_n": _round(self._cpu_n),
            "mem_s": _round(self._mem_s, 1),
            "mem_n": _round(self._mem_n),
            "pwr_s": _round(self._pwr_s),
            "pwr_n": _round(self._pwr_n),
        }
        line = json.dumps(row, separators=(",", ":")) + "\n"
        if self._write_ok:
            try:
                dir_existed = self.path.parent.exists()
                file_existed = self.path.exists()
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.path, "a", encoding="utf-8") as f:
                    f.write(line)
                self._size += len(line.encode("utf-8"))
                if not dir_existed:
                    _chown_to_invoking_user(self.path.parent)
                if not file_existed:
                    _chown_to_invoking_user(self.path)
            except PermissionError:
                self._write_ok = False
                print(f"yamon summary: cannot write {self.path}; recording disabled")
            except OSError as e:
                print(f"yamon summary: write failed: {e}")
        self._cpu_s = 0.0
        self._cpu_n = 0
        self._mem_s = 0.0
        self._mem_n = 0
        self._pwr_s = 0.0
        self._pwr_n = 0
        self._window_start = None

    def _maybe_rotate_locked(self) -> None:
        if not self._write_ok:
            return
        now_mono = time.monotonic()
        if self._size <= self.max_bytes and now_mono - self._last_rotate_check < 3600:
            return
        self._last_rotate_check = now_mono
        self._rotate_locked()

    def rotate_if_needed(self, force: bool = False) -> None:
        with self._lock:
            if not force and self._size <= self.max_bytes:
                return
            self._rotate_locked()

    def _rotate_locked(self) -> None:
        if not self._write_ok or self._size == 0:
            return
        cutoff = int(time.time()) - self.retention_days * 86400
        kept: List[str] = []
        kept_bytes = 0
        parsed = 0
        invalid = 0
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for raw in f:
                    line = raw.strip()
                    if not line:
                        continue
                    ts = _parse_ts(line)
                    if ts is None:
                        invalid += 1
                        continue
                    parsed += 1
                    if ts < cutoff:
                        continue
                    kept.append(line)
                    kept_bytes += len(line.encode("utf-8")) + 1
        except OSError:
            return
        # enforce hard size cap by dropping oldest rows first (only when over)
        if kept_bytes > self.max_bytes:
            total = kept_bytes
            idx = 0
            for i, line in enumerate(kept):
                total -= len(line.encode("utf-8")) + 1
                idx = i + 1
                if total <= self.max_bytes:
                    break
            kept = kept[idx:]
            kept_bytes = total
        if len(kept) == parsed and invalid == 0:
            return
        tmp = self.path.with_name(self.path.name + ".tmp")
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                for line in kept:
                    f.write(line + "\n")
            os.replace(tmp, self.path)
            self._size = kept_bytes
            _chown_to_invoking_user(self.path)
            print(f"yamon summary: rotated {self.path.name}, kept {len(kept)} rows")
        except OSError as e:
            print(f"yamon summary: rotation failed: {e}")
            try:
                tmp.unlink()
            except OSError:
                pass

    # ------------------------------------------------------------------- read

    def get_windows(self, days_list: Sequence[int]) -> dict:
        """Average CPU / memory used / system power over trailing windows."""
        now = int(time.time())
        rows = self._load_rows()
        windows = []
        for d in days_list:
            cutoff = now - d * 86400
            cpu_s = cpu_n = mem_s = mem_n = pwr_s = pwr_n = 0
            oldest: Optional[int] = None
            for r in rows:
                ts = r.get("ts")
                # Earlier rows counted samples rather than elapsed time and
                # used a different CPU metric. Do not mix the two contracts.
                if r.get("schema") != 2 or ts is None or ts < cutoff:
                    continue
                cpu_s += r.get("cpu_s", 0)
                cpu_n += r.get("cpu_n", 0)
                mem_s += r.get("mem_s", 0)
                mem_n += r.get("mem_n", 0)
                pwr_s += r.get("pwr_s", 0)
                pwr_n += r.get("pwr_n", 0)
                if oldest is None or ts < oldest:
                    oldest = ts
            windows.append({
                "days": d,
                "cpu_percent": _round(cpu_s / cpu_n, 1) if cpu_n else None,
                "memory_used_gb": _round(mem_s / mem_n / 2**30, 1) if mem_n else None,
                "system_power_w": _round(pwr_s / pwr_n, 1) if pwr_n else None,
                "samples": cpu_n,
                "mem_samples": mem_n,
                "pwr_samples": pwr_n,
                "oldest_ts": oldest,
            })
        return {"generated_at": now, "windows": windows}

    def _load_rows(self, _retry: bool = True) -> List[dict]:
        try:
            st = self.path.stat()
            key = (st.st_mtime_ns, st.st_size)
        except OSError:
            return []
        if key == self._cache_key:
            return self._cache_rows
        rows: List[dict] = []
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    ts = _parse_ts(line)
                    if ts is None:
                        continue
                    row = json.loads(line)
                    row["ts"] = ts
                    rows.append(row)
        except OSError:
            return []
        # the file may have rotated while we were reading; don't publish a
        # stale generation over a newer one
        try:
            st2 = self.path.stat()
            key2 = (st2.st_mtime_ns, st2.st_size)
        except OSError:
            return []
        if key2 != key:
            if _retry:
                return self._load_rows(_retry=False)
            rows = []
        with self._lock:
            self._cache_key = key
            self._cache_rows = rows
        return rows


summary_store = SummaryStore()
