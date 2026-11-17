"""Run the example DAG end to end with a fake Anomalo client.

The unit tests call each operator directly with a mocked context, so they
cannot tell whether an operator works inside a real Airflow task run. Here
Airflow runs every task in the example DAG, passes the job id between tasks
through XCom, and reports the run's final state. Only the Anomalo API is faked.
"""

import importlib
import json

import pytest

from airflow.utils.state import DagRunState


JOB_ID = "job-123"


class FakeAnomaloClient:
    """Stands in for `anomalo.Client`, answering the calls the provider makes."""

    calls = []
    check_succeeds = True

    def __init__(self, api_token, host):
        self.api_token = api_token
        self.host = host

    def get_table_information(self, table_name):
        FakeAnomaloClient.calls.append(("get_table_information", table_name))
        return {"id": 42}

    def run_checks(self, table_id, interval_id, check_ids):
        FakeAnomaloClient.calls.append(("run_checks", table_id))
        return {"run_checks_job_id": JOB_ID}

    def get_run_result(self, job_id):
        FakeAnomaloClient.calls.append(("get_run_result", job_id))
        return {
            "check_runs": [
                {
                    "results_pending": False,
                    "run_config": {"_metadata": {"check_type": "rule"}},
                    "results": {"success": FakeAnomaloClient.check_succeeds},
                }
            ]
        }


@pytest.fixture
def fake_anomalo(monkeypatch):
    monkeypatch.setenv(
        "AIRFLOW_CONN_ANOMALO_DEFAULT",
        json.dumps(
            {
                "conn_type": "anomalo",
                "host": "https://anomalo.example.com",
                "extra": {"api_token": "test-token"},
            }
        ),
    )
    monkeypatch.setattr(
        "airflow.providers.anomalo.hooks.anomalo.Client", FakeAnomaloClient
    )
    FakeAnomaloClient.calls = []
    FakeAnomaloClient.check_succeeds = True
    return FakeAnomaloClient


@pytest.fixture
def dag():
    # Imported here rather than at the top, so a DAG that fails to import fails
    # these tests instead of stopping the whole test run from being collected.
    module = importlib.import_module(
        "airflow.providers.anomalo.example_dags.example_anomalo"
    )
    return module.dag


def test_example_dag_passes_the_job_id_between_tasks(airflow_db, fake_anomalo, dag):
    dag_run = dag.test()

    assert dag_run.state == DagRunState.SUCCESS
    # The sensor and the pass/fail operator each read the job id that the
    # run-check task pushed to XCom.
    assert fake_anomalo.calls.count(("get_run_result", JOB_ID)) == 2


def test_example_dag_fails_when_a_required_check_fails(airflow_db, fake_anomalo, dag):
    fake_anomalo.check_succeeds = False

    dag_run = dag.test()

    assert dag_run.state == DagRunState.FAILED
    assert ("get_run_result", JOB_ID) in fake_anomalo.calls
