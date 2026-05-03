"""
Unit tests for file handling utilities.
"""

import pytest

from saspytest.files import upload_file, download_file, submit_sas_file


class TestUploadFile:
    def test_success_none_result(self, mock_sas):
        mock_sas.upload.return_value = None
        assert upload_file(mock_sas, "/local/path", "/remote/path") is True

    def test_success_dict_result(self, mock_sas):
        mock_sas.upload.return_value = {"Success": True}
        assert upload_file(mock_sas, "/local/path", "/remote/path") is True

    def test_failure(self, mock_sas):
        mock_sas.upload.return_value = {"Success": False}
        assert upload_file(mock_sas, "/local/path", "/remote/path") is False

    @pytest.mark.parametrize("result", [{}, {"success": True}, {"Success": 0}])
    def test_missing_or_falsey_success_value(self, mock_sas, result):
        mock_sas.upload.return_value = result
        assert upload_file(mock_sas, "/local/path", "/remote/path") is False

    def test_unexpected_result_type(self, mock_sas):
        mock_sas.upload.return_value = "unexpected"
        assert upload_file(mock_sas, "/local/path", "/remote/path") is False

    def test_forwards_overwrite(self, mock_sas):
        mock_sas.upload.return_value = None
        assert upload_file(mock_sas, "/local/path", "/remote/path", overwrite=False) is True
        mock_sas.upload.assert_called_once_with("/local/path", "/remote/path", overwrite=False)

    def test_propagates_saspy_exception(self, mock_sas):
        mock_sas.upload.side_effect = OSError("upload failed")
        with pytest.raises(OSError, match="upload failed"):
            upload_file(mock_sas, "/local/path", "/remote/path")


class TestDownloadFile:
    def test_success_none_result(self, mock_sas):
        mock_sas.download.return_value = None
        assert download_file(mock_sas, "/local/path", "/remote/path") is True

    def test_success_dict_result(self, mock_sas):
        mock_sas.download.return_value = {"Success": True}
        assert download_file(mock_sas, "/local/path", "/remote/path") is True

    def test_failure(self, mock_sas):
        mock_sas.download.return_value = {"Success": False}
        assert download_file(mock_sas, "/local/path", "/remote/path") is False

    @pytest.mark.parametrize("result", [{}, {"success": True}, {"Success": 0}])
    def test_missing_or_falsey_success_value(self, mock_sas, result):
        mock_sas.download.return_value = result
        assert download_file(mock_sas, "/local/path", "/remote/path") is False

    def test_forwards_overwrite(self, mock_sas):
        mock_sas.download.return_value = None
        assert download_file(mock_sas, "/local/path", "/remote/path", overwrite=False) is True
        mock_sas.download.assert_called_once_with("/local/path", "/remote/path", overwrite=False)

    def test_rejects_existing_local_file_without_overwrite(self, mock_sas, tmp_path):
        local_path = tmp_path / "existing.txt"
        local_path.write_text("existing", encoding="utf-8")

        assert download_file(mock_sas, str(local_path), "/remote/path", overwrite=False) is False
        mock_sas.download.assert_not_called()

    def test_propagates_saspy_exception(self, mock_sas):
        mock_sas.download.side_effect = OSError("download failed")
        with pytest.raises(OSError, match="download failed"):
            download_file(mock_sas, "/local/path", "/remote/path")


class TestSubmitSasFile:
    def test_submits_file_content(self, mock_sas, tmp_path):
        sas_file = tmp_path / "test.sas"
        sas_file.write_text("data test; run;", encoding="utf-8")
        mock_sas.submit.return_value = {"LOG": "NOTE: OK", "LST": ""}

        result = submit_sas_file(mock_sas, sas_file)

        mock_sas.submit.assert_called_once_with("data test; run;")
        assert result == {"LOG": "NOTE: OK", "LST": ""}

    def test_file_not_found(self, mock_sas, tmp_path):
        missing = tmp_path / "missing.sas"
        with pytest.raises(FileNotFoundError, match="SAS file not found"):
            submit_sas_file(mock_sas, missing)

    def test_directory_is_rejected(self, mock_sas, tmp_path):
        with pytest.raises(FileNotFoundError, match="SAS file not found"):
            submit_sas_file(mock_sas, tmp_path)

    def test_propagates_decoding_error(self, mock_sas, tmp_path):
        sas_file = tmp_path / "invalid.sas"
        sas_file.write_bytes(b"\xff")
        with pytest.raises(UnicodeDecodeError):
            submit_sas_file(mock_sas, sas_file)

    def test_propagates_read_error(self, mock_sas, tmp_path, mocker):
        sas_file = tmp_path / "unreadable.sas"
        sas_file.write_text("data test; run;", encoding="utf-8")
        mocker.patch("pathlib.Path.read_text", side_effect=PermissionError("denied"))
        with pytest.raises(PermissionError, match="denied"):
            submit_sas_file(mock_sas, sas_file)

    def test_accepts_empty_file(self, mock_sas, tmp_path):
        sas_file = tmp_path / "empty.sas"
        sas_file.write_text("", encoding="utf-8")
        expected_result = {"LOG": "", "LST": ""}
        mock_sas.submit.return_value = expected_result

        result = submit_sas_file(mock_sas, sas_file)

        mock_sas.submit.assert_called_once_with("")
        assert result is expected_result

    def test_accepts_readable_non_sas_file(self, mock_sas, tmp_path):
        source_file = tmp_path / "program.txt"
        source_file.write_text("%put NOTE: OK;", encoding="utf-8")
        mock_sas.submit.return_value = {"LOG": "NOTE: OK", "LST": ""}

        submit_sas_file(mock_sas, source_file)

        mock_sas.submit.assert_called_once_with("%put NOTE: OK;")

    def test_propagates_submit_exception(self, mock_sas, tmp_path):
        sas_file = tmp_path / "test.sas"
        sas_file.write_text("data test; run;", encoding="utf-8")
        mock_sas.submit.side_effect = RuntimeError("submit failed")

        with pytest.raises(RuntimeError, match="submit failed"):
            submit_sas_file(mock_sas, sas_file)

    def test_accepts_string_path(self, mock_sas, tmp_path):
        sas_file = tmp_path / "test.sas"
        sas_file.write_text("proc print; run;", encoding="utf-8")
        mock_sas.submit.return_value = {"LOG": "", "LST": ""}

        submit_sas_file(mock_sas, str(sas_file))

        mock_sas.submit.assert_called_once_with("proc print; run;")
