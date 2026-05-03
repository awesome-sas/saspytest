"""Live-SAS coverage for file transfers and SAS file submission."""

from uuid import uuid4

import pytest

from saspytest import assert_no_errors, download_file, submit_sas_file, upload_file

pytestmark = pytest.mark.integration


def test_upload_and_download_return_values_and_overwrite_rejection(sas_session, tmp_path):
    """Validate transfer status values, content, and overwrite protection."""
    sas = sas_session
    source = tmp_path / "source.txt"
    downloaded = tmp_path / "downloaded.txt"
    remote = f"/tmp/SASPYTEST_FILE_{uuid4().hex}.txt"
    content = "SASPYTEST upload content\n"
    source.write_text(content, encoding="utf-8")

    try:
        assert upload_file(sas, str(source), remote) is True
        assert upload_file(sas, str(source), remote, overwrite=False) is False

        assert download_file(sas, str(downloaded), remote) is True
        assert downloaded.read_text(encoding="utf-8") == content

        downloaded.write_text("existing content\n", encoding="utf-8")
        assert download_file(sas, str(downloaded), remote, overwrite=False) is False
        assert download_file(sas, str(downloaded), remote, overwrite=True) is True
        assert downloaded.read_text(encoding="utf-8") == content
    finally:
        sas.file_delete(remote, quiet=True)


def test_file_transfer_errors_are_not_reported_as_success(sas_session, tmp_path):
    """Validate false status results or propagated I/O errors for bad paths."""
    sas = sas_session
    missing_local = tmp_path / "missing.txt"
    missing_remote = f"/tmp/SASPYTEST_MISSING_{uuid4().hex}.txt"
    local_target = tmp_path / "downloaded.txt"

    try:
        try:
            upload_result = upload_file(sas, str(missing_local), missing_remote)
        except OSError:
            pass
        else:
            assert upload_result is False

        try:
            download_result = download_file(sas, str(local_target), missing_remote)
        except OSError:
            pass
        else:
            assert download_result is False
    finally:
        sas.file_delete(missing_remote, quiet=True)


def test_submit_sas_file_returns_log_and_listing(sas_session, tmp_path):
    """Validate that submit_sas_file exposes the SAS log and listing unchanged."""
    sas = sas_session
    sas_file = tmp_path / "submit_file.sas"
    sas_file.write_text(
        """
        data SASPYTEST_SUBMIT_FILE;
            value = 42;
        run;

        %put NOTE: SASPYTEST_SUBMIT_FILE completed;
        proc print data=SASPYTEST_SUBMIT_FILE noobs;
        run;
        """,
        encoding="utf-8",
    )

    result = submit_sas_file(sas, sas_file)

    assert set(result) >= {"LOG", "LST"}
    assert_no_errors(result["LOG"])
    assert "SASPYTEST_SUBMIT_FILE completed" in result["LOG"]
    assert "42" in result["LST"]
