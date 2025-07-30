import time
import pandas as pd
import boto3
import streamlit as st
from connection_athena import get_boto3_session

aws_conf = st.secrets["aws"]

def executar_athena_df(query: str, database: str) -> pd.DataFrame:
    """
    Executa uma query no Athena e retorna o resultado como DataFrame, lendo o arquivo CSV gerado no S3.
    """
    session = get_boto3_session()
    client = session.client('athena')

    # Executa a query
    resp = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': aws_conf['athena_s3_output']}
    )
    query_exec_id = resp["QueryExecutionId"]

    # Espera até finalizar
    while True:
        status = client.get_query_execution(QueryExecutionId=query_exec_id)
        state = status['QueryExecution']['Status']['State']
        if state == 'SUCCEEDED':
            break
        elif state in ('FAILED', 'CANCELLED'):
            reason = status['QueryExecution']['Status'].get('StateChangeReason', 'Motivo desconhecido')
            raise Exception(f"Query falhou ou foi cancelada: {reason}")
        time.sleep(1)

    # Pega o caminho do resultado no S3
    result_s3 = status['QueryExecution']['ResultConfiguration']['OutputLocation']

    s3 = session.client('s3')
    result_path = result_s3.replace("s3://", "")
    bucket, key = result_path.split("/", 1)

    import io
    obj = s3.get_object(Bucket=bucket, Key=key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))

    return df