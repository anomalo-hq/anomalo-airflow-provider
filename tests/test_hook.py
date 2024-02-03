import pytest

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
