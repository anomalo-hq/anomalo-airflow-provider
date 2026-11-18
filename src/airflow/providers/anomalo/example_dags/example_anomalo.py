import pendulum


try:
    from airflow.sdk import DAG
except ImportError:
    from airflow.models import DAG
try:
    from airflow.providers.standard.operators.empty import EmptyOperator
except ImportError:
    from airflow.operators.empty import EmptyOperator
from airflow.providers.anomalo.operators.anomalo import (
    AnomaloPassFailOperator,
    AnomaloRunCheckOperator,
)
from airflow.providers.anomalo.sensors.anomalo import AnomaloJobCompleteSensor


args = {
    "owner": "AL",
    "start_date": pendulum.datetime(2024, 1, 1, tz="UTC"),
}

with DAG(
    dag_id="AnomaloDAG",
    default_args=args,
    description="Simple Anomalo Airflow operator example",
    schedule="@daily",
    catchup=False,
) as dag:
    ingest_transform_data = EmptyOperator(task_id="ingest_transform_data")

    my_table_name = "public-bq.austin_bikeshare.bikeshare_stations"

    anomalo_run = AnomaloRunCheckOperator(
        task_id="AnomaloRunCheck",
        table_name=my_table_name,
    )

    anomalo_sensor = AnomaloJobCompleteSensor(
        task_id="AnomaloJobCompleteSensor",
        xcom_job_id_task=anomalo_run.task_id,
        poke_interval=60,
        timeout=900,  # 15 minutes
        mode="poke",
    )

    anomalo_validate = AnomaloPassFailOperator(
        task_id="AnomaloPassFail",
        table_name=my_table_name,
        xcom_job_id_task=anomalo_run.task_id,
        must_pass=[
            "data_freshness",
            "data_volume",
            "metric",
            "rule",
            "missing_data",
            "anomaly",
        ],
    )

    publish_data = EmptyOperator(task_id="publish_data")

    (
        ingest_transform_data
        >> anomalo_run
        >> anomalo_sensor
        >> anomalo_validate
        >> publish_data
    )
