import streamlit as st
import pandas as pd
import datetime


def print_full(x):
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 2000)
    pd.set_option('display.float_format', '{:20,.2f}'.format)
    pd.set_option('display.max_colwidth', None)
    print(x)
    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.float_format')
    pd.reset_option('display.max_colwidth')

st.set_page_config(layout="wide")
st.header('Dashboard de gestão energética da UTFPR / Campus Pato Branco')

c = st.container()
with c:
    col1, col2, col3 = st.columns([0.65,0.2,0.15])


conn = st.connection("my_database")
df = conn.query("select * from devices where device_type=4 order by device_name")
devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
devices = devices.set_index('device_id')

df_m = conn.query("select measurement_name, measurement_type_id from measurements natural join measurement_type where device_id=32 and measurement_time between '2024-05-09 08:00:01' and '2024-05-09 08:00:15' order by measurement_type_id")
measurements = pd.DataFrame(df_m, columns=['measurement_name', 'measurement_type_id'])
measurements = measurements.set_index('measurement_type_id')

with col1:
    multi = st.multiselect(
        'Selecione um ou mais dispositivos:',
        df['device_name'])

with col2:
    measure = st.selectbox(
        'Selecione uma variável',
        df_m['measurement_name'])

today = datetime.datetime.now()
with col3:
    d = st.date_input(
        "Selecione um período",
        (today, today),
        format="DD.MM.YYYY",
    )

if len(d) == 2:
    chart_data = pd.DataFrame()
    for m in multi:
        device_id = devices[devices['device_name']==m].index.values.item(0)
        device_type = devices.at[device_id, 'device_type']

        measure_id = measurements[measurements['measurement_name']==measure].index.values.item(0)

        df = conn.query("select measurement_value, measurement_time from measurements where measurement_time between '" + str(d[0]) + " 00:00:01' and '" + str(d[1]) + " 23:59:59' and device_id=" + str(device_id) + " and measurement_type_id=" + str(measure_id) + " order by measurement_time", ttl=0)
        if chart_data.empty:
            chart_data = pd.DataFrame(df, columns=['measurement_time', 'measurement_value'])
            #chart_data['measurement_time'] = pd.to_datetime(chart_data['measurement_time']) # para converter para datetime
            #chart_data['measurement_time'] -= pd.to_timedelta(3, unit='h') # pra reduzir 1 hora
            chart_data = chart_data.set_index('measurement_time')
            chart_data = chart_data.rename(columns={"measurement_value": m})
        else:
            chart_data2 = pd.DataFrame(df, columns=['measurement_time', 'measurement_value'])
            #chart_data2['measurement_time'] = pd.to_datetime(chart_data2['measurement_time']) # para converter para datetime
            #chart_data2['measurement_time'] -= pd.to_timedelta(3, unit='h') # pra reduzir 1 hora
            chart_data2 = chart_data2.set_index('measurement_time')
            chart_data2 = chart_data2.rename(columns={"measurement_value": m})

            chart_data = chart_data.merge(chart_data2, left_index=True, right_index=True, how='outer')

    st.line_chart(chart_data, height=550)
    conn.reset()
