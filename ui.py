"""Identidade visual compartilhada do painel de energia da UTFPR."""
from pathlib import Path
from html import escape
import base64

import streamlit as st

def setup_page(title, description, compact=False):
    st.set_page_config(page_title=f"{title} | SolarDash", page_icon="☀️", layout="wide", initial_sidebar_state="auto")
    css = (Path(__file__).parent / "assets" / "theme.css").read_text()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    if compact:
        st.markdown('<header class="dashboard-heading"><div class="dashboard-identity">'
                    f'<h1>{escape(title)}</h1><p>{escape(description)}</p></div>'
                    '</header>', unsafe_allow_html=True)
        return
    st.markdown('<div class="topline">CENTRAL DE MONITORAMENTO <span>UTFPR / PATO BRANCO</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero"><div><div class="eyebrow">ENERGIA EM FOCO</div>'
                f'<h1>{escape(title)}</h1><p>{escape(description)}</p></div>'
                '<div class="hero-sun" aria-hidden="true">☀</div></div>', unsafe_allow_html=True)


def render_sidebar(pages):
    logo = base64.b64encode((Path(__file__).parent / 'assets' / 'utfpr-pb-negativa.png').read_bytes()).decode('ascii')
    with st.sidebar:
        st.markdown('<div class="sidebar-identity"><div class="sidebar-wordmark">'
                    '<span class="sidebar-sun" aria-hidden="true">☀</span> Solar<span>Dash</span></div>'
                    '<p>GESTÃO ENERGÉTICA</p></div>'
                    '<div class="sidebar-section">MONITORAMENTO</div>', unsafe_allow_html=True)
        for group in pages.values():
            for page in group:
                st.page_link(page, label=page.title, icon=page.icon, use_container_width=True)
        st.markdown('<footer class="sidebar-campus-logo">'
                    f'<img src="data:image/png;base64,{logo}" alt="UTFPR — Campus Pato Branco">'
                    '</footer>', unsafe_allow_html=True)


def period_selector():
    period = st.segmented_control("Período de análise", ["Dia", "Mês", "Ano"], default="Dia", selection_mode="single")
    return {"Dia": "tab1", "Mês": "tab2", "Ano": "tab3"}.get(period, "tab1")


def render_chart(fig, **kwargs):
    if not any(len(trace.x) if trace.x is not None else 0 for trace in fig.data):
        st.info("Nenhuma medição para exibir. Selecione dispositivos e um período com dados disponíveis.")
        return
    colors = ["#f28b24", "#197bba", "#14a89a", "#735cbd", "#df617a", "#365b80"]
    fig.update_layout(
        template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        colorway=colors, font=dict(family="Arial, sans-serif", color="#52647a", size=13),
        margin=dict(l=24, r=24, t=55, b=30), hovermode="x unified",
        legend=dict(orientation="h", y=-0.2, title_text=""),
        title=dict(font=dict(size=18, color="#102c4c")),
    )
    for index, trace in enumerate(fig.data):
        color = colors[index % len(colors)]
        if trace.type == "scatter":
            trace.update(line=dict(color=color, width=3))
            if trace.fill and trace.fill != "none":
                trace.update(fillcolor="rgba(242,139,36,0.14)")
        elif trace.type == "bar":
            trace.update(marker_color=color)
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="#edf1f5", zeroline=False)
    with st.container(border=True):
        st.plotly_chart(fig, theme=None, **kwargs)
