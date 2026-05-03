"""
Dataset and library assertions for SAS testing with saspy.

This module provides assertion functions for validating SAS datasets,
libraries, and data structures.
"""

from typing import Any, List, Optional
import uuid

import saspy

from ._identifiers import validate_sas_identifier


def _temporary_name(kind: str) -> str:
    """Create a valid, collision-resistant name for a per-call SAS artifact."""
    return f"SASPYTEST_{kind}_{uuid.uuid4().hex[:12].upper()}"


def _required_macro_value(
    sas: saspy.SASsession, name: str, description: str, msg: Optional[str] = None
) -> str:
    """Read a required SAS macro value and report failed metadata collection clearly."""
    value = sas.symget(name)
    if value is None or not str(value).strip():
        detail = f"SAS did not produce the expected macro variable {name}"
        raise AssertionError(msg or f"Unable to determine {description}: {detail}")
    return str(value).strip()


def _dataset_missing_message(dataset: str, libref: str) -> str:
    return f"Dataset {libref}.{dataset} was not found"


def assert_dataset_exists(
    sas: saspy.SASsession, dataset: str, libref: str = "WORK", msg: Optional[str] = None
) -> None:
    """
    Assert that a SAS dataset exists.

    Args:
        sas: SAS session instance
        dataset: Dataset name
        libref: Library reference (default: WORK)
        msg: Optional custom error message

    Raises:
        AssertionError: If dataset doesn't exist

    Example:
        >>> sas.submit("data test; x=1; run;")
        >>> assert_dataset_exists(sas, "test")
    """
    validate_sas_identifier(dataset, "dataset")
    validate_sas_identifier(libref, "libref", max_length=8)
    result_name = _temporary_name("DSEXIST")
    code = f"""
        %let {result_name} = %sysfunc(exist({libref}.{dataset}));
    """
    sas.submit(code)
    exists = _required_macro_value(sas, result_name, f"whether {libref}.{dataset} exists", msg)

    if msg is None:
        msg = f"Dataset {libref}.{dataset} should exist but was not found"

    assert exists == "1", msg


def assert_dataset_not_exists(
    sas: saspy.SASsession, dataset: str, libref: str = "WORK", msg: Optional[str] = None
) -> None:
    """
    Assert that a SAS dataset does NOT exist.

    Args:
        sas: SAS session instance
        dataset: Dataset name
        libref: Library reference (default: WORK)
        msg: Optional custom error message

    Raises:
        AssertionError: If dataset exists

    Example:
        >>> assert_dataset_not_exists(sas, "nonexistent")
    """
    validate_sas_identifier(dataset, "dataset")
    validate_sas_identifier(libref, "libref", max_length=8)
    result_name = _temporary_name("DSEXIST")
    code = f"""
        %let {result_name} = %sysfunc(exist({libref}.{dataset}));
    """
    sas.submit(code)
    exists = _required_macro_value(sas, result_name, f"whether {libref}.{dataset} exists", msg)

    if msg is None:
        msg = f"Dataset {libref}.{dataset} should not exist but was found"

    assert exists == "0", msg


def assert_library_exists(sas: saspy.SASsession, libref: str, msg: Optional[str] = None) -> None:
    """
    Assert that a SAS library exists and is assigned.

    Args:
        sas: SAS session instance
        libref: Library reference name
        msg: Optional custom error message

    Raises:
        AssertionError: If library doesn't exist

    Example:
        >>> assert_library_exists(sas, "WORK")
    """
    validate_sas_identifier(libref, "libref", max_length=8)
    result_name = _temporary_name("LIBEXIST")
    code = f"""
        %let {result_name} = %sysfunc(libref({libref}));
    """
    sas.submit(code)
    result = _required_macro_value(sas, result_name, f"whether library {libref} exists", msg)

    if msg is None:
        msg = f"Library {libref} should exist but was not assigned"

    # libref() returns 0 if library exists
    assert result == "0", msg


def assert_record_count(
    sas: saspy.SASsession,
    dataset: str,
    expected_count: int,
    libref: str = "WORK",
    msg: Optional[str] = None,
) -> None:
    """
    Assert that a dataset has the expected number of observations.

    Args:
        sas: SAS session instance
        dataset: Dataset name
        expected_count: Expected number of observations
        libref: Library reference (default: WORK)
        msg: Optional custom error message

    Raises:
        AssertionError: If record count doesn't match

    Example:
        >>> sas.submit("data test; do i=1 to 5; output; end; run;")
        >>> assert_record_count(sas, "test", 5)
    """
    validate_sas_identifier(dataset, "dataset")
    validate_sas_identifier(libref, "libref", max_length=8)
    exists_name = _temporary_name("DSEXIST")
    count_name = _temporary_name("NOBS")
    code = f"""
        %let {exists_name} = %sysfunc(exist({libref}.{dataset}));
        %if &{exists_name} = 1 %then %do;
            data _null_;
                if 0 then set {libref}.{dataset} nobs=count;
                call symputx('{count_name}', count);
                stop;
            run;
        %end;
    """
    sas.submit(code)
    exists = _required_macro_value(sas, exists_name, f"whether {libref}.{dataset} exists", msg)
    if exists != "1":
        raise AssertionError(msg or _dataset_missing_message(dataset, libref))

    count_value = _required_macro_value(
        sas, count_name, f"the record count for {libref}.{dataset}", msg
    )
    try:
        actual_count = int(count_value)
    except ValueError as exc:
        raise AssertionError(
            msg or f"SAS returned an invalid record count for {libref}.{dataset}: {count_value!r}"
        ) from exc

    if msg is None:
        msg = (
            f"Dataset {libref}.{dataset} expected {expected_count} observations, got {actual_count}"
        )

    assert actual_count == expected_count, msg


def assert_columns_exist(
    sas: saspy.SASsession,
    dataset: str,
    columns: List[str],
    libref: str = "WORK",
    msg: Optional[str] = None,
) -> None:
    """
    Assert that specific columns exist in a dataset.

    Args:
        sas: SAS session instance
        dataset: Dataset name
        columns: List of column names to check
        libref: Library reference (default: WORK)
        msg: Optional custom error message

    Raises:
        AssertionError: If any column is missing

    Example:
        >>> sas.submit("data test; x=1; y=2; run;")
        >>> assert_columns_exist(sas, "test", ["x", "y"])
    """
    validate_sas_identifier(dataset, "dataset")
    validate_sas_identifier(libref, "libref", max_length=8)
    for index, column in enumerate(columns):
        validate_sas_identifier(column, f"columns[{index}]")
    exists_name = _temporary_name("DSEXIST")
    columns_name = _temporary_name("COLS")
    allvars_name = _temporary_name("ALLVARS")
    code = f"""
        %let {exists_name} = %sysfunc(exist({libref}.{dataset}));
        %if &{exists_name} = 1 %then %do;
            proc contents data={libref}.{dataset} out={columns_name} noprint;
            run;

            data _null_;
                set {columns_name} end=eof;
                length allvars $32767;
                retain allvars '';
                allvars = catx(' ', allvars, upcase(name));
                if eof then call symputx('{allvars_name}', allvars);
            run;
        %end;
    """
    sas.submit(code)
    exists = _required_macro_value(sas, exists_name, f"whether {libref}.{dataset} exists", msg)
    if exists != "1":
        raise AssertionError(msg or _dataset_missing_message(dataset, libref))

    all_vars = _required_macro_value(sas, allvars_name, f"the columns for {libref}.{dataset}", msg)
    all_vars = all_vars.upper().split()

    missing = [col for col in columns if col.upper() not in all_vars]

    if msg is None:
        msg = f"Dataset {libref}.{dataset} missing columns: {missing}"

    assert len(missing) == 0, msg


def assert_datasets_equal(
    sas: saspy.SASsession,
    dataset1: str,
    dataset2: str,
    libref1: str = "WORK",
    libref2: str = "WORK",
    msg: Optional[str] = None,
) -> None:
    """
    Assert that two datasets are equal (same data and structure).

    Uses PROC COMPARE to check for differences.

    Args:
        sas: SAS session instance
        dataset1: First dataset name
        dataset2: Second dataset name
        libref1: Library for first dataset (default: WORK)
        libref2: Library for second dataset (default: WORK)
        msg: Optional custom error message

    Raises:
        AssertionError: If datasets are different

    Example:
        >>> sas.submit("data test1; x=1; run; data test2; x=1; run;")
        >>> assert_datasets_equal(sas, "test1", "test2")
    """
    validate_sas_identifier(dataset1, "dataset1")
    validate_sas_identifier(dataset2, "dataset2")
    validate_sas_identifier(libref1, "libref1", max_length=8)
    validate_sas_identifier(libref2, "libref2", max_length=8)
    exists1_name = _temporary_name("DSEXIST")
    exists2_name = _temporary_name("DSEXIST")
    diff_name = _temporary_name("DIFF")
    sysinfo_name = _temporary_name("SYSINFO")
    code = f"""
        %let {exists1_name} = %sysfunc(exist({libref1}.{dataset1}));
        %let {exists2_name} = %sysfunc(exist({libref2}.{dataset2}));
        %if &{exists1_name} = 1 and &{exists2_name} = 1 %then %do;
            proc compare base={libref1}.{dataset1}
                         compare={libref2}.{dataset2}
                         out={diff_name} outnoequal outbase outcomp;
            run;

            %let {sysinfo_name} = &sysinfo;
        %end;
    """
    sas.submit(code)
    exists1 = _required_macro_value(sas, exists1_name, f"whether {libref1}.{dataset1} exists", msg)
    if exists1 != "1":
        raise AssertionError(msg or _dataset_missing_message(dataset1, libref1))

    exists2 = _required_macro_value(sas, exists2_name, f"whether {libref2}.{dataset2} exists", msg)
    if exists2 != "1":
        raise AssertionError(msg or _dataset_missing_message(dataset2, libref2))

    sysinfo_value = _required_macro_value(sas, sysinfo_name, "the PROC COMPARE SYSINFO value", msg)
    try:
        sysinfo = int(sysinfo_value)
    except ValueError as exc:
        raise AssertionError(
            msg or f"SAS returned an invalid PROC COMPARE SYSINFO value: {sysinfo_value!r}"
        ) from exc

    if msg is None:
        msg = (
            f"Datasets {libref1}.{dataset1} and {libref2}.{dataset2} "
            f"are not equal (SYSINFO={sysinfo})"
        )

    # SYSINFO=0 means datasets are equal
    assert sysinfo == 0, msg


def get_dataset_as_df(sas: saspy.SASsession, dataset: str, libref: str = "WORK") -> Any:
    """
    Get a SAS dataset as a pandas DataFrame.

    Args:
        sas: SAS session instance
        dataset: Dataset name
        libref: Library reference (default: WORK)

    Returns:
        pandas.DataFrame: Dataset contents

    Example:
        >>> df = get_dataset_as_df(sas, "test")
        >>> assert len(df) == 5
    """
    validate_sas_identifier(dataset, "dataset")
    validate_sas_identifier(libref, "libref", max_length=8)
    return sas.sd2df(dataset, libref)
