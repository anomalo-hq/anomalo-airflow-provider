import pytest

from airflow.exceptions import AirflowException

from airflow.providers.anomalo.hooks.anomalo import AnomaloHook
from airflow.models.connection import Connection


def test_get_conn(mocker):
    hook = AnomaloHook()
    get_connection = mocker.patch.object(
        hook,
        "get_connection",
        return_value=Connection(host="foo", extra={"api_token": "bar"}),
    )
    mock_client = mocker.patch("airflow.providers.anomalo.hooks.anomalo.Client")

    hook.get_conn()
    get_connection.assert_called()
    mock_client.assert_called_with(api_token="bar", host="foo")


def test_get_conn_falls_back_to_password(mocker):
    hook = AnomaloHook()
    mocker.patch.object(
        hook, "get_connection", return_value=Connection(host="foo", password="secret")
    )
    mock_client = mocker.patch("airflow.providers.anomalo.hooks.anomalo.Client")

    hook.get_conn()
    mock_client.assert_called_with(api_token="secret", host="foo")


def test_get_conn_prefers_the_api_token_extra(mocker):
    hook = AnomaloHook()
    mocker.patch.object(
        hook,
        "get_connection",
        return_value=Connection(
            host="foo", password="secret", extra={"api_token": "bar"}
        ),
    )
    mock_client = mocker.patch("airflow.providers.anomalo.hooks.anomalo.Client")

    hook.get_client()
    mock_client.assert_called_with(api_token="bar", host="foo")


def test_get_conn_without_a_token_raises(mocker):
    hook = AnomaloHook()
    mocker.patch.object(hook, "get_connection", return_value=Connection(host="foo"))
    mocker.patch("airflow.providers.anomalo.hooks.anomalo.Client")

    with pytest.raises(AirflowException, match="no API token"):
        hook.get_conn()
