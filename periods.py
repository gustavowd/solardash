"""Seleção de período com rascunho e aplicação explícita."""
import calendar
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from sqlalchemy.exc import SQLAlchemyError
from streamlit.errors import StreamlitSecretNotFoundError

PRESETS = ['Hoje', 'Ontem', 'Dia', 'Últimos 7 Dias', 'Últimos 30 Dias', 'Período de Dias',
           'Mês Atual', 'Mês Anterior', 'Mês', 'Ano Atual', 'Ano Anterior', 'Período de Meses',
           'Anos', 'Desde a Instalação']
MONTHS = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']


def month_end(day):
    return day.replace(day=calendar.monthrange(day.year, day.month)[1])


def preset_dates(preset, today=None):
    today = today or date.today()
    if preset == 'Hoje': return today, today
    if preset == 'Ontem': return today-timedelta(days=1), today-timedelta(days=1)
    if preset == 'Últimos 7 Dias': return today-timedelta(days=6), today
    if preset == 'Últimos 30 Dias': return today-timedelta(days=29), today
    if preset == 'Mês Atual': return today.replace(day=1), today
    if preset == 'Mês Anterior':
        last = today.replace(day=1)-timedelta(days=1)
        return last.replace(day=1), last
    if preset == 'Ano Atual': return date(today.year, 1, 1), today
    if preset == 'Ano Anterior': return date(today.year-1, 1, 1), date(today.year-1, 12, 31)
    return None


def choose_preset(value):
    st.session_state.period_draft_preset = value


def month_input(label, initial, key):
    st.caption(label)
    month, year = st.columns([2, 1])
    m = month.selectbox('Mês', range(1, 13), index=initial.month-1,
                        format_func=lambda n: MONTHS[n-1], key=f'{key}_month')
    y = year.number_input('Ano', min_value=1900, max_value=2200, value=initial.year, key=f'{key}_year')
    return date(int(y), m, 1)


def close_period():
    st.session_state.period_open = False


def open_period():
    start, _ = st.session_state.monitor_period
    st.session_state.period_draft_preset = st.session_state.get('period_applied_preset', 'Hoje')
    # Cada abertura começa com os valores aplicados, descartando edições canceladas.
    for key in ['period_day', 'period_days', 'period_single_month', 'period_single_year',
                'period_start_month', 'period_start_year', 'period_end_month', 'period_end_year',
                'period_year_start', 'period_year_end']:
        st.session_state.pop(key, None)
    st.session_state.period_day = start
    st.session_state.period_open = True


@st.dialog('Selecionar Período', width='large', on_dismiss=close_period)
def period_dialog():
    preset = st.session_state.period_draft_preset
    start, end = st.session_state.monitor_period
    with st.container(key='period_presets'):
        for offset in range(0, len(PRESETS), 3):
            columns = st.columns(3)
            for column, name in zip(columns, PRESETS[offset:offset+3]):
                column.button(name, key=f'preset_{name}', use_container_width=True,
                              type='primary' if name == preset else 'secondary',
                              on_click=choose_preset, args=(name,))
    chosen = preset_dates(preset)
    if preset == 'Dia':
        day = st.date_input('Dia', key='period_day', format='DD/MM/YYYY')
        chosen = day, day
    elif preset == 'Período de Dias':
        chosen = st.date_input('Data inicial e final', value=(start, end), key='period_days', format='DD/MM/YYYY')
    elif preset == 'Mês':
        first = month_input('Selecione o mês', start, 'period_single')
        chosen = first, month_end(first)
    elif preset == 'Período de Meses':
        first = month_input('Mês inicial', start, 'period_start')
        last = month_input('Mês final', end, 'period_end')
        chosen = first, month_end(last)
    elif preset == 'Anos':
        left, right = st.columns(2)
        y1 = left.number_input('Ano inicial', min_value=1900, max_value=2200, value=start.year, key='period_year_start')
        y2 = right.number_input('Ano final', min_value=1900, max_value=2200, value=end.year, key='period_year_end')
        chosen = date(int(y1), 1, 1), date(int(y2), 12, 31)
    elif preset == 'Desde a Instalação':
        st.caption('Da primeira medição disponível no banco até hoje.')
    if chosen and len(chosen) == 2:
        st.caption(f'{chosen[0]:%d/%m/%Y} — {chosen[1]:%d/%m/%Y}')
    st.divider()
    cancel, apply = st.columns(2)
    if cancel.button('Cancelar', use_container_width=True):
        close_period()
        st.rerun()
    if apply.button('Aplicar', type='primary', use_container_width=True):
        if preset == 'Desde a Instalação':
            try:
                conn = st.connection('my_database', connect_args={'connect_timeout': 5, 'options': '-c statement_timeout=15000'}, pool_timeout=5)
                result = conn.query('SELECT min(measurement_time) AS first FROM measurements', ttl=3600, show_spinner='Consultando primeira medição…')
                if result.empty or pd.isna(result.iloc[0]['first']):
                    st.warning('Não há medições para determinar o início do período.')
                    return
                chosen = pd.Timestamp(result.iloc[0]['first']).date(), date.today()
            except (SQLAlchemyError, pd.errors.DatabaseError, StreamlitSecretNotFoundError):
                st.error('Não foi possível consultar a primeira medição. Tente novamente.')
                return
        if not chosen or len(chosen) != 2 or chosen[0] > chosen[1]:
            st.warning('Selecione um intervalo completo com início anterior ou igual ao fim.')
            return
        st.session_state.monitor_period = tuple(chosen)
        st.session_state.period_applied_preset = preset
        close_period()
        st.rerun()


def period_selector():
    if 'monitor_period' not in st.session_state:
        st.session_state.monitor_period = (date.today(), date.today())
    start, end = st.session_state.monitor_period
    st.button(f'📅 {start:%d/%m/%Y} — {end:%d/%m/%Y}', key='open_period',
              use_container_width=True, on_click=open_period)
    if st.session_state.get('period_open', False):
        period_dialog()
    return start, end
