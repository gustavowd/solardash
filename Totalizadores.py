"""Visão geral: geração e consumo no mesmo período."""
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError
from streamlit.errors import StreamlitSecretNotFoundError
from ui import setup_page, PAGES
from monitoring import monitor
from periods import period_selector

setup_page('Visão geral', 'Geração e consumo do campus', compact=True)
nav, period = st.columns([3, 2])
with nav:
    mode = st.segmented_control('Visualização', ['Monitorar', 'Analisar'], default='Monitorar', label_visibility='collapsed')

if mode == 'Analisar':
    st.markdown('**Analisar medições por equipamento**')
    st.caption('Selecione uma categoria para abrir sua tela de variáveis, histórico e exportação.')
    columns = st.columns(3)
    for index, (path, label, icon) in enumerate(PAGES[2:]):
        with columns[index % 3]:
            st.page_link(path, label=label, icon=icon, use_container_width=True)
else:
    with period:
        start, end = period_selector()
    st.caption(f'{start:%d/%m/%Y} — {end:%d/%m/%Y} · {"Potência ao longo do dia" if start == end else "Energia no período"}')
    try:
        conn = st.connection('my_database', connect_args={'connect_timeout': 5, 'options': '-c statement_timeout=15000'}, pool_timeout=5)
        with st.spinner('Carregando equipamentos…'):
            devices = conn.query('SELECT device_id, device_name, device_type FROM devices ORDER BY device_name', ttl=600, show_spinner=False)
        monitor(conn, devices, start, end)
    except (SQLAlchemyError, StreamlitSecretNotFoundError):
        st.error('Não foi possível carregar os dados. Verifique a conexão com o banco do campus.')
        if st.button('Tentar novamente'):
            st.rerun()
