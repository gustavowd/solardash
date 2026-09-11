"""Análise de variáveis individuais, preservando os valores do banco."""
from datetime import timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from monitoring import device_params
from ui import render_chart

CATEGORIES = {1: 'Inversores', 2: 'Medidores', 3: 'Medidor geral', 4: 'Estação solarimétrica', 5: 'Cargas'}


def variable_catalog(conn):
    # O cadastro é pequeno; não percorre o histórico para montar um seletor.
    return conn.query(
        'SELECT measurement_type_id, measurement_name FROM measurement_type ORDER BY measurement_type_id',
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
    equipment_col, params_col, download_col = st.columns([2, 2, 1])
    device_labels = {row.device_id: f'{CATEGORIES.get(row.device_type, "Equipamento")} · {row.device_name} · {row.device_id}'
                     for row in devices.itertuples()}
    with equipment_col:
        selected = st.session_state.get('analysis_equipment', list(devices.loc[devices.device_type == 1, 'device_id']))
        with st.popover(f'Equipamentos · {len(selected)} selecionado(s)', use_container_width=True):
            ids = st.multiselect('Equipamentos', list(device_labels), default=selected,
                                format_func=lambda key: device_labels[key], key='analysis_equipment')
    if not ids:
        st.info('Selecione pelo menos um equipamento para consultar suas variáveis.')
        return
    catalog = variable_catalog(conn)
    variable_labels = {row.measurement_type_id: f'{row.measurement_name} · {row.measurement_type_id}' for row in catalog.itertuples()}
    with params_col:
        # Descarta parâmetros removidos do cadastro.
        previous = st.session_state.get('analysis_variables', [])
        valid = [value for value in previous if value in variable_labels]
        if previous != valid:
            st.session_state.analysis_variables = valid
        with st.popover(f'Parâmetros · {len(valid)} selecionado(s)', use_container_width=True):
            variables = st.multiselect('Variáveis', list(variable_labels),
                                       format_func=lambda key: variable_labels[key], key='analysis_variables')
            st.caption('Todos os parâmetros cadastrados. Alguns podem não ter leituras nos equipamentos selecionados. Cada parâmetro tem seu próprio eixo vertical.')
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
