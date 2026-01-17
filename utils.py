import streamlit as st

def sanitize_text(text):
    if text is None:
        return ""
    return str(text)


def load_css(file_path):
    with open(file_path) as f:
        st.html(f"<style>{f.read()}</style>")


