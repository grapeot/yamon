import os
import tempfile
from unittest.mock import patch


# The module constructs a default store at import; keep it off the real home.
_summary_dir = tempfile.TemporaryDirectory(prefix="yamon-test-")
with patch.dict(os.environ, {"YAMON_DATA_DIR": _summary_dir.name}):
    from yamon.summary import summary_store


def pytest_sessionfinish():
    summary_store.release_writer_lock()
    _summary_dir.cleanup()
