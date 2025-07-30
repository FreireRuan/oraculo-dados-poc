import streamlit as st
import boto3

aws_conf = st.secrets["aws"]

@st.cache_resource
def get_boto3_session():
    """
    Retorna uma sessão boto3 configurada com as credenciais do Athena.
    """
    return boto3.Session(
        aws_access_key_id=aws_conf["aws_access_key_id"],
        aws_secret_access_key=aws_conf["aws_secret_access_key"],
        region_name=aws_conf.get("region", "us-east-1"),
    )