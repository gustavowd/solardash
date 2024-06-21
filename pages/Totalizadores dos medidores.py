import streamlit as st
import pandas as pd
import datetime
import plotly.express as px
import calendar

st.set_page_config(
    page_title="Sistema de monitoramento energético do Campus Pato Branco da UTFPR",
    layout="wide"
)

tab1, tab2, tab3 = st.tabs(["📈 Dia", "Mês", "Ano"])

with tab1:
    st.header('Total de consumo no dia')
    c = st.container()
    with c:
        col1, col2 = st.columns([0.2,0.8])


    conn = st.connection("my_database")
    with col1:
        option = st.selectbox(
            "Selecione o transformador",
            ("TRAFO 1", "TRAFO 2", "TRAFO 3", "TRAFO 4", "Total"),
            key="day_combo")

    df = conn.query("select * from devices where device_type=2 order by device_name")
    devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
    #print(devices)
    devices = devices.set_index('device_id')

    total_day = 0
    match option:
        case "TRAFO 1":
            with col2:
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day",
                    default=["Meter_TR1_BLOCO_B", "Meter_TR1_BLOCO_C", "Meter_TR1_BLOCO_D", "Meter_TR1_BLOCO_F", "Meter_TR1_BLOCO_H", "Meter_TR1_BLOCO_I", "Meter_TR1_BLOCO_J", "Meter_TR1_BLOCO_L", "Meter_TR1_BLOCO_M", "Meter_TR1_BLOCO_N"])
        case "TRAFO 2":
            with col2:
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day",
                    default=["Meter_TR2_BLOCO_J1", "Meter_TR2_BLOCO_M", "Meter_TR2_BLOCO_N"])
        case "TRAFO 3":
            with col2:
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day",
                    default=["Meter_TR3_BLOCO_V", "Meter_TR3_BLOCO_V_AC", "Meter_TR3_BLOCO_W"])
        case "TRAFO 4":
            with col2:                
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day",
                    default=["Meter_TR4_BLOCO_KY", "Meter_TR4_BLOCO_O", "Meter_TR4_BLOCO_P", "Meter_TR4_BLOCO_Q", "Meter_TR4_BLOCO_R", "Meter_TR4_BLOCO_RU", "Meter_TR4_BLOCO_S", "Meter_TR4_BLOCO_T", "Meter_TR4_BLOCO_U", "Meter_TR4_BLOCO_Z", "Meter_TR4_ILUM_EXTER"])
        case "Total":
            with col2:
                total_day = 1
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    [" "],
                    key="day",
                    default=[" "])
        case _ :
            with col2:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day")
                
    today = datetime.datetime.now()
    chart_data = pd.DataFrame()
    if 'multi_day' in locals():
        if total_day == 1:
            devices = devices.reset_index()  # make sure indexes pair with number of rows
            for index, device in devices.iterrows():
                device_id = device['device_id']
                df = conn.query("select make_timestamp(" + today.strftime("%Y") + "," + today.strftime("%m") + "," + today.strftime("%d") +", extract(hour from measurement_time)::int, extract(minute from measurement_time)::int, 0), AVG(measurement_value) from measurements where measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' and device_id=" + str(device_id) + " and measurement_type_id=27 group by extract(hour from measurement_time), extract(minute from measurement_time) order by extract(hour from measurement_time), extract(minute from measurement_time)", ttl=0)
                if chart_data.empty:
                    chart_data = pd.DataFrame(df, columns=['make_timestamp', 'avg'])
                    chart_data['make_timestamp'] = pd.to_datetime(chart_data['make_timestamp']) # para converter para datetime
                    #chart_data['make_timestamp'] -= pd.to_timedelta(3, unit='h')
                    chart_data = chart_data.rename(columns={"make_timestamp": "Horário"})
                    chart_data = chart_data.set_index('Horário')
                else:
                    chart_data2 = pd.DataFrame(df, columns=['make_timestamp', 'avg'])
                    chart_data2['make_timestamp'] = pd.to_datetime(chart_data2['make_timestamp']) # para converter para datetime
                    #chart_data2['make_timestamp'] -= pd.to_timedelta(3, unit='h')
                    chart_data2 = chart_data2.rename(columns={"make_timestamp": "Horário"})
                    chart_data2 = chart_data2.set_index('Horário')
                    chart_data = chart_data.add(chart_data2, fill_value=None)
        else:
            for m in multi_day:
                device_id = devices[devices['device_name']==m].index.values.item(0)
                #df = conn.query("select measurement_value, measurement_time from measurements where measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 05:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 19:59:59' and device_id=" + str(device_id) + " and measurement_type_id=1 order by measurement_time", ttl=0)
                df = conn.query("select make_timestamp(" + today.strftime("%Y") + "," + today.strftime("%m") + "," + today.strftime("%d") +", extract(hour from measurement_time)::int, extract(minute from measurement_time)::int, 0), AVG(measurement_value) from measurements where measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' and device_id=" + str(device_id) + " and measurement_type_id=27 group by extract(hour from measurement_time), extract(minute from measurement_time) order by extract(hour from measurement_time), extract(minute from measurement_time)", ttl=0)
                if chart_data.empty:
                    chart_data = pd.DataFrame(df, columns=['make_timestamp', 'avg'])
                    chart_data['make_timestamp'] = pd.to_datetime(chart_data['make_timestamp']) # para converter para datetime
                    #chart_data['make_timestamp'] -= pd.to_timedelta(3, unit='h')
                    chart_data = chart_data.rename(columns={"make_timestamp": "Horário"})
                    chart_data = chart_data.set_index('Horário')
                else:
                    chart_data2 = pd.DataFrame(df, columns=['make_timestamp', 'avg'])
                    chart_data2['make_timestamp'] = pd.to_datetime(chart_data2['make_timestamp']) # para converter para datetime
                    #chart_data2['make_timestamp'] -= pd.to_timedelta(3, unit='h')
                    chart_data2 = chart_data2.rename(columns={"make_timestamp": "Horário"})
                    chart_data2 = chart_data2.set_index('Horário')
                    chart_data = chart_data.add(chart_data2, fill_value=None)

        chart_data = chart_data.rename(columns={"avg": "Energia consumida em kw"})
        #st.line_chart(chart_data, height=500, y="Energia gerada em kw")
        fig = px.area(chart_data)
        fig.update_layout(xaxis_title=dict(text='Horário'),
            yaxis_title=dict(text='Energia consumida em kw'),
            showlegend=False,
            height=500)

        # Plot!
        st.plotly_chart(fig, use_container_width=True)
        conn.reset()

with tab2:
    st.header('Total de consumo no mês')
    c = st.container()
    with c:
        col1, col2, col3 = st.columns([0.17, 0.1, 0.63])


    conn = st.connection("my_database")
    with col1:
        option = st.selectbox(
            "Selecione a unidade consumidora",
            ("TRAFO 1", "TRAFO 2", "TRAFO 3", "TRAFO 4", "Total"),
            key="month_combo")
        
    today = datetime.datetime.now()
    month = int(today.strftime("%m"))
    options = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    with col2:

        option_month = st.selectbox(
            "Selecione o mês",
            options,
            key="month_combo2",
            index=month-1)

    df = conn.query("select * from devices where device_type=2 order by device_name")
    devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
    devices = devices.set_index('device_id')

    total = 0
    match option:
        case "TRAFO 1":
            with col3:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="month",
                    default=["Meter_TR1_BLOCO_B", "Meter_TR1_BLOCO_C", "Meter_TR1_BLOCO_D", "Meter_TR1_BLOCO_F", "Meter_TR1_BLOCO_H", "Meter_TR1_BLOCO_I", "Meter_TR1_BLOCO_J", "Meter_TR1_BLOCO_L", "Meter_TR1_BLOCO_M", "Meter_TR1_BLOCO_N"])
        case "TRAFO 2":
            with col3:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="month",
                    default=["Meter_TR2_BLOCO_J1", "Meter_TR2_BLOCO_M", "Meter_TR2_BLOCO_N"])
        case "TRAFO 3":
            with col3:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="month",
                    default=["Meter_TR3_BLOCO_V", "Meter_TR3_BLOCO_V_AC", "Meter_TR3_BLOCO_W"])
        case "TRAFO 4":
            with col3:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="month",
                    default=["Meter_TR4_BLOCO_KY", "Meter_TR4_BLOCO_O", "Meter_TR4_BLOCO_P", "Meter_TR4_BLOCO_Q", "Meter_TR4_BLOCO_R", "Meter_TR4_BLOCO_RU", "Meter_TR4_BLOCO_S", "Meter_TR4_BLOCO_T", "Meter_TR4_BLOCO_U", "Meter_TR4_BLOCO_Z", "Meter_TR4_ILUM_EXTER"])
        case "Total":
            with col3:
                total = 1
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    [" "],
                    key="month",
                    default=[" "])
                
    chart_data = pd.DataFrame()
    #print(option_month)
    month_index = options.index(option_month) + 1
    #print(month_index)
    if today.day == 1 and month_index == today.month:
        if total == 1:
            devices = devices.reset_index()  # make sure indexes pair with number of rows
            for index, device in devices.iterrows():
                device_id = device['device_id']
                df = conn.query("select day, sum(pico) as pico_mes from picosdiariosmedidores where year=" + today.strftime("%Y") + " and month=" + str(month_index) + " group by day order by day", ttl=0)
                if chart_data.empty:
                    chart_data = pd.DataFrame(df, columns=['day', 'pico_mes'])
                    chart_data = chart_data.rename(columns={"pico_mes": "Energia gerada em kwh"})
                    chart_data = chart_data.rename(columns={"day": "Dia do mês"})
                    chart_data = chart_data.set_index('Dia do mês')

                    if month_index == today.month:
                        df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + " and measurement_type_id=27 and measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' group by day order by day", ttl=0)
                        chart_data3 = pd.DataFrame(df, columns=['day', 'max'])
                        chart_data3 = chart_data3.rename(columns={"max": "Energia gerada em kwh"})
                        chart_data3 = chart_data3.rename(columns={"day": "Dia do mês"})
                        chart_data3 = chart_data3.set_index('Dia do mês')
                        chart_data = pd.concat([chart_data, chart_data3])
                else:
                    chart_data2 = pd.DataFrame(df, columns=['day', 'pico_mes'])
                    chart_data2 = chart_data2.rename(columns={"pico_mes": "Energia gerada em kwh"})
                    chart_data2 = chart_data2.rename(columns={"day": "Dia do mês"})
                    chart_data2 = chart_data2.set_index('Dia do mês')
        else:
            for m in multi_month:
                device_id = devices[devices['device_name']==m].index.values.item(0)
                df = conn.query("select day, sum(pico) as pico_mes from picosdiariosmedidores natural join devices where device_id=" + str(device_id) + " and year=" + today.strftime("%Y") + " and month=" + str(month_index) + " group by day order by day", ttl=0)
                if chart_data.empty:
                    chart_data = pd.DataFrame(df, columns=['day', 'pico_mes'])
                    chart_data = chart_data.rename(columns={"pico_mes": "Energia gerada em kwh"})
                    chart_data = chart_data.rename(columns={"day": "Dia do mês"})
                    chart_data = chart_data.set_index('Dia do mês')

                    if month_index == today.month:
                        df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + " and measurement_type_id=27 and measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' group by day order by day", ttl=0)
                        chart_data3 = pd.DataFrame(df, columns=['day', 'max'])
                        chart_data3 = chart_data3.rename(columns={"max": "Energia gerada em kwh"})
                        chart_data3 = chart_data3.rename(columns={"day": "Dia do mês"})
                        chart_data3 = chart_data3.set_index('Dia do mês')
                        chart_data = pd.concat([chart_data, chart_data3])
                else:
                    chart_data2 = pd.DataFrame(df, columns=['day', 'pico_mes'])
                    chart_data2 = chart_data2.rename(columns={"pico_mes": "Energia gerada em kwh"})
                    chart_data2 = chart_data2.rename(columns={"day": "Dia do mês"})
                    chart_data2 = chart_data2.set_index('Dia do mês')

                    if month_index == today.month:
                        df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + " and measurement_type_id=27 and measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' group by day order by day", ttl=0)
                        chart_data4 = pd.DataFrame(df, columns=['day', 'max'])
                        chart_data4 = chart_data4.rename(columns={"max": "Energia gerada em kwh"})
                        chart_data4 = chart_data4.rename(columns={"day": "Dia do mês"})
                        chart_data4 = chart_data4.set_index('Dia do mês')
                        chart_data2 = pd.concat([chart_data2, chart_data4])
                    chart_data = chart_data.add(chart_data2, fill_value=0)
    else:
        if total == 1:
            #devices = devices.reset_index()  # make sure indexes pair with number of rows
            #for index, device in devices.iterrows():
            #    device_id = device['device_id']
            df = conn.query("select day, sum(pico) as pico_mes from picosdiariosmedidores where year=" + today.strftime("%Y") + " and month=" + str(month_index) + " group by day order by day", ttl=0)
            chart_data = pd.DataFrame(df, columns=['day', 'pico_mes'])
            chart_data = chart_data.rename(columns={"pico_mes": "Energia gerada em kwh"})
            chart_data = chart_data.rename(columns={"day": "Dia do mês"})
            chart_data = chart_data.set_index('Dia do mês')
        else:
            for m in multi_month:
                device_id = devices[devices['device_name']==m].index.values.item(0)
                df = conn.query("select day, sum(pico) as pico_mes from picosdiariosmedidores natural join devices where device_id=" + str(device_id) + " and year=" + today.strftime("%Y") + " and month=" + str(month_index) + " group by day order by day", ttl=0)
                if chart_data.empty:
                    chart_data = pd.DataFrame(df, columns=['day', 'pico_mes'])
                    if today.day == 1 and month_index == today.month:
                        df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + " and measurement_type_id=27 and measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' group by day order by day", ttl=0)
                        chart_data = pd.DataFrame(df, columns=['day', 'max'])
                        chart_data = chart_data.rename(columns={"max": "Energia gerada em kwh"})
                        chart_data = chart_data.rename(columns={"day": "Dia do mês"})
                        chart_data = chart_data.set_index('Dia do mês')
                    else:
                        chart_data = chart_data.rename(columns={"pico_mes": "Energia gerada em kwh"})
                        chart_data = chart_data.rename(columns={"day": "Dia do mês"})
                        chart_data = chart_data.set_index('Dia do mês')

                        if month_index == today.month:
                            df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + " and measurement_type_id=27 and measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' group by day order by day", ttl=0)
                            chart_data3 = pd.DataFrame(df, columns=['day', 'max'])
                            chart_data3 = chart_data3.rename(columns={"max": "Energia gerada em kwh"})
                            chart_data3 = chart_data3.rename(columns={"day": "Dia do mês"})
                            chart_data3 = chart_data3.set_index('Dia do mês')
                            chart_data = pd.concat([chart_data, chart_data3])
                else:
                    chart_data2 = pd.DataFrame(df, columns=['day', 'pico_mes'])
                    if today.day == 1 and month_index == today.month:
                        df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + " and measurement_type_id=27 and measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' group by day order by day", ttl=0)
                        chart_data2 = pd.DataFrame(df, columns=['day', 'max'])
                        chart_data2 = chart_data2.rename(columns={"max": "Energia gerada em kwh"})
                        chart_data2 = chart_data2.rename(columns={"day": "Dia do mês"})
                        chart_data2 = chart_data2.set_index('Dia do mês')
                        chart_data = chart_data.add(chart_data2, fill_value=0)
                    else:
                        chart_data2 = chart_data2.rename(columns={"pico_mes": "Energia gerada em kwh"})
                        chart_data2 = chart_data2.rename(columns={"day": "Dia do mês"})
                        chart_data2 = chart_data2.set_index('Dia do mês')

                        if month_index == today.month:
                            df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + " and measurement_type_id=27 and measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 00:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 23:59:59' group by day order by day", ttl=0)
                            chart_data4 = pd.DataFrame(df, columns=['day', 'max'])
                            chart_data4 = chart_data4.rename(columns={"max": "Energia gerada em kwh"})
                            chart_data4 = chart_data4.rename(columns={"day": "Dia do mês"})
                            chart_data4 = chart_data4.set_index('Dia do mês')
                            chart_data2 = pd.concat([chart_data2, chart_data4])
                        chart_data = chart_data.add(chart_data2, fill_value=0)

    number_of_days = calendar.monthrange(today.year, month_index)[1]
    #st.bar_chart(chart_data, height=500, y="Energia gerada em kwh")
    chart_data = chart_data.div(1000)

    fig = px.bar(chart_data)
    fig.update_layout(xaxis_title=dict(text='Dia do mês'),
        yaxis_title=dict(text='Energia consumida em kwh'),
        showlegend=False,
        xaxis_dtick = 1,
        xaxis_range=[1,number_of_days],
        height=500)

    # Plot!
    st.plotly_chart(fig, use_container_width=True)
    conn.reset()


with tab3:
    st.header('Total de geração no ano')
    c = st.container()
    with c:
        col1, col2, col3 = st.columns([0.17, 0.1, 0.63])


    conn = st.connection("my_database")
    with col1:
        option = st.selectbox(
            "Selecione a unidade consumidora",
            ("TRAFO 1", "TRAFO 2", "TRAFO 3", "TRAFO 4", "Total"),
            key="year_combo")
        
    today = datetime.datetime.now()
    year = int(today.strftime("%Y"))
    options = ["2024"]
    with col2:
        option_year = st.selectbox(
            "Selecione o ano",
            options,
            key="year_combo2",
            index=year-2024)

    df = conn.query("select * from devices where device_type=2 order by device_name")
    devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
    devices = devices.set_index('device_id')

    total_year = 0
    match option:
        case "TRAFO 1":
            with col3:
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="year",
                    default=["Meter_TR1_BLOCO_B", "Meter_TR1_BLOCO_C", "Meter_TR1_BLOCO_D", "Meter_TR1_BLOCO_F", "Meter_TR1_BLOCO_H", "Meter_TR1_BLOCO_I", "Meter_TR1_BLOCO_J", "Meter_TR1_BLOCO_L", "Meter_TR1_BLOCO_M", "Meter_TR1_BLOCO_N"])
        case "TRAFO 2":
            with col3:
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="year",
                    default=["Meter_TR2_BLOCO_J1", "Meter_TR2_BLOCO_M", "Meter_TR2_BLOCO_N"])
        case "TRAFO 3":
            with col3:
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="year",
                    default=["Meter_TR3_BLOCO_V", "Meter_TR3_BLOCO_V_AC", "Meter_TR3_BLOCO_W"])
        case "TRAFO 4":
            with col3:
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="year",
                    default=["Meter_TR4_BLOCO_KY", "Meter_TR4_BLOCO_O", "Meter_TR4_BLOCO_P", "Meter_TR4_BLOCO_Q", "Meter_TR4_BLOCO_R", "Meter_TR4_BLOCO_RU", "Meter_TR4_BLOCO_S", "Meter_TR4_BLOCO_T", "Meter_TR4_BLOCO_U", "Meter_TR4_BLOCO_Z", "Meter_TR4_ILUM_EXTER"])
        case "Total":
            with col3:
                total_year = 1
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    [" "],
                    key="year",
                    default=[" "])
                
    chart_data = pd.DataFrame()
    year_index = options.index(option_year) + 2024

    if total_year == 1:
        df = conn.query("select month, sum(pico) as picos from picosdiariosmedidores where year=" + str(year_index) + " group by month order by month", ttl=0)
        chart_data = pd.DataFrame(df, columns=['month', 'picos'])
        chart_data = chart_data.rename(columns={"picos": "Energia consumida em MWh"})
        chart_data = chart_data.rename(columns={"month": "Meses do ano"})
        chart_data = chart_data.set_index('Meses do ano')
    else:
        for m in multi_year:
            device_id = devices[devices['device_name']==m].index.values.item(0)
            #df = conn.query("select day, sum(pico) as pico_mes from picosdiariosinversores natural join devices where device_id=" + str(device_id) + " and year=" + today.strftime("%Y") + " and month=" + str(month_index) + " group by day order by day")
            df = conn.query("select device_name, month, sum(pico) as picos from picosdiariosmedidores natural join devices where device_id=" + str(device_id) + " and year=" + str(year_index) + " group by (device_name, month) order by month", ttl=0)
            if chart_data.empty:
                chart_data = pd.DataFrame(df, columns=['month', 'picos'])
                chart_data = chart_data.rename(columns={"picos": "Energia consumida em MWh"})
                chart_data = chart_data.rename(columns={"month": "Meses do ano"})
                chart_data = chart_data.set_index('Meses do ano')
            else:
                chart_data2 = pd.DataFrame(df, columns=['month', 'picos'])
                chart_data2 = chart_data2.rename(columns={"picos": "Energia consumida em MWh"})
                chart_data2 = chart_data2.rename(columns={"month": "Meses do ano"})
                chart_data2 = chart_data2.set_index('Meses do ano')
                chart_data = chart_data.add(chart_data2, fill_value=0)

    #st.bar_chart(chart_data, height=500, y="Energia gerada em kwh")
    chart_data = chart_data.div(1000000)

    fig = px.bar(chart_data)
    fig.update_layout(xaxis_title=dict(text='Meses do ano'),
        yaxis_title=dict(text='Energia consumida em MWh'),
        showlegend=False,
        xaxis_dtick = 1,
        xaxis_range=[1,12],
        height=500)

    # Plot!
    st.plotly_chart(fig, use_container_width=True)
    conn.reset()
