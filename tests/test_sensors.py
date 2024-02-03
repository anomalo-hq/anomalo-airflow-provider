import pytest

from airflow.providers.anomalo.sensors.anomalo import AnomaloJobCompleteSensor


@pytest.mark.parametrize(
    "run_result, complete",
    [
        ({"check_runs": [{"results_pending": False}]}, True),
        ({"check_runs": [{"results_pending": True}]}, False),
    ],
)
def test_job_complete_sensor_true(mocker, run_result, complete):
    mock_hook = mocker.patch("airflow.providers.anomalo.sensors.anomalo.AnomaloHook")
    mock_client = mock_hook.return_value.get_client.return_value = mocker.MagicMock()

    sensor = AnomaloJobCompleteSensor(job_id="foo", task_id="bar")
    mock_client.get_run_result.return_value = run_result
    assert sensor.poke(context=None) == complete

    mock_client.get_run_result.assert_called_with("foo")


def test_job_complete_sensor_xcom(mocker):
    mock_hook = mocker.patch("airflow.providers.anomalo.sensors.anomalo.AnomaloHook")
    mock_client = mock_hook.return_value.get_client.return_value = mocker.MagicMock()
    mock_context = mocker.MagicMock()

    sensor = AnomaloJobCompleteSensor(xcom_job_id_task="foo_task", task_id="bar")
    xcom_pull = mocker.patch.object(sensor, "xcom_pull", return_value="foo")

    sensor.poke(context=mock_context)

    xcom_pull.assert_called()
    mock_client.get_run_result.assert_called_with("foo")
