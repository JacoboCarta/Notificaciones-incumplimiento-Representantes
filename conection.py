import oracledb
import streamlit as st
import os

oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_26")

@st.cache_resource
def get_connection():
    conn = oracledb.connect(
        user=os.getenv("ORACLE_USER", "G08_E01"),
        password=os.getenv("ORACLE_PASSWORD", ""),
        dsn=os.getenv("ORACLE_DSN", "adbg08_tp"),
        config_dir=os.getenv("ORACLE_WALLET", ""),
        wallet_location=os.getenv("ORACLE_WALLET", ""),
        wallet_password=""
    )
    return conn
