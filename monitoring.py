"""Consultas e gráficos da visão geral do campus."""
from datetime import date, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st
from monitor_groups import GROUPS
from ui import render_chart


def campus_index(values):
    # Datas sem fuso dos agregados já representam o calendário local.
    def local(value):
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is not None:
            timestamp = timestamp.tz_convert('America/Sao_Paulo').tz_localize(None)
        return timestamp
    return pd.DatetimeIndex([local(value) for value in values])


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
    totals = []
    cursor = start
    while cursor <= end:
        last = min(cursor + timedelta(days=6), end)
        # Um dia de sobreposição preserva o intervalo que termina à meia-noite.
        values = power(conn, ids, variable, cursor, min(last + timedelta(days=1), end), divisor)
        daily = power_energy_daily(values)
        if not daily.empty:
            totals.append(daily.loc[(daily.index.date >= cursor) & (daily.index.date <= last)])
        cursor = last + timedelta(days=1)
    return pd.concat(totals).sort_index() if totals else pd.Series(dtype=float)


def power_energy_daily(values):
    values = values.sort_index().copy()
    if values.empty:
        return values
    values.index = campus_index(values.index)
    hours = values.index.to_series().diff().dt.total_seconds() / 3600
    # Integra apenas minutos consecutivos, sem estimar energia nas lacunas.
    valid = hours.eq(1 / 60)
    amounts = ((values + values.shift()) / 2 * hours).where(valid)
    days = (values.index - pd.Timedelta(seconds=1)).normalize()
    return amounts.groupby(days).sum(min_count=1)


def equipment(devices, kind):
    available = devices[devices.device_type == kind]
    labels = dict(zip(available.device_id, available.device_name))
    initial_ids = list(labels)
    if kind == 3:
        initial_ids = [key for key, name in labels.items()
                       if 'geral' in name.casefold() and 'utfpr' in name.casefold()][:1]
    group = 'Total'
    with st.popover('Selecionar equipamentos', use_container_width=True):
        if kind in GROUPS:
            group = st.selectbox('Unidade consumidora' if kind == 1 else 'Transformador',
                                 ['Total', *GROUPS[kind]], key=f'group_{kind}')
        defaults = initial_ids if group == 'Total' else [key for key, name in labels.items() if name in GROUPS[kind][group]]
        with st.form(f'equipment_form_{kind}_{group}'):
            draft = st.multiselect('Equipamentos', list(labels), default=defaults,
                                   format_func=lambda key: labels[key], key=f'devices_{kind}_{group}')
            if st.form_submit_button('Aplicar seleção', type='primary'):
                st.session_state[f'equipment_applied_{kind}'] = (group, list(draft))
    applied_group, ids = st.session_state.get(f'equipment_applied_{kind}', ('Total', initial_ids))
    ids = [key for key in ids if key in labels]
    st.caption(f'{applied_group} · {len(ids)} equipamento(s)')
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
            ids = [34] if kind == 3 else equipment(devices, kind)
            if not ids:
                st.caption('Selecione ao menos um equipamento.')
                continue
            # Potência de inversores e medidores: W → kW no mesmo eixo.
            variable, divisor = (0, 1000) if kind == 1 else (27, 1000)
            if kind == 3:
                variable, divisor = 42, 1000
            selections.append((kind, label, ids, variable, divisor))
        if not daily:
            preset = st.session_state.get('period_applied_preset')
            context = (start, end, preset)
            if st.session_state.get('monitor_grouping_context') != context:
                st.session_state.monitor_grouping = 'Ano' if preset == 'Anos' else ('Mês' if (end-start).days > 62 else 'Dia')
                st.session_state.monitor_grouping_context = context
            grouping = st.selectbox('Agrupar barras por', ['Dia', 'Mês', 'Ano'], key='monitor_grouping')
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
        for label, values in series.items():
            values = values.copy()
            values.index = campus_index(values.index)
            series[label] = values
        frame = pd.DataFrame(series).sort_index()
        if frame.empty or frame.dropna(how='all').empty:
            st.info('Selecione séries e equipamentos com dados disponíveis no período.')
            return
        frame.index = pd.to_datetime(frame.index)
        if not daily and grouping != 'Dia':
            frame = frame.resample('MS' if grouping == 'Mês' else 'YS').sum(min_count=1)
            if grouping == 'Ano':
                frame.index = frame.index.strftime('%Y')
        frame.index.name = 'Horário' if daily else 'Período'
        fig = px.line(frame) if daily else px.bar(frame, barmode='group')
        fig.update_layout(height=380, yaxis_title='Potência (kW)' if daily else 'Energia (kWh)')
        if daily:
            for trace in fig.data:
                if trace.name == 'Geração':
                    trace.update(
                        line=dict(color='#f97316'), # Força a cor laranja da Geração
                        fill='tozeroy',
                        fillcolor='rgba(249, 115, 22, 0.12)'
                    )
                elif trace.name == 'Consumo':
                    trace.update(line=dict(color='#3b82f6')) # Azul para Consumo (opcional)
                elif trace.name == 'Consumo geral':
                    trace.update(line=dict(color='#10b981')) # Verde para Consumo geral (opcional)
        if not daily and grouping == 'Ano':
            fig.update_xaxes(type='category', title='Ano')
        render_chart(fig, use_container_width=True)
        st.download_button('↓ Download CSV', frame.to_csv(sep=';', decimal=',').encode('utf-8'), 'monitoramento.csv', 'text/csv')
        if not daily:
            st.caption('Totais dos registros disponíveis; lacunas não significam zero. O dia atual usa as medições quando ainda não existe agregado, seguindo a convenção anterior.')
            if any(kind == 3 for kind, *_ in selections):
                st.caption('Consumo geral: energia estimada pela potência real entre minutos consecutivos disponíveis; lacunas ficam fora do total.')
