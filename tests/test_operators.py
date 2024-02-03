from typing import List, Mapping, Tuple
import pytest

from datetime import date

from airflow.exceptions import AirflowException
from airflow.providers.anomalo.operators.anomalo import (
    AnomaloPassFailOperator,
    AnomaloRunCheckOperator,
    AnomaloCheckRunResultOperator,
)


def test_run_check_operator(mocker):
    mock_hook = mocker.patch("airflow.providers.anomalo.operators.anomalo.AnomaloHook")
    mock_client = mock_hook.return_value.get_client.return_value = mocker.MagicMock()

    mock_client.get_table_information.return_value = {"id": "foo_id"}
    mock_client.run_checks.return_value = {"run_checks_job_id": "anomalo_job_id"}

    run_check = AnomaloRunCheckOperator(
        table_name="foo", run_date=date(2023, 2, 1), task_id="bar"
    )

    assert run_check.execute(context=None) == "anomalo_job_id"
    mock_client.get_table_information.assert_called_with(table_name="foo")
    mock_client.run_checks.assert_called_with(
        table_id="foo_id", interval_id="2023-02-01", check_ids=None
    )


@pytest.mark.parametrize(
    "status_checker, expect_passes", [(lambda x: True, True), (lambda x: False, False)]
)
def test_check_run_result_operator(mocker, status_checker, expect_passes):
    mock_hook = mocker.patch("airflow.providers.anomalo.operators.anomalo.AnomaloHook")
    mock_client = mock_hook.return_value.get_client.return_value = mocker.MagicMock()

    mock_client.get_table_information.return_value = {"id": "foo_id"}
    mock_client.get_check_intervals.return_value = [
        {"latest_run_checks_job_id": "anomalo_job_id"}
    ]
    run_result_mock = mocker.MagicMock()
    mock_client.get_run_result.return_value = run_result_mock

    check_run = AnomaloCheckRunResultOperator(
        table_name="foo",
        run_date=date(2023, 2, 1),
        task_id="bar",
        status_checker=status_checker,
    )

    try:
        results = check_run.execute(context=None)
        actual_passes = True
    except AirflowException:
        actual_passes = False

    mock_client.get_table_information.assert_called_with(table_name="foo")
    mock_client.get_check_intervals.assert_called_with(
        table_id="foo_id", start="2023-02-01", end=None
    )
    mock_client.get_run_result.assert_called_with(job_id="anomalo_job_id")

    assert actual_passes == expect_passes

    if actual_passes:
        assert results == run_result_mock


def create_mock_run_result(type_to_success: List[Tuple[str, bool]]) -> Mapping:
    runs = []
    for check_type, success in type_to_success:
        runs.append(
            {
                "run_config": {"_metadata": {"check_type": check_type}},
                "results": {"success": success},
            }
        )
    return {"check_runs": runs}


@pytest.mark.parametrize(
    "results, must_pass, expect_passes",
    [
        (create_mock_run_result([("rule", True)]), ["rule"], True),
        (create_mock_run_result([("rule", True), ("rule", False)]), ["rule"], False),
        (create_mock_run_result([("rule", True), ("metric", False)]), ["rule"], True),
        (
            create_mock_run_result([("rule", True), ("metric", False)]),
            ["rule", "metric"],
            False,
        ),
    ],
)
def test_check_pass_fail_operator(mocker, results, must_pass, expect_passes):
    print(results)

    check_pass = AnomaloPassFailOperator(
        table_name="foo", run_date=date(2023, 2, 1), must_pass=must_pass, task_id="bar"
    )

    actual_passes = check_pass.status_checker(results=results)
    assert actual_passes == expect_passes
