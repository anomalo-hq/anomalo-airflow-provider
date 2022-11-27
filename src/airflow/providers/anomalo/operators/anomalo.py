from datetime import date, timedelta

from airflow.models import BaseOperator

from airflow import AirflowException
from airflow.providers.anomalo.hooks.anomalo import AnomaloHook


class AnomaloPassFailOperator(BaseOperator):
    """
    Validate whether checks on a given table pass or fail.

    :param table_name: the full name of the table in Anomalo.
    :param must_pass: a list of checks that must pass for this task to succeed.
    :param anomalo_conn_id: (Optional) The connection ID used to connect to Anomalo.
    """

    def __init__(
        self, table_name, must_pass, anomalo_conn_id="anomalo_default", *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.anomalo_conn_id = anomalo_conn_id
        self.table_name = table_name
        self.must_pass = must_pass

    def execute(self, context):
        api_client = AnomaloHook(anomalo_conn_id=self.anomalo_conn_id).get_client()
        today = date.today() - timedelta(days=1)
        d1 = today.strftime("%Y-%m-%d")
        table_id = api_client.get_table_information(table_name=self.table_name)["id"]
        my_job_id = api_client.get_check_intervals(
            table_id=table_id, start=d1, end=None
        )[0]["latest_run_checks_job_id"]
        results = api_client.get_run_result(job_id=my_job_id)

        check_runs = results["check_runs"]
        failed_check_types = {
            check_type
            for check_run in check_runs
            if (check_type := check_run["run_config"]["_metadata"]["check_type"])
            in self.must_pass
            and not (check_run["results"]["success"])
        }

        if failed_check_types:
            self.log.error(
                f"check type(s): {', '.join(failed_check_types)} for table {self.table_name} did not pass"
            )
            raise AirflowException("Anomalo checks have failed")

        return results


class AnomaloRunCheckOperator(BaseOperator):
    """
    Triggers a job that runs all the checks on a given table.
    Execution returns the job id of the run.

    :param table_name: the full name of the table in Anomalo.
    :param anomalo_conn_id: (Optional) The connection ID used to connect to Anomalo.
    """

    def __init__(self, table_name, anomalo_conn_id="anomalo_default", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.anomalo_conn_id = anomalo_conn_id
        self.table_name = table_name

    def execute(self, context):
        api_client = AnomaloHook(anomalo_conn_id=self.anomalo_conn_id).get_client()

        table_id = api_client.get_table_information(table_name=self.table_name)["id"]
        run = api_client.run_checks(table_id=table_id)
        self.log.info(f"Triggered Anomalo checks for {self.table_name}")
        return run["run_checks_job_id"]
