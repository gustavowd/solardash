import streamlit as st

st.set_page_config(
    page_title="Totalizados",
    page_icon="👋",
)

st.write("# Sistema de monitoramento energético do Campus Pato Branco da UTFPR")

#st.sidebar.success("Selecione um tipo de dispositivo")

st.markdown(
    """
    ### Totalizadores
    Nessa página futuramente estará disponível os valores totais de geração fotovoltaica e de consumo por bloco em kwh.
    Por enquanto, selecione um tipo de dispositivo para realizar as consultas.
"""
)
