import oracledb
import streamlit as st

oracledb.init_oracle_client(lib_dir=r"C:\oracle\instantclient_23_26")

@st.cache_resource
def get_connection():
    conn = oracledb.connect(
        user="G08_E01",
        password="Bi!2026-08-01",
        dsn="adbg08_tp",
        config_dir=r"C:\oracle\wallet_g08",
        wallet_location=r"C:\oracle\wallet_g08",
        wallet_password=""
    )
    return conn