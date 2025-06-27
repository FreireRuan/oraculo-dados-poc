import time
import pandas as pd
from pyathena import connect
import streamlit as st
from connection_athena import get_boto3_session

aws_conf = st.secrets["aws"]


def executar_athena_df(query: str, database: str) -> pd.DataFrame:
    """
    Executa a query no Athena e retorna com o resultado.
    """
    # Dispara execução da query
    session = get_boto3_session()
    client = session.client('athena')
    resp = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': aws_conf['athena_s3_output']}
    )
    query_exec_id = resp["QueryExecutionId"]

    # Polling até a query concluir
    while True:
        status = client.get_query_execution(QueryExecutionId=query_exec_id)
        state = status['QueryExecution']['Status']['State']
        if state in ('SUCCEEDED', 'FAILED', 'CANCELLED'):
            break
        time.sleep(1)

    # Lê resultado via PyAthena
    df = pd.read_sql(
        query,
        connect(
            s3_staging_dir=aws_conf['athena_s3_output'],
            region_name=aws_conf.get('region', 'us-east-1')
        )
    )
    return df