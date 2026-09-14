"""Análise de variáveis individuais, preservando os valores do banco."""
from datetime import timedelta
import re
import pandas as pd
import plotly.express as px
import streamlit as st
from monitoring import device_params
from ui import render_chart

CATEGORIES = {1: 'Inversores', 2: 'Medidores', 3: 'Medidor geral', 4: 'Estação solarimétrica', 5: 'Cargas'}


def variable_unit(name):
    match = re.search(r'\(([^()]+)\)\s*$', name)
    return match.group(1).strip() if match else 'Valor de origem'


def variable_catalog(conn, kind, start, end):
    return conn.query(
        'SELECT mt.measurement_type_id, mt.measurement_name FROM measurement_type mt '
        'WHERE EXISTS (SELECT 1 FROM measurements m '
        'JOIN devices d ON d.device_id = m.device_id '
        'WHERE d.device_type = :kind AND m.measurement_type_id = mt.measurement_type_id '
        'AND m.measurement_time >= :start AND m.measurement_time < :end) '
        'ORDER BY mt.measurement_type_id',
        params={'kind': int(kind), 'start': start, 'end': end + timedelta(days=1)},
        ttl=600, show_spinner=False)


def readings(conn, ids, variables, start, end):
    slots, params = device_params(ids)
    params.update({f'v{i}': int(value) for i, value in enumerate(variables)})
    variable_slots = ','.join(f':v{i}' for i in range(len(variables)))
    params.update(start=start, end=end+timedelta(days=1))
    return conn.query(
        'SELECT measurement_time AS time, device_id, measurement_type_id, measurement_value AS value '
        f'FROM measurements WHERE device_id IN ({slots}) AND measurement_type_id IN ({variable_slots}) '
        'AND measurement_time >= :start AND measurement_time < :end '
        'ORDER BY measurement_time, device_id, measurement_type_id', params=params, ttl=60, show_spinner=False)


def analyze(conn, devices, start, end):
    kind = st.selectbox('Tipo de equipamento', list(CATEGORIES),
                        format_func=CATEGORIES.get, key='analysis_kind')
    devices = devices.loc[devices.device_type == kind]
    context = (kind, start, end)
    if st.session_state.get('analysis_context') != context:
        for key in ['analysis_equipment', 'analysis_variables', 'analysis_applied', 'analysis_stats']:
            st.session_state.pop(key, None)
        st.session_state.analysis_context = context
    if devices.empty:
        st.info('Não há equipamentos cadastrados neste tipo.')
        return
    device_labels = {row.device_id: f'{CATEGORIES.get(row.device_type, "Equipamento")} · {row.device_name} · {row.device_id}'
                     for row in devices.itertuples()}
    with st.spinner('Carregando variáveis do tipo de equipamento…'):
        catalog = variable_catalog(conn, kind, start, end)
    if catalog.empty:
        st.info('Não há variáveis com leituras para este tipo de equipamento no período selecionado.')
        return
    variable_labels = {row.measurement_type_id: f'{row.measurement_name} · {row.measurement_type_id}' for row in catalog.itertuples()}
    variable_units = {variable_labels[row.measurement_type_id]: variable_unit(row.measurement_name)
                      for row in catalog.itertuples()}
    default_ids = list(devices.device_id)
    with st.form('analysis_selection'):
        equipment_col, params_col = st.columns(2)
        with equipment_col:
            draft_ids = st.multiselect('Equipamentos', list(device_labels), default=default_ids,
                                       format_func=lambda key: device_labels[key], key='analysis_equipment')
        with params_col:
            draft_variables = st.multiselect('Variáveis', list(variable_labels),
                                             format_func=lambda key: variable_labels[key], key='analysis_variables')
        if st.form_submit_button('Aplicar seleção', type='primary'):
            st.session_state.analysis_applied = (list(draft_ids), list(draft_variables))
    ids, variables = st.session_state.get('analysis_applied', ([], []))
    ids = [key for key in ids if key in device_labels]
    variables = [key for key in variables if key in variable_labels]
    if not ids:
        st.info('Selecione os equipamentos e variáveis e clique em Aplicar seleção.')
        return
    download_col = st.container()
    if not variables:
        st.info('Selecione potência, tensão, corrente ou outra variável disponível nos equipamentos.')
        return
    with st.spinner('Carregando variáveis…'):
        data = readings(conn, ids, variables, start, end)
    if data.empty:
        st.info('Não há leituras para os equipamentos, variáveis e período selecionados.')
        return
    data = data.copy()
    data['time'] = pd.to_datetime(data.time)
    data['Equipamento'] = data.device_id.map(device_labels)
    data['Parâmetro'] = data.measurement_type_id.map(variable_labels)
    data['Série'] = data['Equipamento'] + ' — ' + data['Parâmetro']
    with download_col:
        export = data.rename(columns={'time': 'Horário', 'value': 'Valor'})
        st.download_button('↓ Download CSV', export.to_csv(index=False, sep=';', decimal=',').encode('utf-8'),
                           'analise.csv', 'text/csv', use_container_width=True)
    chart, stats = st.columns([4, 1.2])
    with chart:
        # Painéis separados evitam comparar tensão e potência na mesma escala.
        facet = 'Parâmetro' if data['Parâmetro'].nunique() > 1 else None
        fig = px.line(data, x='time', y='value', color='Série', facet_row=facet,
                      labels={'time': 'Horário', 'value': 'Valor de origem'})
        fig.update_layout(height=max(380, 240*data['Parâmetro'].nunique()),
                          yaxis_title='Valor de origem')
        if facet:
            fig.update_yaxes(matches=None)
            fig.for_each_annotation(lambda item: item.update(text=item.text.replace('Parâmetro=', '')))
        series_units = dict(zip(data['Série'], data['Parâmetro'].map(variable_units)))
        for trace in fig.data:
            axis = 'yaxis' + trace.yaxis[1:]
            fig.layout[axis].title.text = series_units[trace.name]
        render_chart(fig, use_container_width=True)
    with stats, st.container(border=True):
        name = st.selectbox('Estatísticas da série', list(data['Série'].unique()), key='analysis_stats')
        values = data.loc[data['Série'] == name, 'value'].dropna()
        metrics = [('Máximo', values.max()), ('Mínimo', values.min()), ('Média', values.mean()),
                   ('Variação', values.max()-values.min()), ('Desvio padrão', values.std(ddof=0)), ('Mediana', values.median())]
        columns = st.columns(2)
        for index, (label, value) in enumerate(metrics):
            formatted = f'{value:,.2f}'.replace(',', '_').replace('.', ',').replace('_', '.') if pd.notna(value) else '—'
            columns[index % 2].metric(label, formatted)
        st.caption('Estatísticas das leituras disponíveis, na unidade de origem. Desvio padrão populacional.')
