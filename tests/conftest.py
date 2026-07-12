import pathlib
import sys

import pytest

# Make the repo root importable (app.backend.*) regardless of pytest rootdir.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Every TestClient request comes from the same 'IP', so a combined run
    trips the per-IP auth limits (e.g. register 10/h). Reset between tests —
    the limiter itself stays untouched in production."""
    from app.backend.accounts import ratelimit
    ratelimit.reset()
    yield
