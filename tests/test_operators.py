import pytest

from airflow.providers.anomalo.operators import AnomaloCheckRunResultOperator
from unittest.mock import patch
from typing import SimpleNamespace


def test_check_run_result_operator_passing():
    def mock_get_table_information(*, table_name):
        ...

    class MockHook:
        def __init__(self, *args, **kwargs):
            ...

        def get_client():
            return SimpleNamespace(get_table_information=mock_get_table_information)

    with patch("airflow.providers.anomalo.operators.anomalo.AnomaloHook", MockHook):
        ...
