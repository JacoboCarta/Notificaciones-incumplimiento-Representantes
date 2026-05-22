import oracledb
import streamlit as st

oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_26")

@st.cache_resource
def get_connection():
    conn = oracledb.connect(
        user="",
        password="",
        dsn="",
        config_dir=r"",
        wallet_location=r"",
        wallet_password=""
    )
    return conn
