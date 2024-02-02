import pytest

from datetime import date

from airflow.providers.anomalo.operators.anomalo import (AnomaloPassFailOperator, AnomaloRunCheckOperator, AnomaloCheckRunResultOperator)



def test_run_check_operator(mocker):
    mocker.patch('airflow.providers.anomalo.operators.anomalo.BaseOperator')
    mock_hook = mocker.patch("airflow.providers.anomalo.operators.anomalo.AnomaloHook")
    mock_client = mock_hook.return_value.get_client.return_value = mocker.MagicMock()

    mock_client.get_table_information.return_value = {'id': "foo_id"}
    mock_client.run_checks.return_value = {"run_checks_job_id": "anomalo_job_id"}

    run_check = AnomaloRunCheckOperator(table_name="foo", run_date=date(2023, 2, 1), task_id="bar")
    
    assert run_check.execute(context=None) == "anomalo_job_id"
    mock_client.get_table_information.assert_called_with(table_name="foo")
    mock_client.run_checks.assert_called_with(table_id="foo_id", interval_id="2023-02-01", check_ids=None)
    