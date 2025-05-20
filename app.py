import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import logging
import io
import smtplib
import os
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()
gestormail = os.environ.get('gestor_mail')
gestorpass = os.environ.get('gestor_password')

from pagamentos import Cartao, Paypal, Transferencia, Pix, Cripto, system

st.set_page_config(page_title='Sistema de Pagamentos', layout='wide')
st.title('Sistema de Processamento de Pagamentos')
logging.basicConfig(filename='logs_erros.log', level=logging.ERROR)

# def enviar_email_simulado(destinatario, assunto, corpo):
#     if destinatario:
#         st.info(f'Email enviado para {destinatario}: {assunto}')

# -------- corrigindo o envio de emailssssss

def enviar_email(destinatario, assunto, corpo):
    if not destinatario:
        st.warning("Nenhum destinatário fornecido. E-mail não enviado.")
        return

    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = gestormail  
    sender_password = gestorpass
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = destinatario
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  
        server.login(sender_email, sender_password)  
        server.sendmail(sender_email, destinatario, msg.as_string())  
        server.quit()  

        st.info(f"E-mail enviado com sucesso para {destinatario}: {assunto}")
    except Exception as e:
        logging.error(f"Erro ao enviar e-mail para {destinatario}: {e}")
        st.error(f"Erro ao enviar e-mail: {e}")

def carregar_transacoes():
    try:
        df = pd.read_csv('pagamentos.csv', names=['ID', 'Método', 'Valor', 'Data', 'Status'], parse_dates=['Data'], dayfirst=True)
        df['Data'] = pd.to_datetime(df['Data'], format='%d-%m-%Y %H:%M:%S', errors='coerce')
        return df.dropna()
    except FileNotFoundError:
        return pd.DataFrame(columns=['ID', 'Método', 'Valor', 'Data', 'Status'])
    except Exception as e:
        logging.error(f'Erro ao carregar CSV: {e}')
        return pd.DataFrame()

def processar_e_exibir(metodo_pagamento, email=None):
    try:
        with st.spinner('Processando...'):
            system(metodo_pagamento)  

        if metodo_pagamento.status == 'Aprovado':
            st.success('✅ Pagamento aprovado!')
            st.balloons()
        else:
            st.error('!Pagamento recusado!')

        if email:
            enviar_email(email, 'Status do pagamento', f'Seu pagamento foi {metodo_pagamento.status}.')

        st.toast(f'Status: {metodo_pagamento.status}')
    except Exception as e:
        logging.error(f'Erro ao processar pagamento: {e}')
        st.error('Erro ao processar pagamento.')





# ===== Sidebar: Formas de pagamento =====

st.sidebar.header('Novo Pagamento')
metodo = st.sidebar.selectbox('Método', ['Cartão', 'Paypal', 'Transferência', 'Pix', 'Cripto'])
valor = st.sidebar.number_input('Valor', min_value=0.00, format='%.2f')
email_usuario = st.sidebar.text_input('Email para notificação (opcional)')

if metodo == 'Cartão':
    numero = st.sidebar.text_input('Número do cartão')
    nome = st.sidebar.text_input('Nome do titular')
    validade = st.sidebar.text_input('Validade (MM/AA)')
    cvv = st.sidebar.text_input('CVV')
    if st.sidebar.button('Processar'):
        if all([numero, nome, validade, cvv]):
            try:
                pag = Cartao(valor, numero, nome, validade, cvv)
                processar_e_exibir(pag, email_usuario)
            except Exception as e:
                st.error(str(e))
                logging.error(f'Erro Cartão: {e}')
        else:
            st.warning('Preencha todos os campos do cartão.')

elif metodo == 'Paypal':
    email_paypal = st.sidebar.text_input('Email PayPal')
    senha = st.sidebar.text_input('Senha', type='password')
    if st.sidebar.button('Processar'):
        if email_paypal and senha:
            pag = Paypal(valor, email_paypal, senha)
            processar_e_exibir(pag, email_usuario)
        else:
            st.warning('Preencha email e senha do PayPal.')

elif metodo == 'Transferência':
    banco = st.sidebar.text_input('Banco')
    conta_origem = st.sidebar.text_input('Conta origem')
    conta_destino = st.sidebar.text_input('Conta destino')
    if st.sidebar.button('Processar'):
        if all([banco, conta_origem, conta_destino]):
            pag = Transferencia(valor, banco, conta_origem, conta_destino)
            processar_e_exibir(pag, email_usuario)
        else:
            st.warning('Preencha todos os dados bancários.')

elif metodo == 'Pix':
    chave = st.sidebar.text_input('Chave Pix')
    if st.sidebar.button('Processar'):
        if chave:
            pag = Pix(valor, chave)
            processar_e_exibir(pag, email_usuario)
        else:
            st.warning('Informe a chave Pix.')

elif metodo == 'Cripto':
    carteira = st.sidebar.text_input('Endereço da carteira')
    cripto = st.sidebar.selectbox('Criptomoeda', ['BTC', 'ETH', 'USDT'])
    if st.sidebar.button('Processar'):
        if carteira:
            pag = Cripto(valor, carteira, cripto)
            processar_e_exibir(pag, email_usuario)
        else:
            st.warning('Informe o endereço da carteira.')



# ===== Dashboard =====

st.header('Dashboard de Transações')
df = carregar_transacoes()

if not df.empty:
    with st.expander('Filtro'):
        colf1, colf2, colf3 = st.columns(3)
        
        # Definir valores padrão para as datas
        default_data_inicial = pd.to_datetime(df['Data'].min()).date() if not df.empty else datetime.date.today()
        default_data_final = pd.to_datetime(df['Data'].max()).date() if not df.empty else datetime.date.today()
        
        # Forçar conversão para evitar problemas com datetime.date
        try:
            default_data_inicial = default_data_inicial if isinstance(default_data_inicial, datetime.date) else datetime.date.today()
            default_data_final = default_data_final if isinstance(default_data_final, datetime.date) else datetime.date.today()
        except Exception as e:
            st.error(f'Erro ao definir datas padrão: {e}')
            default_data_inicial = datetime.date.today()
            default_data_final = datetime.date.today()

        # Usar st.date_input com valores padrão
        data_inicial = colf1.date_input('Data inicial', value=default_data_inicial)
        data_final = colf2.date_input('Data final', value=default_data_final)

        metodo_filtro = colf3.multiselect('Métodos', df['Método'].unique(), default=df['Método'].unique())
        status_filtro = colf3.multiselect('Status', df['Status'].unique(), default=df['Status'].unique())

        # Converter data_inicial e data_final para datetime64[ns] para comparação
        try:
            data_inicial = pd.to_datetime(data_inicial)
            data_final = pd.to_datetime(data_final) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # Incluir todo o dia final
        except Exception as e:
            st.error(f'Erro ao converter datas: {e}')
            data_inicial = pd.to_datetime(datetime.date.today())
            data_final = pd.to_datetime(datetime.date.today()) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

        df_filtrado = df[
            (df['Data'] >= data_inicial) &
            (df['Data'] <= data_final) &
            (df['Método'].isin(metodo_filtro)) &
            (df['Status'].isin(status_filtro))
        ]

    st.subheader('Análises Inteligentes')
    colai1, colai2, colai3 = st.columns(3)
    colai1.metric('💰 Valor Médio', f'R$ {df_filtrado['Valor'].mean():.2f}' if not df_filtrado.empty else 'R$ 0,00')
    colai2.metric('Método Mais Usado', df_filtrado['Método'].mode()[0] if not df_filtrado.empty else 'N/A')
    colai3.metric('Dia com Mais Transações', 
                df_filtrado['Data'].dt.date.value_counts().idxmax().strftime('%d-%m-%Y') if not df_filtrado.empty else 'N/A')

    st.subheader('Visualizações')
    tipo_grafico = st.selectbox('Escolha o tipo de gráfico', ['Barra', 'Pizza', 'Area'])
    if tipo_grafico == 'Barra':
        fig = px.bar(df_filtrado.groupby('Método')['Valor'].sum().reset_index(), x='Método', y='Valor', title='Valor por Método')
    elif tipo_grafico == 'Pizza':
        fig = px.pie(df_filtrado, names='Método', values='Valor', title='Distribuição por Método')
    else:
        df_filtrado_sorted = df_filtrado.sort_values("Data").copy()
        df_filtrado_sorted["Data_str"] = df_filtrado_sorted["Data"].dt.strftime('%Y-%m-%d %H:%M:%S')
        fig = px.area(df_filtrado_sorted, x="Data", y="Valor", color="Método", title="Pagamentos Acumulados por Método")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader('Transações')
    st.dataframe(df_filtrado.sort_values('Data', ascending=False), use_container_width=True)

    buffer = io.BytesIO()
    df_filtrado.to_excel(buffer, index=False, engine='openpyxl')
    st.download_button('📥 Baixar Excel', data=buffer.getvalue(), file_name='transacoes.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

else:
    st.info('Nenhuma transação registrada ainda.')