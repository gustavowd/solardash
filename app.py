import streamlit as st
import pandas as pd

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

st.title('Dashboard de gestão energética da UTFPR / Campus Pato Branco')

conn = st.connection("my_database")
df = conn.query("select * from devices order by device_id")
devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
devices = devices.set_index('device_id')
#print(devices)

multi = st.multiselect(
    'Selecione um ou mais dispositivos:',
     df['device_name'])
#'You selected: ', multi

# df1 = conn.query("select * from measurements where measurement_time between '2024-04-20' and '2024-04-24' and device_id=2" + " and measurement_type_id=1 order by measurement_time")
# chart_data = pd.DataFrame(df1, columns=['measurement_time', 'measurement_value'])
# chart_data['measurement_time'] = pd.to_datetime(chart_data['measurement_time']) # para converter para datetime
# chart_data['measurement_time'] -= pd.to_timedelta(3, unit='h') # pra reduzir 1 hora
# chart_data = chart_data.set_index('measurement_time')
# chart_data = chart_data.rename(columns={"measurement_value": "Inverter1"})

# df2 = conn.query("select * from measurements where measurement_time between '2024-04-20' and '2024-04-24' and device_id=35" + " and measurement_type_id=1 order by measurement_time")
# chart_data2 = pd.DataFrame(df2, columns=['measurement_time', 'measurement_value'])
# chart_data2['measurement_time'] = pd.to_datetime(chart_data2['measurement_time']) # para converter para datetime
# chart_data2['measurement_time'] -= pd.to_timedelta(3, unit='h') # pra reduzir 1 hora
# chart_data2 = chart_data2.set_index('measurement_time')
# chart_data2 = chart_data2.rename(columns={"measurement_value": "Inverter2"})
# chart_data = chart_data.merge(chart_data2, left_index=True, right_index=True, how='outer')

# df3 = conn.query("select * from measurements where measurement_time between '2024-04-20' and '2024-04-24' and device_id=36" + " and measurement_type_id=1 order by measurement_time")
# chart_data2 = pd.DataFrame(df3, columns=['measurement_time', 'measurement_value'])
# chart_data2['measurement_time'] = pd.to_datetime(chart_data2['measurement_time']) # para converter para datetime
# chart_data2['measurement_time'] -= pd.to_timedelta(3, unit='h') # pra reduzir 1 hora
# chart_data2 = chart_data2.set_index('measurement_time')
# chart_data2 = chart_data2.rename(columns={"measurement_value": "Inverter3"})
# chart_data = chart_data.merge(chart_data2, left_index=True, right_index=True, how='outer')

# df4 = conn.query("select * from measurements where measurement_time between '2024-04-20' and '2024-04-24' and device_id=37" + " and measurement_type_id=1 order by measurement_time")
# chart_data2 = pd.DataFrame(df4, columns=['measurement_time', 'measurement_value'])
# chart_data2['measurement_time'] = pd.to_datetime(chart_data2['measurement_time']) # para converter para datetime
# chart_data2['measurement_time'] -= pd.to_timedelta(3, unit='h') # pra reduzir 1 hora
# chart_data2 = chart_data2.set_index('measurement_time')
# chart_data2 = chart_data2.rename(columns={"measurement_value": "Inverter4"})
# chart_data = chart_data.merge(chart_data2, left_index=True, right_index=True, how='outer')

# pd.set_option('display.max_columns', None)
# print_full(chart_data)

chart_data = pd.DataFrame()
for m in multi:
    device_id = devices[devices['device_name']==m].index.values.item(0)
    device_type = devices.at[device_id, 'device_type']

    if device_type == 1:
        df = conn.query("select * from measurements where measurement_time between '2024-04-20 00:00:01' and '2024-04-24 23:59:59' and device_id=" + str(device_id) + " and measurement_type_id=0 order by measurement_time")
    elif device_type == 2:
        df = conn.query("select * from measurements where measurement_time between '2024-04-20 00:00:01' and '2024-04-24 23:59:59' and device_id=" + str(device_id) + " and measurement_type_id=27 order by measurement_time")
    elif device_type == 3:
        df = conn.query("select * from measurements where measurement_time between '2024-04-20 00:00:01' and '2024-04-24 23:59:59' and device_id=" + str(device_id) + " and measurement_type_id=42 order by measurement_time")
    elif device_type == 4:
        df = conn.query("select * from measurements where measurement_time between '2024-04-20 00:00:01' and '2024-04-24 23:59:59' and device_id=" + str(device_id) + " and measurement_type_id=22 order by measurement_time")
    if chart_data.empty:
        chart_data = pd.DataFrame(df, columns=['measurement_time', 'measurement_value'])
        chart_data['measurement_time'] = pd.to_datetime(chart_data['measurement_time']) # para converter para datetime
        chart_data['measurement_time'] -= pd.to_timedelta(3, unit='h') # pra reduzir 1 hora
        chart_data = chart_data.set_index('measurement_time')
        chart_data = chart_data.rename(columns={"measurement_value": m})
    else:
        chart_data2 = pd.DataFrame(df, columns=['measurement_time', 'measurement_value'])
        chart_data2['measurement_time'] = pd.to_datetime(chart_data2['measurement_time']) # para converter para datetime
        chart_data2['measurement_time'] -= pd.to_timedelta(3, unit='h') # pra reduzir 1 hora
        chart_data2 = chart_data2.set_index('measurement_time')
        chart_data2 = chart_data2.rename(columns={"measurement_value": m})

        chart_data = chart_data.merge(chart_data2, left_index=True, right_index=True, how='outer')

st.line_chart(chart_data)