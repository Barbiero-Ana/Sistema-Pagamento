import streamlit as st
import pandas as pd
from pagamentos import Cartao, Paypal, Transferencia, Pix, Cripto, system

st.set_page_config(page_title="Sistema de Pagamentos", layout="wide")
st.title("💳 Sistema de Processamento de Pagamentos")

# Formulário de pagamento
st.sidebar.header("📝 Novo Pagamento")
metodo = st.sidebar.selectbox("Escolha o método de pagamento", ["Cartão", "Paypal", "Transferência", "Pix", "Cripto"])

valor = st.sidebar.number_input("Valor", min_value=0.01)

def processar_e_exibir(metodo_pagamento):
    system(metodo_pagamento)
    st.success(f"Status: {metodo_pagamento.status}")
    st.toast(f"Transação registrada como {metodo_pagamento.status}")

# Formulários específicos por método
if metodo == "Cartão":
    numero = st.sidebar.text_input("Número do cartão")
    nome = st.sidebar.text_input("Nome do titular")
    validade = st.sidebar.text_input("Validade (MM/AA)")
    cvv = st.sidebar.text_input("CVV")
    if st.sidebar.button("Processar"):
        try:
            pag = Cartao(valor, numero, nome, validade, cvv)
            processar_e_exibir(pag)
        except Exception as e:
            st.error(str(e))

elif metodo == "Paypal":
    email = st.sidebar.text_input("Email")
    senha = st.sidebar.text_input("Senha", type="password")
    if st.sidebar.button("Processar"):
        pag = Paypal(valor, email, senha)
        processar_e_exibir(pag)

elif metodo == "Transferência":
    banco = st.sidebar.text_input("Banco")
    conta_origem = st.sidebar.text_input("Conta origem")
    conta_destino = st.sidebar.text_input("Conta destino")
    if st.sidebar.button("Processar"):
        pag = Transferencia(valor, banco, conta_origem, conta_destino)
        processar_e_exibir(pag)

elif metodo == "Pix":
    chave = st.sidebar.text_input("Chave Pix")
    if st.sidebar.button("Processar"):
        pag = Pix(valor, chave)
        processar_e_exibir(pag)

elif metodo == "Cripto":
    carteira = st.sidebar.text_input("Endereço da carteira")
    cripto = st.sidebar.selectbox("Criptomoeda", ["BTC", "ETH", "USDT"])
    if st.sidebar.button("Processar"):
        pag = Cripto(valor, carteira, cripto)
        processar_e_exibir(pag)

# Dashboard
st.header("📊 Dashboard de Transações")

try:
    df = pd.read_csv("pagamentos.csv", names=["ID", "Método", "Valor", "Data", "Status"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Transações", len(df))
    col2.metric("Valor Total Aprovado", f"R$ {df[df['Status'] == 'Aprovado']['Valor'].sum():.2f}")
    col3.metric("Taxa de Sucesso", f"{(df['Status'] == 'Aprovado').mean() * 100:.1f}%")

    st.bar_chart(df.groupby("Método")["Valor"].sum())
    st.dataframe(df.sort_values("Data", ascending=False), use_container_width=True)

except FileNotFoundError:
    st.info("Nenhuma transação registrada ainda.")
