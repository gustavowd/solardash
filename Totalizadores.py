"""Visão geral: geração e consumo no mesmo período."""
import streamlit as st
from pandas.errors import DatabaseError
from sqlalchemy.exc import SQLAlchemyError
from streamlit.errors import StreamlitSecretNotFoundError
from ui import setup_page
from monitoring import monitor
from analysis import analyze
from periods import period_selector

setup_page('Visão geral', 'Geração e consumo do campus', compact=True)
nav, period = st.columns([3, 2])
with nav:
    mode = st.segmented_control('Visualização', ['Monitorar', 'Analisar'], default='Monitorar', label_visibility='collapsed')

with period:
    start, end = period_selector()
st.caption(f'{start:%d/%m/%Y} — {end:%d/%m/%Y} · ' +
           ('Variáveis por equipamento' if mode == 'Analisar' else
            'Potência ao longo do dia' if start == end else 'Energia no período'))
try:
    conn = st.connection('my_database', connect_args={'connect_timeout': 5, 'options': '-c statement_timeout=15000'}, pool_timeout=5)
    with st.spinner('Carregando equipamentos…'):
        devices = conn.query('SELECT device_id, device_name, device_type FROM devices ORDER BY device_name', ttl=600, show_spinner=False)
    if mode == 'Analisar':
        analyze(conn, devices, start, end)
    else:
        monitor(conn, devices, start, end)
except (SQLAlchemyError, DatabaseError, StreamlitSecretNotFoundError):
    st.error('Não foi possível concluir a consulta. Tente um período menor ou verifique a conexão com o banco do campus.')
    if st.button('Tentar novamente'):
        st.rerun()
