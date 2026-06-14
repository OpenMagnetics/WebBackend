"""Integration test for the design-telemetry pipeline.

Exercises the real HTTP path end to end:

    POST /telemetry  ->  BackgroundTask  ->  telemetry.{sessions,designs,events}

and asserts the rows land in the (production) Postgres DB. Every row this test
writes is tagged `environment = 'development'` so it is trivially filtered out
of real product stats; the test then deletes everything it created.

What it verifies:
  * the endpoint accepts events and writes them,
  * dev traffic is tagged 'development' (the whole point of the env column),
  * MAS payloads are content-deduplicated (same MAS across events -> one
    `designs` row, referenced by several events),
  * intermediate vs final `stage` is recorded.

Run it (backend must be up on :8000, OM_DB_* env vars set):

    OM_DB_USER=... OM_DB_PASSWORD=... OM_DB_ADDRESS=... OM_DB_NAME=... OM_DB_PORT=... \
        venv/bin/python tests/test_telemetry.py

It exits 0 on success, 1 on failure, and is also importable by pytest.
"""

import os
import json
import time
import uuid
import urllib.request

import sqlalchemy


TELEMETRY_URL = os.getenv("OM_TELEMETRY_URL", "http://localhost:8000/telemetry")


def _engine():
    user = os.environ["OM_DB_USER"]
    password = os.environ["OM_DB_PASSWORD"]
    address = os.environ["OM_DB_ADDRESS"]
    port = os.environ["OM_DB_PORT"]
    name = os.environ["OM_DB_NAME"]
    return sqlalchemy.create_engine(
        f"postgresql://{user}:{password}@{address}:{port}/{name}"
    )


def _post(payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        TELEMETRY_URL, data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status


def test_telemetry_records_in_db():
    engine = _engine()
    # Bare UUID (36 chars) — matches the frontend's session_id column width.
    session_id = str(uuid.uuid4())
    # A nonce embedded in every test MAS so cleanup can delete exactly our rows.
    nonce = session_id

    # MAS A appears in two events (must deduplicate to ONE design row); MAS B is
    # a distinct design.
    mas_a = {"inputs": {"designRequirements": {"topology": "Flyback"}},
             "magnetic": {"_test_nonce": nonce, "variant": "A"}}
    mas_b = {"inputs": {"designRequirements": {"topology": "Flyback"}},
             "magnetic": {"_test_nonce": nonce, "variant": "B"}}

    events = [
        {"event_type": "wizard_submit", "source": "wizard/Flyback",
         "stage": "intermediate", "topology": "Flyback", "mas_data": mas_a},
        {"event_type": "design_report", "source": "adviser",
         "stage": "final", "topology": "Flyback", "mas_data": mas_a},
        {"event_type": "design_export", "source": "export/stp",
         "stage": "final", "topology": "Flyback", "mas_data": mas_b},
    ]

    try:
        for e in events:
            payload = dict(e, session_id=session_id, environment="development")
            status = _post(payload)
            assert status == 200, f"POST /telemetry returned {status}"

        # Background tasks are async; poll until all three events land (or time out).
        rows = []
        for _ in range(20):  # up to ~10s
            with engine.connect() as conn:
                rows = conn.execute(sqlalchemy.text(
                    "SELECT e.event_type, e.stage, e.design_id, s.environment "
                    "FROM telemetry.events e JOIN telemetry.sessions s USING (session_id) "
                    "WHERE e.session_id = :sid ORDER BY e.event_id"),
                    {"sid": session_id}).fetchall()
            if len(rows) >= 3:
                break
            time.sleep(0.5)

        assert len(rows) == 3, f"expected 3 events, found {len(rows)}"

        # Every row must be tagged development (so it can be filtered out of stats).
        assert all(r.environment == "development" for r in rows), \
            f"events not tagged development: {[r.environment for r in rows]}"

        # event_type / stage recorded correctly.
        by_type = {r.event_type: r for r in rows}
        assert by_type["wizard_submit"].stage == "intermediate"
        assert by_type["design_report"].stage == "final"
        assert by_type["design_export"].stage == "final"

        # Dedup: the two MAS-A events share one design row; MAS-B is a different one.
        assert by_type["wizard_submit"].design_id == by_type["design_report"].design_id, \
            "identical MAS was not deduplicated to one design row"
        assert by_type["design_export"].design_id != by_type["wizard_submit"].design_id, \
            "distinct MAS collapsed into the same design row"

        distinct_designs = len({r.design_id for r in rows})
        assert distinct_designs == 2, f"expected 2 distinct designs, found {distinct_designs}"

        print(f"PASS: 3 events recorded (dev-tagged), deduped to 2 designs, stages correct "
              f"[session {session_id}]")

    finally:
        # Clean up everything this test created, in FK-safe order.
        with engine.begin() as conn:
            conn.execute(sqlalchemy.text(
                "DELETE FROM telemetry.events WHERE session_id = :sid"), {"sid": session_id})
            conn.execute(sqlalchemy.text(
                "DELETE FROM telemetry.designs WHERE mas_data->'magnetic'->>'_test_nonce' = :n"),
                {"n": nonce})
            conn.execute(sqlalchemy.text(
                "DELETE FROM telemetry.sessions WHERE session_id = :sid"), {"sid": session_id})
        engine.dispose()


if __name__ == "__main__":
    import sys
    try:
        test_telemetry_records_in_db()
    except AssertionError as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001 - surface any wiring/connection error loudly
        print(f"ERROR: {type(exc).__name__}: {exc}")
        sys.exit(1)
    sys.exit(0)
