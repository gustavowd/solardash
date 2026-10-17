"""Visão geral: geração e consumo no mesmo período."""
import streamlit as st
from pandas.errors import DatabaseError
from sqlalchemy.exc import SQLAlchemyError
from streamlit.errors import StreamlitSecretNotFoundError
from ui import setup_page, render_sidebar
from monitoring import monitor
from analysis import analyze
from periods import period_selector

# 1. Configuração global da página (geralmente fica na primeira linha executável)
st.set_page_config(
    page_title="SolarDash",
    layout="wide",
    page_icon=":material/solar_power:"
)

# 2. Injeção do CSS para reduzir o espaço em branco superior
st.markdown(
    """
    <style>
        /* Cola o conteúdo principal bem no topo da página */
        .block-container {
            padding-top: 0.5rem !important;
            padding-bottom: 1rem !important;
            max-width: 100% !important;
        }

        /* Remove completamente a barra de cabeçalho padrão do Streamlit */
        header[data-testid="stHeader"] {
            display: none !important;
            height: 0px !important;
        }

        /* Remove margens extras do topo geradas por elementos vazios */
        div.block-container > div:first-child {
            margin-top: 0px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

def overview():
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


def about():
    setup_page('Sobre', 'Monitoramento energético da UTFPR — Campus Pato Branco', compact=True)
    st.subheader('SolarDash')
    st.write('Painel de acompanhamento da geração fotovoltaica e do consumo de energia do campus. '
             'Reúne medições dos equipamentos, séries históricas e exportação de dados em CSV.')
    st.subheader('Dados e medições')
    st.write('As leituras são obtidas do banco de dados da instalação. A coleta é realizada por sistemas externos; '
             'a disponibilidade dos resultados depende dos registros de cada equipamento.')
    st.write('Potência é apresentada em W ou kW, e energia em kWh, conforme a visualização. '
             'Na análise individual, as unidades seguem o cadastro das variáveis.')
    st.subheader('Instituição')
    st.write('Universidade Tecnológica Federal do Paraná — Campus Pato Branco.')


pages = {
    'Principal': [
        st.Page(overview, title='Dashboard', icon=':material/dashboard:', default=True),
        st.Page(about, title='Sobre', icon=':material/info:', url_path='sobre'),
    ],
    'Equipamentos': [
        st.Page('pages/Totalizadores dos medidores.py', title='Consumo consolidado', icon=':material/bar_chart:'),
        st.Page('pages/Inversores.py', title='Inversores', icon=':material/solar_power:'),
        st.Page('pages/Medidores.py', title='Medidores', icon=':material/speed:'),
        st.Page('pages/Medidores Gerais (Demanda).py', title='Demanda', icon=':material/monitoring:'),
        st.Page('pages/Cargas.py', title='Cargas', icon=':material/electrical_services:'),
        st.Page('pages/Estação Solarimétrica.py', title='Estação solarimétrica', icon=':material/thermostat:'),
    ],
}
selected_page = st.navigation(pages, position='hidden')
render_sidebar(pages)
selected_page.run()
