import streamlit as st

# Título do aplicativo
st.title("Minha Primeira Calculadora Streamlit")
st.write("Esta é uma calculadora simples para somar dois números.")

# Entradas para os números
numero1 = st.number_input("Digite o primeiro número:", value=0.0, format="%.2f")
numero2 = st.number_input("Digite o segundo número:", value=0.0, format="%.2f")

# Botão para calcular
if st.button("Somar Números"):
    soma = numero1 + numero2
    st.success(f"A soma de {numero1} e {numero2} é: {soma}")
    st.balloons() # Um pequeno efeito visual para comemorar!

st.markdown("---")
st.write("Desenvolvido para testar o Streamlit.")