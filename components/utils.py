import streamlit as st
import matplotlib.pyplot as plt

def show_chart(df):
    # Crear un gráfico usando Matplotlib
    fig, ax = plt.subplots()
    df.plot(kind='bar', ax=ax)
    st.pyplot(fig)
