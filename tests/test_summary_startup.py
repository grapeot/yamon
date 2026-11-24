import json
import os
import subprocess
import sys
from types import SimpleNamespace

from yamon.summary import SummaryStore


def test_first_start_creates_data_dir_and_records_history(tmp_path, monkeypatch):
    data_dir = tmp_path / "Application Support" / "yamon"
    monkeypatch.setenv("YAMON_DATA_DIR", str(data_dir))
    assert not data_dir.exists()

    store = SummaryStore()
    try:
        assert store.is_writer
        assert (data_dir / "summary.jsonl.lock").is_file()
        other = SummaryStore()
        try:
            assert not other.is_writer
        finally:
            other.release_writer_lock()

        store.tick(SimpleNamespace(cpu_percent=20, memory_used=2**30,
                                   system_power=None, cpu_temp_c=None,
                                   gpu_temp_c=None, gpu_usage=None))
        store.flush()
        assert json.loads((data_dir / "summary.jsonl").read_text())["cpu_s"] == 20
    finally:
        store.release_writer_lock()


def test_unusable_data_path_stays_read_only(tmp_path):
    blocked = tmp_path / "not-a-directory"
    blocked.touch()
    assert not SummaryStore(blocked / "summary.jsonl").is_writer


def test_module_startup_claims_writer_in_fresh_process(tmp_path):
    data_dir = tmp_path / "new" / "yamon"
    subprocess.run(
        [sys.executable, "-c", "from yamon.summary import summary_store; assert summary_store.is_writer"],
        env={**os.environ, "YAMON_DATA_DIR": str(data_dir)}, check=True,
    )
    assert (data_dir / "summary.jsonl.lock").is_file()


def test_writer_does_not_follow_symlink_lock(tmp_path):
    target = tmp_path / "unrelated"
    target.write_text("keep")
    (tmp_path / "summary.jsonl.lock").symlink_to(target)
    assert not SummaryStore(tmp_path / "summary.jsonl").is_writer
    assert target.read_text() == "keep"
