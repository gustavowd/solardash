import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

st.set_page_config(
    page_title="Sistema de monitoramento energético do Campus Pato Branco da UTFPR",
    layout="wide"
)

st.header('Total de geração por inversor')

c = st.container()
with c:
    col1, col2 = st.columns([0.65,0.35])


conn = st.connection("my_database")
df = conn.query("select * from devices where device_type=1 order by device_name")
devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
devices = devices.set_index('device_id')

with col1:
    multi = st.multiselect(
        'Selecione um ou mais dispositivos:',
        df['device_name'],
        default=["Huawei - 21010738716TK4900687", "Huawei - 21010738716TK4900689", "Huawei - 21010738716TK4900706", "Huawei - 21010738716TK6901199", "Huawei - 21010738716TK6901301", "Huawei - 21010738716TK6901324", "Huawei - 21010738716TK6901325"])

days = datetime.timedelta(days=1)
today = datetime.datetime.now()
yesterday = today - days
with col2:
    d = st.date_input(
        "Selecione um período",
        (yesterday, today),
        format="DD.MM.YYYY",
    )

if len(d) == 2:
    chart_data = pd.DataFrame()
    for m in multi:
        device_id = devices[devices['device_name']==m].index.values.item(0)
        device_type = devices.at[device_id, 'device_type']

        df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + "and measurement_type_id=7 and measurement_time between '" + str(d[0]) + " 00:00:01' and '" + str(d[1]) + " 23:59:59' group by day order by day")
        #df = conn.query("select measurement_value, measurement_time from measurements where measurement_time between '" + str(d[0]) + " 00:00:01' and '" + str(d[1]) + " 23:59:59' and device_id=" + str(device_id) + " and measurement_type_id=" + str(measure_id) + " order by measurement_time")
        if chart_data.empty:
            chart_data = pd.DataFrame(df, columns=['day', 'max'])
            chart_data = chart_data.set_index('day')
            chart_data = chart_data.rename(columns={"max": m})
        else:
            chart_data2 = pd.DataFrame(df, columns=['day', 'max'])
            chart_data2 = chart_data2.set_index('day')
            chart_data2 = chart_data2.rename(columns={"max": m})

            chart_data = chart_data.merge(chart_data2, left_index=True, right_index=True, how='outer')

    #print(chart_data)
    #st.plotly_chart(chart_data, height=550)
    fig = px.bar(chart_data, barmode='group')

    # Plot!
    st.plotly_chart(fig, use_container_width=True)


#st.sidebar.success("Selecione um tipo de dispositivo")

# st.markdown(
#     """
#     ### Totalizadores
#     Nessa página futuramente estará disponível os valores totais de geração fotovoltaica e de consumo por bloco em kwh.
#     Por enquanto, selecione um tipo de dispositivo para realizar as consultas.
# """
# )
