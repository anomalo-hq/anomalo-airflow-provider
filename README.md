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
![](https://raw.githubusercontent.com/anomalo-hq/anomalo-airflow-provider/main/docs/connection.png)
Then fill in the fields for "Connection Id" (`anomalo-default` is the default connection id), "Host", and "API Secret Token".

## Usage

1. Obtain Anomalo table name from GUI. For example
   ![](https://raw.githubusercontent.com/anomalo-hq/anomalo-airflow-provider/main/docs/table.png)
   would be `public-bq.covid19_nyt.us_counties`

2. This package includes 3 different operators. You can find documentation for them on the operator code itself.
   1. Run checks Operator: `airflow.providers.anomalo.operators.anomalo.AnomaloRunCheckOperator`
   2. Job Sensor `airflow.providers.anomalo.sensors.anomalo.AnomaloJobCompleteSensor`
   3. Validate table checks: `airflow.providers.anomalo.operators.anomalo.AnomaloPassFailOperator`

3. See `anomalo_dag_example.py` for usage example
