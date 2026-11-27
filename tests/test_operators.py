from typing import List, Mapping, Tuple
import pytest

from datetime import date, datetime

from airflow.exceptions import AirflowException
from airflow.providers.anomalo.operators.anomalo import (
    AnomaloPassFailOperator,
    AnomaloRunCheckOperator,
    AnomaloCheckRunResultOperator,
    anomalo_today,
    resolve_run_date,
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
    check_pass = AnomaloPassFailOperator(
        table_name="foo", run_date=date(2023, 2, 1), must_pass=must_pass, task_id="bar"
    )

    actual_passes = check_pass.status_checker(results=results)
    assert actual_passes == expect_passes


@pytest.mark.parametrize(
    "run_date, expected",
    [
        (date(2026, 11, 1), "2026-11-01"),
        (datetime(2026, 11, 1, 5, 30), "2026-11-01"),
        ("2026-11-01", "2026-11-01"),
        (" 2026-11-01\n", "2026-11-01"),
    ],
)
def test_resolve_run_date(run_date, expected):
    assert resolve_run_date(run_date) == expected


@pytest.mark.parametrize("run_date", [None, ""])
def test_resolve_run_date_defaults_to_anomalo_today(run_date):
    assert resolve_run_date(run_date) == anomalo_today().strftime("%Y-%m-%d")


@pytest.mark.parametrize("run_date", ["01/11/2026", "2026-11-01T00:00:00", "yesterday"])
def test_resolve_run_date_rejects_other_strings(run_date):
    with pytest.raises(AirflowException, match="YYYY-MM-DD"):
        resolve_run_date(run_date)


@pytest.mark.parametrize(
    "operator_class",
    [AnomaloRunCheckOperator, AnomaloCheckRunResultOperator, AnomaloPassFailOperator],
)
def test_run_date_is_a_template_field(operator_class):
    assert "run_date" in operator_class.template_fields


def test_run_check_operator_accepts_a_string_run_date(mocker):
    mock_hook = mocker.patch("airflow.providers.anomalo.operators.anomalo.AnomaloHook")
    mock_client = mock_hook.return_value.get_client.return_value = mocker.MagicMock()

    mock_client.get_table_information.return_value = {"id": "foo_id"}
    mock_client.run_checks.return_value = {"run_checks_job_id": "anomalo_job_id"}

    run_check = AnomaloRunCheckOperator(
        table_name="foo", run_date="2023-02-01", task_id="bar"
    )

    assert run_check.execute(context=None) == "anomalo_job_id"
    mock_client.run_checks.assert_called_with(
        table_id="foo_id", interval_id="2023-02-01", check_ids=None
    )


def test_run_date_renders_through_airflow_templating():
    import pendulum
    from airflow import macros

    try:
        from airflow.sdk import DAG
    except ImportError:
        from airflow.models import DAG

    with DAG(
        dag_id="templated_run_date",
        start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
        schedule=None,
    ):
        lagged = AnomaloRunCheckOperator(
            task_id="lagged",
            table_name="w.s.t",
            run_date="{{ macros.ds_add(ds, -2) }}",
        )
        logical_day = AnomaloPassFailOperator(
            task_id="logical_day", table_name="w.s.t", must_pass=[], run_date="{{ ds }}"
        )
        fixed = AnomaloRunCheckOperator(
            task_id="fixed", table_name="w.s.t", run_date=date(2026, 10, 1)
        )

    context = {"ds": "2026-11-03", "macros": macros}
    for task in (lagged, logical_day, fixed):
        task.render_template_fields(context)

    assert resolve_run_date(lagged.run_date) == "2026-11-01"
    assert resolve_run_date(logical_day.run_date) == "2026-11-03"
    # A date passed directly is left alone by templating.
    assert fixed.run_date == date(2026, 10, 1)
