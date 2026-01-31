import streamlit as st

def render_header():
    st.markdown(
        "<h2 style='margin-top: 0; margin-bottom: 0.5rem;'>"
        "Switzerland's Energy Dashboard 2025"
        "</h2>",
        unsafe_allow_html=True,
    )
