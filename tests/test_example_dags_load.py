"""Load the example DAGs the way Airflow's DAG processor does.

An import or argument that the installed Airflow version has removed shows up
here as an import error, without running any task.
"""

try:
    from airflow.dag_processing.dagbag import DagBag
except ImportError:
    from airflow.models.dagbag import DagBag


def test_example_dags_load_without_errors(example_dags_folder):
    dag_bag = DagBag(dag_folder=str(example_dags_folder))

    assert dag_bag.import_errors == {}
    assert "AnomaloDAG" in dag_bag.dags
