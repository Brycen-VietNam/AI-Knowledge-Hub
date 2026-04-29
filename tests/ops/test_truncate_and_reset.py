"""Tests for scripts/truncate_and_reset.py

TDD: tests written before implementation.
All DB calls mocked — no live connection required.
"""
import importlib
import sys
import types
from unittest.mock import MagicMock, call, patch

import pytest


def _load_script():
    """Import truncate_and_reset without executing main()."""
    spec = importlib.util.spec_from_file_location(
        "truncate_and_reset",
        "scripts/truncate_and_reset.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def script():
    return _load_script()


@pytest.fixture()
def mock_engine():
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    # Default row count scalar returns
    conn.execute.return_value.scalar.return_value = 0
    engine = MagicMock()
    engine.connect.return_value = conn
    return engine, conn


class TestConfirmGate:
    def test_missing_confirm_flag_exits_nonzero(self, script):
        with pytest.raises(SystemExit) as exc:
            script.main(["--no-confirm-missing"])
        assert exc.value.code != 0

    def test_confirm_flag_allows_execution(self, script, mock_engine):
        engine, conn = mock_engine
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://stub"}):
            with patch.object(script, "_build_engine", return_value=engine):
                script.main(["--confirm"])
        conn.execute.assert_called()

    def test_no_args_exits_nonzero(self, script):
        with pytest.raises(SystemExit) as exc:
            script.main([])
        assert exc.value.code != 0


class TestSQLSafety:
    def test_no_fstring_in_truncate_calls(self, script):
        import inspect
        src = inspect.getsource(script)
        assert "f\"" not in src or "truncate" not in src.split("f\"")[1].split("\"")[0]

    def test_uses_sqlalchemy_text(self, script):
        import inspect
        src = inspect.getsource(script)
        assert "sqlalchemy.text(" in src or "from sqlalchemy import text" in src or "text(" in src

    def test_no_hardcoded_db_credentials(self, script):
        import inspect
        src = inspect.getsource(script)
        for bad in ("postgres://", "postgresql://", "password=", "DATABASE_URL ="):
            assert bad not in src, f"Hardcoded credential pattern found: {bad!r}"


class TestRowCountLogging:
    def test_logs_before_count(self, script, mock_engine, caplog):
        import logging
        engine, conn = mock_engine
        conn.execute.return_value.scalar.side_effect = [42, 0, 10, 0]
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://stub"}):
            with patch.object(script, "_build_engine", return_value=engine):
                with caplog.at_level(logging.INFO):
                    script.main(["--confirm"])
        assert any("42" in r.message for r in caplog.records)

    def test_logs_after_count_zero(self, script, mock_engine, caplog):
        import logging
        engine, conn = mock_engine
        conn.execute.return_value.scalar.side_effect = [5, 0, 3, 0]
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://stub"}):
            with patch.object(script, "_build_engine", return_value=engine):
                with caplog.at_level(logging.INFO):
                    script.main(["--confirm"])
        assert any("0" in r.message for r in caplog.records)


class TestIdempotency:
    def test_second_run_no_error(self, script, mock_engine):
        engine, conn = mock_engine
        conn.execute.return_value.scalar.return_value = 0
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://stub"}):
            with patch.object(script, "_build_engine", return_value=engine):
                script.main(["--confirm"])
                script.main(["--confirm"])

    def test_truncate_called_for_both_tables(self, script, mock_engine):
        engine, conn = mock_engine
        conn.execute.return_value.scalar.return_value = 0
        with patch.dict("os.environ", {"DATABASE_URL": "postgresql://stub"}):
            with patch.object(script, "_build_engine", return_value=engine):
                script.main(["--confirm"])
        executed_statements = [str(c.args[0]) for c in conn.execute.call_args_list]
        text_args = " ".join(executed_statements).lower()
        assert "embeddings" in text_args
        assert "audit_logs" in text_args


class TestEnvConfig:
    def test_database_url_from_env(self, script):
        stub_url = "postgresql+psycopg2://test:test@localhost/testdb"
        conn = MagicMock()
        conn.__enter__ = MagicMock(return_value=conn)
        conn.__exit__ = MagicMock(return_value=False)
        conn.execute.return_value.scalar.return_value = 0
        mock_eng = MagicMock()
        mock_eng.connect.return_value = conn

        captured = {}

        def fake_build_engine(url):
            captured["url"] = url
            return mock_eng

        with patch.dict("os.environ", {"DATABASE_URL": stub_url}):
            with patch.object(script, "_build_engine", side_effect=fake_build_engine):
                script.main(["--confirm"])

        assert captured["url"] == stub_url

    def test_missing_database_url_exits(self, script):
        import os
        env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
        with patch.dict("os.environ", env, clear=True):
            with pytest.raises(SystemExit) as exc:
                script.main(["--confirm"])
        assert exc.value.code != 0
