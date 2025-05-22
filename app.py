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
import re
from database import init_db, cadastrar_usuario, verificar_login, verificar_senha_mestra, listar_administradores, redefinir_senha_admin, carregar_transacoes
from pagamentos import Cartao, Paypal, Transferencia, Pix, Cripto, system

# Configuração inicial
st.set_page_config(page_title='Sistema de Pagamentos', layout='wide')
logging.basicConfig(filename='logs_erros.log', level=logging.ERROR)
load_dotenv()
gestormail = os.environ.get('gestor_mail')
gestorpass = os.environ.get('gestor_password')

# Inicializar banco de dados
init_db()

# Função de envio de e-mail
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

# Função para processar pagamento
def processar_e_exibir(metodo_pagamento, email=None):
    try:
        with st.spinner('Processando...'):
            system(metodo_pagamento)
        
        if metodo_pagamento.status == 'Aprovado':
            st.success('✅ Pagamento aprovado!')
            st.balloons()
        else:
            st.error('🚫 Pagamento recusado')

        if email:
            enviar_email(email, 'Status do pagamento', f'Seu pagamento foi {metodo_pagamento.status}.')
        
        st.toast(f'Status: {metodo_pagamento.status}')
    except Exception as e:
        logging.error(f'Erro ao processar pagamento: {e}')
        st.error(f'Erro ao processar pagamento: {e}')

# Gerenciamento de sessão
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None
    st.session_state['tipo_usuario'] = None

# Tela de login
if not st.session_state['usuario']:
    st.title('Login')
    with st.form('login_form'):
        login = st.text_input('Login')
        senha = st.text_input('Senha', type='password')
        submit = st.form_submit_button('Entrar')
        
        if submit:
            tipo_usuario = verificar_login(login, senha)
            if tipo_usuario:
                st.session_state['usuario'] = login
                st.session_state['tipo_usuario'] = tipo_usuario
                st.success(f'Bem-vindo, {login}!')
                st.rerun()
            else:
                st.error('Login ou senha inválidos.')
    
    st.subheader('Cadastrar Novo Usuário')
    with st.form('cadastro_form'):
        novo_login = st.text_input('Novo Login')
        nova_senha = st.text_input('Nova Senha', type='password')
        tipo_usuario_cadastro = st.selectbox('Tipo de Usuário', ['normal', 'admin']) if st.session_state.get('tipo_usuario') == 'admin' else 'normal'
        senha_mestra = st.text_input('Senha Mestra (necessária para cadastrar administradores)', type='password') if tipo_usuario_cadastro == 'admin' else None
        cadastrar = st.form_submit_button('Cadastrar')
        
        if cadastrar:
            if novo_login and nova_senha:
                if tipo_usuario_cadastro == 'admin' and not st.session_state.get('tipo_usuario') == 'admin':
                    st.error('Apenas administradores podem cadastrar novos administradores.')
                elif tipo_usuario_cadastro == 'admin' and not verificar_senha_mestra(senha_mestra):
                    st.error('Senha mestra inválida.')
                else:
                    tipo = tipo_usuario_cadastro if st.session_state.get('tipo_usuario') == 'admin' else 'normal'
                    if cadastrar_usuario(novo_login, nova_senha, tipo):
                        st.success(f'Usuário {novo_login} cadastrado como {tipo}!')
                    else:
                        st.error('Login já existe.')
            else:
                st.warning('Preencha todos os campos.')
else:
    st.title('Sistema de Processamento de Pagamentos')
    st.write(f'Usuário: {st.session_state["usuario"]} ({st.session_state["tipo_usuario"]})')
    if st.button('Sair'):
        st.session_state['usuario'] = None
        st.session_state['tipo_usuario'] = None
        st.rerun()

    # Seção para administradores: Gerenciamento de usuários
    if st.session_state['tipo_usuario'] == 'admin':
        st.subheader('Gerenciamento de Administradores')
        
        # Listar administradores
        st.write('**Lista de Administradores**')
        admins = listar_administradores()
        if admins:
            for admin in admins:
                st.write(f'- {admin}')
        else:
            st.info('Nenhum administrador encontrado.')
        
        # Redefinir senha de administrador
        with st.form('redefinir_senha_admin_form'):
            admin_login = st.selectbox('Selecionar Administrador', admins)
            nova_senha_admin = st.text_input('Nova Senha', type='password')
            senha_mestra = st.text_input('Senha Mestra', type='password')
            redefinir = st.form_submit_button('Redefinir Senha')
            
            if redefinir:
                if nova_senha_admin and senha_mestra:
                    if verificar_senha_mestra(senha_mestra):
                        if redefinir_senha_admin(admin_login, nova_senha_admin, senha_mestra):
                            st.success(f'Senha do administrador {admin_login} redefinida com sucesso!')
                        else:
                            st.error('Erro ao redefinir senha: administrador não encontrado.')
                    else:
                        st.error('Senha mestra inválida.')
                else:
                    st.warning('Preencha todos os campos.')

    # Sidebar: Formas de pagamento (apenas para usuários normais)
    if st.session_state['tipo_usuario'] == 'normal':
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
                    if not re.match(r'^\d{2}/\d{2}$', validade):
                        st.warning('Validade deve estar no formato MM/AA.')
                    elif not cvv.isdigit() or len(cvv) not in [3, 4]:
                        st.warning('CVV deve ter 3 ou 4 dígitos.')
                    else:
                        try:
                            pag = Cartao(valor, st.session_state['usuario'], numero, nome, validade, cvv)
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
                    try:
                        pag = Paypal(valor, st.session_state['usuario'], email_paypal, senha)
                        processar_e_exibir(pag, email_usuario)
                    except Exception as e:
                        st.error(str(e))
                        logging.error(f'Erro PayPal: {e}')
                else:
                    st.warning('Preencha email e senha do PayPal.')

        elif metodo == 'Transferência':
            banco = st.sidebar.text_input('Banco')
            conta_origem = st.sidebar.text_input('Conta origem')
            conta_destino = st.sidebar.text_input('Conta destino')
            if st.sidebar.button('Processar'):
                if all([banco, conta_origem, conta_destino]):
                    try:
                        pag = Transferencia(valor, st.session_state['usuario'], banco, conta_origem, conta_destino)
                        processar_e_exibir(pag, email_usuario)
                    except Exception as e:
                        st.error(str(e))
                        logging.error(f'Erro Transferência: {e}')
                else:
                    st.warning('Preencha todos os dados bancários.')

        elif metodo == 'Pix':
            chave = st.sidebar.text_input('Chave Pix')
            if st.sidebar.button('Processar'):
                if chave:
                    try:
                        pag = Pix(valor, st.session_state['usuario'], chave)
                        processar_e_exibir(pag, email_usuario)
                    except Exception as e:
                        st.error(str(e))
                        logging.error(f'Erro Pix: {e}')
                else:
                    st.warning('Informe a chave Pix.')

        elif metodo == 'Cripto':
            carteira = st.sidebar.text_input('Endereço da carteira')
            cripto = st.sidebar.selectbox('Criptomoeda', ['BTC', 'ETH', 'USDT'])
            if st.sidebar.button('Processar'):
                if carteira:
                    try:
                        pag = Cripto(valor, st.session_state['usuario'], carteira, cripto)
                        processar_e_exibir(pag, email_usuario)
                    except Exception as e:
                        st.error(str(e))
                        logging.error(f'Erro Cripto: {e}')
                else:
                    st.warning('Informe o endereço da carteira.')

    # Dashboard
    st.header('Dashboard de Transações')
    usuario_login = st.session_state['usuario'] if st.session_state['tipo_usuario'] == 'normal' else None
    df = carregar_transacoes(usuario_login)

    if not df.empty:
        with st.expander('Filtro'):
            colf1, colf2, colf3 = st.columns(3)
            default_data_inicial = pd.to_datetime(df['data'].min()).date() if not df.empty else datetime.date.today()
            default_data_final = pd.to_datetime(df['data'].max()).date() if not df.empty else datetime.date.today()
            
            try:
                default_data_inicial = default_data_inicial if isinstance(default_data_inicial, datetime.date) else datetime.date.today()
                default_data_final = default_data_final if isinstance(default_data_final, datetime.date) else datetime.date.today()
            except Exception as e:
                st.error(f'Erro ao definir datas padrão: {e}')
                default_data_inicial = datetime.date.today()
                default_data_final = datetime.date.today()

            data_inicial = colf1.date_input('Data inicial', value=default_data_inicial)
            data_final = colf2.date_input('Data final', value=default_data_final)
            metodo_filtro = colf3.multiselect('Métodos', df['metodo'].unique(), default=df['metodo'].unique())
            status_filtro = colf3.multiselect('Status', df['status'].unique(), default=df['status'].unique())

            try:
                data_inicial = pd.to_datetime(data_inicial)
                data_final = pd.to_datetime(data_final) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            except Exception as e:
                st.error(f'Erro ao converter datas: {e}')
                data_inicial = pd.to_datetime(datetime.date.today())
                data_final = pd.to_datetime(datetime.date.today()) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

            df_filtrado = df[
                (df['data'] >= data_inicial) &
                (df['data'] <= data_final) &
                (df['metodo'].isin(metodo_filtro)) &
                (df['status'].isin(status_filtro))
            ]

        # Relatórios para administrador
        if st.session_state['tipo_usuario'] == 'admin':
            st.subheader('Relatório Geral')
            colai1, colai2, colai3 = st.columns(3)
            colai1.metric('💰 Valor Total', f'R$ {df_filtrado["valor"].sum():.2f}' if not df_filtrado.empty else 'R$ 0,00')
            colai2.metric('Método Mais Usado', df_filtrado['metodo'].mode()[0] if not df_filtrado.empty else 'N/A')
            colai3.metric('Usuário com Mais Gastos', 
                        df_filtrado.groupby('usuario_login')['valor'].sum().idxmax() if not df_filtrado.empty else 'N/A')

            st.subheader('Análise por Usuário')
            usuarios = df['usuario_login'].unique()
            usuario_selecionado = st.selectbox('Selecione o Usuário', usuarios)
            df_usuario = df_filtrado[df_filtrado['usuario_login'] == usuario_selecionado]
            
            if not df_usuario.empty:
                st.write(f'**Resumo para {usuario_selecionado}**')
                colu1, colu2, colu3 = st.columns(3)
                colu1.metric('Total Gasto', f'R$ {df_usuario["valor"].sum():.2f}')
                colu2.metric('Método Mais Usado', df_usuario['metodo'].mode()[0] if not df_usuario.empty else 'N/A')
                colu3.metric('Transações', len(df_usuario))
                
                st.subheader('Transações do Usuário')
                st.dataframe(df_usuario.sort_values('data', ascending=False), use_container_width=True)
                
                fig_usuario = px.pie(df_usuario, names='metodo', values='valor', title=f'Distribuição por Método - {usuario_selecionado}')
                st.plotly_chart(fig_usuario, use_container_width=True)
            else:
                st.info(f'Nenhuma transação para {usuario_selecionado}.')

        # Relatórios para usuário normal
        st.subheader('Suas Transações')
        st.dataframe(df_filtrado.sort_values('data', ascending=False), use_container_width=True)

        st.subheader('Visualizações')
        tipo_grafico = st.selectbox('Escolha o tipo de gráfico', ['Barra', 'Pizza', 'Area'])
        if tipo_grafico == 'Barra':
            fig = px.bar(df_filtrado.groupby('metodo')['valor'].sum().reset_index(), x='metodo', y='valor', title='Valor por Método')
        elif tipo_grafico == 'Pizza':
            fig = px.pie(df_filtrado, names='metodo', values='valor', title='Distribuição por Método')
        else:
            df_filtrado_sorted = df_filtrado.sort_values("data").copy()
            fig = px.area(df_filtrado_sorted, x="data", y="valor", color="metodo", title="Pagamentos Acumulados por Método")
        st.plotly_chart(fig, use_container_width=True)

        buffer = io.BytesIO()
        df_filtrado.to_excel(buffer, index=False, engine='openpyxl')
        st.download_button('📥 Baixar Excel', data=buffer.getvalue(), file_name='transacoes.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    else:
        st.info('Nenhuma transação registrada.')