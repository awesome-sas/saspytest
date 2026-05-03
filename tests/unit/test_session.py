"""
Unit tests for session management utilities.
"""

# pylint: disable=protected-access
from unittest.mock import patch, MagicMock

import pytest

import saspytest.session as session_module

pytest_plugins = ["pytester"]


class TestFindSaspytestConfig:
    def test_finds_in_cwd(self, tmp_path):
        (tmp_path / "saspytest_config.py").write_text("# config")
        with patch.object(session_module.pathlib.Path, "cwd", return_value=tmp_path):
            result = session_module._find_saspytest_config()
        assert result == str(tmp_path / "saspytest_config.py")

    def test_finds_in_parent(self, tmp_path):
        child = tmp_path / "subdir"
        child.mkdir()
        (tmp_path / "saspytest_config.py").write_text("# config")
        with patch.object(session_module.pathlib.Path, "cwd", return_value=child):
            result = session_module._find_saspytest_config()
        assert result == str(tmp_path / "saspytest_config.py")

    def test_not_found(self, tmp_path):
        with patch.object(session_module.pathlib.Path, "cwd", return_value=tmp_path):
            result = session_module._find_saspytest_config()
        assert result is None

    def test_old_saspy_filename_is_not_discovered(self, tmp_path):
        (tmp_path / "saspy_personal.py").write_text("# saspy config")
        with patch.object(session_module.pathlib.Path, "cwd", return_value=tmp_path):
            result = session_module._find_saspytest_config()
        assert result is None

    def test_cwd_takes_priority_over_parent(self, tmp_path):
        child = tmp_path / "subdir"
        child.mkdir()
        (tmp_path / "saspytest_config.py").write_text("# parent config")
        (child / "saspytest_config.py").write_text("# child config")
        with patch.object(session_module.pathlib.Path, "cwd", return_value=child):
            result = session_module._find_saspytest_config()
        assert result == str(child / "saspytest_config.py")


class TestResolveConfigSource:
    def test_from_env(self, monkeypatch):
        monkeypatch.setenv("SASPY_CONFIG", "/path/to/cfg.py")
        monkeypatch.setenv("SASPY_CFGNAME", "oda")
        cfgfile, cfgname = session_module._resolve_config_source()
        assert cfgfile == "/path/to/cfg.py"
        assert cfgname == "oda"

    def test_env_takes_priority_over_file(self, monkeypatch, tmp_path):
        monkeypatch.setenv("SASPY_CONFIG", "/path/to/cfg.py")
        monkeypatch.delenv("SASPY_CFGNAME", raising=False)
        (tmp_path / "saspytest_config.py").write_text("# config")
        with patch.object(session_module.pathlib.Path, "cwd", return_value=tmp_path):
            cfgfile, cfgname = session_module._resolve_config_source()
        assert cfgfile == "/path/to/cfg.py"
        assert cfgname is None

    def test_no_env_no_file(self, monkeypatch):
        monkeypatch.delenv("SASPY_CONFIG", raising=False)
        monkeypatch.delenv("SASPY_CFGNAME", raising=False)
        with patch.object(session_module, "_find_saspytest_config", return_value=None):
            cfgfile, cfgname = session_module._resolve_config_source()
        assert cfgfile is None
        assert cfgname is None

    def test_no_env_uses_discovered_file(self, monkeypatch):
        monkeypatch.delenv("SASPY_CONFIG", raising=False)
        monkeypatch.delenv("SASPY_CFGNAME", raising=False)
        discovered = "/proj/saspytest_config.py"
        with patch.object(session_module, "_find_saspytest_config", return_value=discovered):
            cfgfile, cfgname = session_module._resolve_config_source()
        assert cfgfile == "/proj/saspytest_config.py"
        assert cfgname is None


class TestGetSasSession:
    def test_creates_session_if_none(self):
        # Reset global state
        session_module._session_container["session"] = None
        mock_sas = MagicMock()

        with patch.object(session_module, "_create_session", return_value=mock_sas):
            result = session_module.get_sas_session()

        assert result is mock_sas
        assert session_module._session_container["session"] is mock_sas

    def test_reuses_existing_session(self):
        mock_sas = MagicMock()
        session_module._session_container["session"] = mock_sas

        with patch.object(session_module, "_create_session") as mock_create:
            result = session_module.get_sas_session()

        assert result is mock_sas
        mock_create.assert_not_called()


class TestCloseSasSession:
    def test_closes_and_clears(self):
        mock_sas = MagicMock()
        session_module._session_container["session"] = mock_sas

        session_module.close_sas_session()

        mock_sas.endsas.assert_called_once()
        assert session_module._session_container["session"] is None

    def test_noop_when_none(self):
        session_module._session_container["session"] = None
        session_module.close_sas_session()  # Should not raise

    def test_teardown_failure_still_clears_container(self):
        mock_sas = MagicMock()
        mock_sas.endsas.side_effect = RuntimeError("teardown failed")
        session_module._session_container["session"] = mock_sas

        with pytest.raises(RuntimeError, match="teardown failed"):
            session_module.close_sas_session()

        assert session_module._session_container["session"] is None


class TestResetTestState:
    def test_uses_supported_macro_dictionary(self):
        mock_sas = MagicMock()

        session_module.reset_test_state(mock_sas)

        submitted = mock_sas.submit.call_args[0][0]
        assert "set sashelp.vmacro" in submitted
        assert "catx(' ', '%nrstr(%symdel)'" in submitted
        assert "delete SASPYTEST_:" in submitted
        assert "DELETE_TEST_DATASETS" not in submitted
        assert "CLEANUP_TEST_MACROS" not in submitted


class TestCleanupTestArtifacts:
    def test_delegates_to_reset_test_state(self):
        mock_sas = MagicMock()

        with patch.object(session_module, "reset_test_state") as reset:
            session_module.cleanup_test_artifacts(mock_sas)

        reset.assert_called_once_with(mock_sas)


class TestCreateSession:
    def test_with_config(self, monkeypatch):
        monkeypatch.setenv("SASPY_CONFIG", "/cfg.py")
        monkeypatch.setenv("SASPY_CFGNAME", "oda")
        mock_sas = MagicMock()

        with patch("saspy.SASsession", return_value=mock_sas) as mock_cls:
            result = session_module._create_session()

        mock_cls.assert_called_once_with(cfgfile="/cfg.py", cfgname="oda")
        assert result is mock_sas

    def test_without_config(self, monkeypatch):
        monkeypatch.delenv("SASPY_CONFIG", raising=False)
        monkeypatch.delenv("SASPY_CFGNAME", raising=False)
        mock_sas = MagicMock()

        with patch.object(session_module, "_find_saspytest_config", return_value=None):
            with patch("saspy.SASsession", return_value=mock_sas) as mock_cls:
                result = session_module._create_session()

        mock_cls.assert_called_once_with()
        assert result is mock_sas


class TestResetSasSession:
    def test_closes_and_reopens(self):
        mock_old = MagicMock()
        mock_new = MagicMock()
        session_module._session_container["session"] = mock_old

        with patch.object(session_module, "_create_session", return_value=mock_new):
            result = session_module.reset_sas_session()

        mock_old.endsas.assert_called_once()
        assert result is mock_new
        assert session_module._session_container["session"] is mock_new


class TestCreateNewSasSession:
    def test_independent_session(self):
        mock_new = MagicMock()
        session_module._session_container["session"] = MagicMock()  # existing

        with patch.object(session_module, "_create_session", return_value=mock_new):
            result = session_module.create_new_sas_session()

        assert result is mock_new
        # existing session should be untouched
        assert session_module._session_container["session"] is not mock_new


def test_require_new_session_closes_when_setup_cleanup_fails(pytester):
    pytester.makeconftest("""
        from pathlib import Path
        import saspy


        def record(value):
            with Path("calls.log").open("a", encoding="utf-8") as stream:
                stream.write(value + "\\n")


        class FakeSAS:
            def submit(self, code):
                record("SUBMIT")
                raise RuntimeError("reset failed")

            def endsas(self):
                record("ENDSESSION")


        saspy.SASsession = FakeSAS
        """)
    pytester.makepyfile(test_new="""
        def test_new_session(require_new_sas_session):
            assert require_new_sas_session
        """)

    result = pytester.runpytest()

    result.assert_outcomes(errors=1)
    calls = (pytester.path / "calls.log").read_text(encoding="utf-8")
    assert "SUBMIT" in calls
    assert "ENDSESSION" in calls
