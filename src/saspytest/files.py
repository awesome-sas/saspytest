"""
File handling utilities for SAS testing with saspy.

This module provides functions for uploading and downloading files
between the local filesystem and SAS server, along with helpers for
submitting SAS code stored in local files.
"""

from pathlib import Path
from typing import Dict, Union
import saspy


def upload_file(
    sas: saspy.SASsession, local_path: str, remote_path: str, overwrite: bool = True
) -> bool:
    """
    Upload a file from local filesystem to SAS server.

    Args:
        sas: SAS session instance
        local_path: Path to local file
        remote_path: Path on SAS server
        overwrite: Whether to overwrite existing file

    Returns:
        bool: True if upload successful

    Example:
        >>> upload_file(sas, "/tmp/data.csv", "/tmp/sas_data.csv")
    """
    result = sas.upload(local_path, remote_path, overwrite=overwrite)
    # upload() returns a dict with success info or None on success
    if result is None:
        return True
    if isinstance(result, dict):
        return bool(result.get("Success"))
    return False


def download_file(
    sas: saspy.SASsession, local_path: str, remote_path: str, overwrite: bool = True
) -> bool:
    """
    Download a file from SAS server to local filesystem.

    Args:
        sas: SAS session instance
        local_path: Path to save file locally
        remote_path: Path on SAS server
        overwrite: Whether to overwrite existing file

    Returns:
        bool: True if download successful

    Example:
        >>> download_file(sas, "/tmp/local.txt", "/tmp/remote.txt")
    """
    if not overwrite and Path(local_path).exists():
        return False

    result = sas.download(local_path, remote_path, overwrite=overwrite)
    # download() returns a dict with success info or None on success
    if result is None:
        return True
    if isinstance(result, dict):
        return bool(result.get("Success"))
    return False


def submit_sas_file(sas: saspy.SASsession, local_path: Union[str, Path]) -> Dict[str, str]:
    """
    Submit SAS code from a local .sas file using an existing SAS session.

    Args:
        sas: SAS session instance
        local_path: Path to local SAS file (.sas)

    Returns:
        Dict[str, str]: saspy submit() result with LOG and LST keys

    Raises:
        FileNotFoundError: If the SAS file does not exist

    Example:
        >>> result = submit_sas_file(sas, "sas_project/programs/greeter.sas")
        >>> log = result["LOG"]
    """
    path = Path(local_path)
    if not path.is_file():
        raise FileNotFoundError(f"SAS file not found: {path}")

    code = path.read_text(encoding="utf-8")
    return sas.submit(code)
