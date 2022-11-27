# Apache Airflow Provider for Anomalo
A set of native Airflow operators for [Anomalo](https://www.anomalo.com/)

### Compatibility
These operators were created and tested with
* Python 3.10
* Airflow 2.3+
* Anomalo python client 0.0.7

### Installation

Simply install `apache-airflow-providers-anomalo` into your airflow instance. You can validate that it is correctly installed by running `airflow providers list` on the command line and seeing if `apache-airflow-providers-anomalo` is a listed providers package.

### Airflow Setup

From the airflow UI, go to Admin > Connections and hit the `+` button at the top to add a new connection.

From the "Connection Type" drop down, select "Anomalo".
![connection](https://github.com/anomalo-hq/anomalo-airflow-provider/blob/main/docs/connection.png?raw=True)
Then fill in the fields for "Connection Id" (`anomalo-default` is the default connection id), "Host", and "API Secret Token".

## Usage

1. Obtain Anomalo table name from GUI. For example
   ![table](https://github.com/anomalo-hq/anomalo-airflow-provider/blob/main/docs/table.png?raw=True)
   would be `public-bq.covid19_nyt.us_counties`

2. This package includes 3 different operators. You can find documentation for them on the operator code itself.
   1. Run checks Operator: `airflow.providers.anomalo.operators.anomalo.AnomaloRunCheckOperator`
   2. Job Sensor `airflow.providers.anomalo.sensors.anomalo.AnomaloJobCompleteSensor`
   3. Validate table checks: `airflow.providers.anomalo.operators.anomalo.AnomaloPassFailOperator`

3. See `anomalo_dag_example.py` for usage example
