"""Consultas e gráficos da visão geral do campus."""
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from monitor_groups import GROUPS
from ui import render_chart


def device_params(ids):
    params = {f'd{i}': int(value) for i, value in enumerate(ids)}
    return ','.join(f':{key}' for key in params), params


def power(conn, ids, variable, start, end, divisor):
    slots, params = device_params(ids)
    params.update(variable=int(variable), start=start, end=end + timedelta(days=1))
    frame = conn.query(
        "SELECT date_trunc('minute', measurement_time) AS time, device_id, "
        "avg(measurement_value) AS value FROM measurements "
        f"WHERE device_id IN ({slots}) AND measurement_type_id=:variable "
        "AND measurement_time >= :start AND measurement_time < :end "
        "GROUP BY 1, device_id ORDER BY 1", params=params, ttl=60, show_spinner=False)
    if frame.empty:
        return pd.Series(dtype=float)
    return frame.groupby('time').value.sum(min_count=1) / divisor


def energy(conn, ids, kind, start, end):
    table, variable = {1: ('picosdiariosinversores', 7), 2: ('picosdiariosmedidores', 27)}[kind]
    slots, params = device_params(ids)
    params.update(start=start, end=end, today=date.today(), tomorrow=date.today()+timedelta(days=1), variable=variable)
    # A leitura do dia complementa somente equipamentos sem agregado para hoje.
    frame = conn.query(
        f"WITH daily AS (SELECT make_date(year::int,month::int,day::int) AS time, device_id, pico AS value "
        f"FROM {table} WHERE device_id IN ({slots}) "
        "AND make_date(year::int,month::int,day::int) BETWEEN :start AND :end), "
        "current_day AS (SELECT CAST(:today AS date) AS time, m.device_id, max(measurement_value) AS value "
        f"FROM measurements m WHERE m.device_id IN ({slots}) AND measurement_type_id=:variable "
        "AND measurement_time >= :today AND measurement_time < :tomorrow "
        "AND CAST(:today AS date) BETWEEN :start AND :end "
        "AND NOT EXISTS (SELECT 1 FROM daily d WHERE d.device_id=m.device_id AND d.time=CAST(:today AS date)) "
        "GROUP BY m.device_id) SELECT time, sum(value)/1000.0 AS value "
        "FROM (SELECT * FROM daily UNION ALL SELECT * FROM current_day) combined GROUP BY time ORDER BY time",
        params=params, ttl=60, show_spinner=False)
    return frame.set_index('time').value if not frame.empty else pd.Series(dtype=float)


def counter_daily(frame):
    if frame.empty:
        return pd.Series(dtype=float)
    frame = frame.copy()
    frame['time'] = pd.to_datetime(frame.time)
    frame = frame.sort_values('time')
    def delta(values):
        values = values.dropna()
        if len(values) < 2 or (values.diff().dropna() < 0).any():
            return float('nan')
        return values.iloc[-1] - values.iloc[0]
    per_device = frame.groupby([frame.time.dt.normalize(), 'device_id']).value.agg(delta)
    return per_device.groupby(level=0).agg(lambda values: values.sum(min_count=len(values)))


def general_energy(conn, ids, variable, start, end, divisor):
    slots, params = device_params(ids)
    params.update(variable=int(variable), start=start, end=end+timedelta(days=1))
    frame = conn.query(
        f"SELECT measurement_time AS time, device_id, measurement_value AS value FROM measurements WHERE device_id IN ({slots}) "
        "AND measurement_type_id=:variable AND measurement_time >= :start AND measurement_time < :end ORDER BY measurement_time",
        params=params, ttl=60, show_spinner=False)
    return counter_daily(frame) / divisor


def equipment(devices, kind):
    available = devices[devices.device_type == kind]
    labels = dict(zip(available.device_id, available.device_name))
    group = 'Total'
    with st.popover('Selecionar equipamentos', use_container_width=True):
        if kind in GROUPS:
            group = st.selectbox('Unidade consumidora' if kind == 1 else 'Transformador',
                                 ['Total', *GROUPS[kind]], key=f'group_{kind}')
        defaults = list(labels) if group == 'Total' else [key for key, name in labels.items() if name in GROUPS[kind][group]]
        ids = st.multiselect('Equipamentos', list(labels), default=defaults,
                            format_func=lambda key: labels[key], key=f'devices_{kind}_{group}')
    st.caption(f'{group} · {len(ids)} equipamento(s)')
    return ids


def monitor(conn, devices, start, end):
    chart, controls = st.columns([4, 1.3])
    selections = []
    daily = start == end
    grouping = 'Dia'
    with controls, st.container(height=430, border=True):
        st.markdown('**Exibir no gráfico**')
        for kind, label in [(1, 'Geração'), (2, 'Consumo'), (3, 'Consumo geral')]:
            if not st.checkbox(label, value=kind == 1, key=f'enabled_{kind}'):
                continue
            ids = equipment(devices, kind)
            if not ids:
                st.caption('Selecione ao menos um equipamento.')
                continue
            # Potência de inversores e medidores: W → kW no mesmo eixo.
            variable, divisor = (0, 1000) if kind == 1 else (27, 1000)
            if kind == 3:
                with st.popover('Configurar medição', use_container_width=True):
                    catalog = conn.query('SELECT measurement_type_id, measurement_name FROM measurement_type ORDER BY measurement_type_id', ttl=600, show_spinner=False)
                    labels = dict(zip(catalog.measurement_type_id, catalog.measurement_name))
                    variable = st.selectbox('Potência' if daily else 'Contador acumulado de energia', list(labels), index=None,
                                            format_func=lambda key: labels[key], key=f'general_variable_{daily}')
                    unit = st.selectbox('Unidade de origem', ['W', 'kW'] if daily else ['Wh', 'kWh'], index=None, key=f'general_unit_{daily}')
                    st.caption('Para energia, usamos a última menos a primeira leitura de cada dia. Reinícios do contador e dias com menos de duas leituras ficam sem valor.')
                if variable is None or unit is None:
                    st.caption('Configure a variável e a unidade do medidor geral.')
                    continue
                divisor = 1000 if unit in ['W', 'Wh'] else 1
            selections.append((kind, label, ids, variable, divisor))
        if not daily:
            grouping = st.selectbox('Agrupar barras por', ['Dia', 'Mês', 'Ano'], index=1 if (end-start).days > 62 else 0)
    with chart:
        series = {}
        with st.spinner('Carregando medições…'):
            for kind, label, ids, variable, divisor in selections:
                if daily:
                    series[label] = power(conn, ids, variable, start, end, divisor)
                elif kind in [1, 2]:
                    series[label] = energy(conn, ids, kind, start, end)
                else:
                    series[label] = general_energy(conn, ids, variable, start, end, divisor)
        frame = pd.DataFrame(series).sort_index()
        if frame.empty or frame.dropna(how='all').empty:
            st.info('Selecione séries e equipamentos com dados disponíveis no período.')
            return
        frame.index = pd.to_datetime(frame.index)
        if not daily and grouping != 'Dia':
            frame = frame.resample('MS' if grouping == 'Mês' else 'YS').sum(min_count=1)
        frame.index.name = 'Horário' if daily else 'Período'
        fig = px.line(frame) if daily else px.bar(frame, barmode='group')
        fig.update_layout(height=380, yaxis_title='Potência (kW)' if daily else 'Energia (kWh)')
        render_chart(fig, use_container_width=True)
        st.download_button('↓ Download CSV', frame.to_csv(sep=';', decimal=',').encode('utf-8'), 'monitoramento.csv', 'text/csv')
        if not daily:
            st.caption('Totais dos registros disponíveis; lacunas não significam zero. O dia atual usa as medições quando ainda não existe agregado, seguindo a convenção anterior.')
