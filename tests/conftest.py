import os
import tempfile
from importlib.metadata import version
from pathlib import Path

import pytest


EXAMPLE_DAGS = (
    Path(__file__).parent.parent / "src/airflow/providers/anomalo/example_dags"
)

# Airflow reads its settings when it is first imported, so point it at a
# throwaway home and database before any test module imports it.
os.environ.setdefault("AIRFLOW_HOME", tempfile.mkdtemp(prefix="airflow-home-"))
os.environ.setdefault("AIRFLOW__CORE__LOAD_EXAMPLES", "False")
os.environ.setdefault("AIRFLOW__CORE__UNIT_TEST_MODE", "True")
# Airflow 3's `dag.test()` finds the DAG it runs in the DAGs folder.
os.environ.setdefault("AIRFLOW__CORE__DAGS_FOLDER", str(EXAMPLE_DAGS))
if version("apache-airflow").startswith("2."):
    # Airflow 2 refuses SQLite with any executor but this one. Airflow 3
    # removed it and accepts SQLite with its default.
    os.environ.setdefault("AIRFLOW__CORE__EXECUTOR", "SequentialExecutor")


@pytest.fixture(scope="session")
def airflow_db():
    """Create Airflow's metadata database, which running a DAG needs."""
    from airflow.utils.db import resetdb

    resetdb()


@pytest.fixture
def example_dags_folder():
    return EXAMPLE_DAGS
