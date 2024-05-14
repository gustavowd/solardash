import streamlit as st
import pandas as pd
import datetime
import plotly.express as px

st.set_page_config(
    page_title="Sistema de monitoramento energético do Campus Pato Branco da UTFPR",
    layout="wide"
)

tab1, tab2, tab3 = st.tabs(["📈 Dia", "Mês", "Ano"])

with tab1:
    st.header('Total de geração no dia')
    c = st.container()
    with c:
        col1, col2 = st.columns([0.2,0.8])


    conn = st.connection("my_database")
    with col1:
        option = st.selectbox(
            "Selecione a unidade consumidora",
            (" ", "UTFPR-76942716", "Politec-73134759", "Area Ex.-88481328", "Total"),
            key="day_combo")

    df = conn.query("select * from devices where device_type=1 order by device_name")
    devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
    devices = devices.set_index('device_id')

    match option:
        case "UTFPR-76942716":
            with col2:
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day",
                    default=["Huawei - 21010738716TK4900687", "Huawei - 21010738716TK4900689", "Huawei - 21010738716TK4900706", "Huawei - 21010738716TK6901199", "Huawei - 21010738716TK6901301", "Huawei - 21010738716TK6901324", "Huawei - 21010738716TK6901325"])
        case "Politec-73134759":
            with col2:
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day",
                    default=["Fronius - 29271811", "Solis - 1812051232060001"])
        case "Area Ex.-88481328":
            with col2:
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day",
                    default=["Solis - 118 DB22B09 047"])
        case "Total":
            with col2:
                multi_day = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day",
                    default=["Fronius - 29271811", "Huawei - 21010738716TK4900687", "Huawei - 21010738716TK4900689", "Huawei - 21010738716TK4900706", "Huawei - 21010738716TK6901199", "Huawei - 21010738716TK6901301", "Huawei - 21010738716TK6901324", "Huawei - 21010738716TK6901325", "Solis - 118 DB22B09 047", "Solis - 1812051232060001"])
        case _ :
            with col2:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="day")
                
    today = datetime.datetime.now()
    chart_data = pd.DataFrame()
    if 'multi_day' in locals():
        for m in multi_day:
            device_id = devices[devices['device_name']==m].index.values.item(0)
            df = conn.query("select measurement_value, measurement_time from measurements where measurement_time between '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 05:00:01' and '" + today.strftime("%Y") + "-" + today.strftime("%m") + "-" + today.strftime("%d") + " 19:59:59' and device_id=" + str(device_id) + " and measurement_type_id=1 order by measurement_time")
            if chart_data.empty:
                chart_data = pd.DataFrame(df, columns=['measurement_time', 'measurement_value'])
                chart_data['measurement_time'] = pd.to_datetime(chart_data['measurement_time']) # para converter para datetime
                chart_data['measurement_time'] -= pd.to_timedelta(3, unit='h')
                chart_data = chart_data.set_index('measurement_time')
            else:
                chart_data2 = pd.DataFrame(df, columns=['measurement_time', 'measurement_value'])
                chart_data2['measurement_time'] = pd.to_datetime(chart_data2['measurement_time']) # para converter para datetime
                chart_data2['measurement_time'] -= pd.to_timedelta(3, unit='h')
                chart_data2 = chart_data2.set_index('measurement_time')
                chart_data = chart_data.add(chart_data2, fill_value=None)

        chart_data = chart_data.div(1000)
        chart_data = chart_data.rename(columns={"measurement_value": "Energia gerada em kw"})
        #st.line_chart(chart_data, height=500, y="Energia gerada em kw")
        fig = px.line(chart_data)
        fig.update_layout(xaxis_title=dict(text='Horário'),
            yaxis_title=dict(text='Energia gerada em kw'),
            showlegend=False,
            height=500)

        # Plot!
        st.plotly_chart(fig, use_container_width=True)
        conn.reset()

with tab2:
    st.header('Total de geração no mês')
    c = st.container()
    with c:
        col1, col2, col3 = st.columns([0.17, 0.1, 0.63])


    conn = st.connection("my_database")
    with col1:
        option = st.selectbox(
            "Selecione a unidade consumidora",
            ("UTFPR-76942716", "Politec-73134759", "Area Ex.-88481328", "Total"),
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

    df = conn.query("select * from devices where device_type=1 order by device_name")
    devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
    devices = devices.set_index('device_id')

    match option:
        case "UTFPR-76942716":
            with col3:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="month",
                    default=["Huawei - 21010738716TK4900687", "Huawei - 21010738716TK4900689", "Huawei - 21010738716TK4900706", "Huawei - 21010738716TK6901199", "Huawei - 21010738716TK6901301", "Huawei - 21010738716TK6901324", "Huawei - 21010738716TK6901325"])
        case "Politec-73134759":
            with col3:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="month",
                    default=["Fronius - 29271811", "Solis - 1812051232060001"])
        case "Area Ex.-88481328":
            with col3:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="month",
                    default=["Solis - 118 DB22B09 047"])
        case "Total":
            with col3:
                multi_month = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="month",
                    default=["Fronius - 29271811", "Huawei - 21010738716TK4900687", "Huawei - 21010738716TK4900689", "Huawei - 21010738716TK4900706", "Huawei - 21010738716TK6901199", "Huawei - 21010738716TK6901301", "Huawei - 21010738716TK6901324", "Huawei - 21010738716TK6901325", "Solis - 118 DB22B09 047", "Solis - 1812051232060001"])
                
    chart_data = pd.DataFrame()
    #print(option_month)
    month_index = options.index(option_month) + 1
    #print(month_index)
    for m in multi_month:
        device_id = devices[devices['device_name']==m].index.values.item(0)
        #df = conn.query("select day,max(measurement_value) from measurements natural join time where device_id=" + str(device_id) + " and measurement_type_id=7 and measurement_time between '" + today.strftime("%Y") + "-" + str(month_index) + "-01 00:00:01' and '" + today.strftime("%Y") + "-" + str(month_index) + "-30 23:59:59' group by day order by day")
        df = conn.query("select day, sum(pico) as pico_mes from picosdiariosinversores natural join devices where device_id=" + str(device_id) + " and year=" + today.strftime("%Y") + " and month=" + str(month_index) + " group by day order by day")
        if chart_data.empty:
            chart_data = pd.DataFrame(df, columns=['day', 'pico_mes'])
            chart_data = chart_data.rename(columns={"pico_mes": "Energia gerada em kwh"})
            chart_data = chart_data.rename(columns={"day": "Dia do mês"})
            chart_data = chart_data.set_index('Dia do mês')
        else:
            chart_data2 = pd.DataFrame(df, columns=['day', 'pico_mes'])
            chart_data2 = chart_data2.rename(columns={"pico_mes": "Energia gerada em kwh"})
            chart_data2 = chart_data2.rename(columns={"day": "Dia do mês"})
            chart_data2 = chart_data2.set_index('Dia do mês')
            chart_data = chart_data.add(chart_data2, fill_value=0)

    chart_data = chart_data.div(1000)
    #st.bar_chart(chart_data, height=500, y="Energia gerada em kwh")

    fig = px.bar(chart_data)
    fig.update_layout(xaxis_title=dict(text='Dia do mês'),
        yaxis_title=dict(text='Energia gerada em kwh'),
        showlegend=False,
        xaxis_dtick = 1,
        xaxis_range=[1,31],
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
            ("UTFPR-76942716", "Politec-73134759", "Area Ex.-88481328", "Total"),
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

    df = conn.query("select * from devices where device_type=1 order by device_name")
    devices = pd.DataFrame(df, columns=['device_name', 'device_id', 'device_type'])
    devices = devices.set_index('device_id')

    match option:
        case "UTFPR-76942716":
            with col3:
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="year",
                    default=["Huawei - 21010738716TK4900687", "Huawei - 21010738716TK4900689", "Huawei - 21010738716TK4900706", "Huawei - 21010738716TK6901199", "Huawei - 21010738716TK6901301", "Huawei - 21010738716TK6901324", "Huawei - 21010738716TK6901325"])
        case "Politec-73134759":
            with col3:
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="year",
                    default=["Fronius - 29271811", "Solis - 1812051232060001"])
        case "Area Ex.-88481328":
            with col3:
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="year",
                    default=["Solis - 118 DB22B09 047"])
        case "Total":
            with col3:
                multi_year = st.multiselect(
                    'Selecione um ou mais dispositivos:',
                    df['device_name'],
                    key="year",
                    default=["Fronius - 29271811", "Huawei - 21010738716TK4900687", "Huawei - 21010738716TK4900689", "Huawei - 21010738716TK4900706", "Huawei - 21010738716TK6901199", "Huawei - 21010738716TK6901301", "Huawei - 21010738716TK6901324", "Huawei - 21010738716TK6901325", "Solis - 118 DB22B09 047", "Solis - 1812051232060001"])
                
    chart_data = pd.DataFrame()
    year_index = options.index(option_year) + 2024
    for m in multi_year:
        device_id = devices[devices['device_name']==m].index.values.item(0)
        #df = conn.query("select day, sum(pico) as pico_mes from picosdiariosinversores natural join devices where device_id=" + str(device_id) + " and year=" + today.strftime("%Y") + " and month=" + str(month_index) + " group by day order by day")
        df = conn.query("select device_name, month, sum(pico) as picos from picosdiariosinversores natural join devices where device_id=" + str(device_id) + " and year=" + str(year_index) + " group by (device_name, month) order by month")
        if chart_data.empty:
            chart_data = pd.DataFrame(df, columns=['month', 'picos'])
            chart_data = chart_data.rename(columns={"picos": "Energia gerada em kwh"})
            chart_data = chart_data.rename(columns={"month": "Meses do ano"})
            chart_data = chart_data.set_index('Meses do ano')
        else:
            chart_data2 = pd.DataFrame(df, columns=['month', 'picos'])
            chart_data2 = chart_data2.rename(columns={"picos": "Energia gerada em kwh"})
            chart_data2 = chart_data2.rename(columns={"month": "Meses do ano"})
            chart_data2 = chart_data2.set_index('Meses do ano')
            chart_data = chart_data.add(chart_data2, fill_value=0)

    chart_data = chart_data.div(1000)
    #st.bar_chart(chart_data, height=500, y="Energia gerada em kwh")

    fig = px.bar(chart_data)
    fig.update_layout(xaxis_title=dict(text='Meses do ano'),
        yaxis_title=dict(text='Energia gerada em kwh'),
        showlegend=False,
        xaxis_dtick = 1,
        xaxis_range=[1,12],
        height=500)

    # Plot!
    st.plotly_chart(fig, use_container_width=True)
    conn.reset()
