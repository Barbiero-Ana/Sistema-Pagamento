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
from database import init_db, cadastrar_usuario, verificar_login, verificar_senha_mestra, listar_administradores, redefinir_senha_admin, carregar_transacoes, contar_usuarios, valor_total_movimentado, metodo_mais_utilizado, metodo_mais_aprovado, metodo_mais_negado, metodo_menos_utilizado
from pagamentos import Cartao, Paypal, Transferencia, Pix, Cripto, system
import sqlite3


st.set_page_config(page_title='Sistema de Pagamentos', layout='wide')
logging.basicConfig(filename='logs_erros.log', level=logging.ERROR)
load_dotenv()
gestormail = os.environ.get('gestor_mail')
gestorpass = os.environ.get('gestor_password')

init_db()

# envio de emails
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

# processar o pagamento
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

# sessoes (usuarios)
if 'usuario' not in st.session_state:
    st.session_state['usuario'] = None
    st.session_state['tipo_usuario'] = None
    st.session_state['opcao_admin'] = 'Cadastrar Usuário'

# login
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
else:
    st.title('Sistema de Processamento de Pagamentos')
    st.write(f'Usuário: {st.session_state["usuario"]} ({st.session_state["tipo_usuario"]})')

    st.sidebar.header('Navegação')
    if st.sidebar.button('Sair', key='logout_button'):
        if st.session_state.get('confirm_logout', False):
            logging.info(f'Usuário {st.session_state["usuario"]} realizou logout.')
            st.session_state['usuario'] = None
            st.session_state['tipo_usuario'] = None
            st.session_state['confirm_logout'] = False
            st.success('Logout realizado com sucesso!')
            st.rerun()
        else:
            st.session_state['confirm_logout'] = True
            st.sidebar.warning('Clique novamente para confirmar o logout.')

    # adm
    if st.session_state['tipo_usuario'] == 'admin':
        st.sidebar.header('Gerenciamento')
        st.session_state['opcao_admin'] = st.sidebar.selectbox('Selecione a Ação', ['Cadastrar Usuário', 'Dashboard Geral'], key='admin_action')

        if st.session_state['opcao_admin'] == 'Cadastrar Usuário':
            st.sidebar.subheader('Cadastrar Novo Usuário')
            with st.sidebar.form('cadastro_form'):
                novo_login = st.text_input('Novo Login')
                nova_senha = st.text_input('Nova Senha', type='password')
                tipo_usuario_cadastro = st.selectbox('Tipo de Usuário', ['normal', 'admin'])
                senha_mestra = st.text_input('Senha Mestra (necessária para administradores)', type='password') if tipo_usuario_cadastro == 'admin' else None
                cadastrar = st.form_submit_button('Cadastrar')
                
                if cadastrar:
                    if novo_login and nova_senha:
                        if tipo_usuario_cadastro == 'admin' and not verificar_senha_mestra(senha_mestra):
                            st.error('Senha mestra inválida.')
                            logging.error(f'Tentativa de cadastro de administrador com senha mestra inválida por {st.session_state["usuario"]}')
                        else:
                            if cadastrar_usuario(novo_login, nova_senha, tipo_usuario_cadastro):
                                st.success(f'Usuário {novo_login} cadastrado como {tipo_usuario_cadastro}!')
                            else:
                                st.error('Login já existe.')
                    else:
                        st.warning('Preencha todos os campos.')

        elif st.session_state['opcao_admin'] == 'Dashboard Geral':
            st.sidebar.subheader('Filtros do Dashboard')
            with st.sidebar.form('filtro_dashboard'):
                data_inicial = st.date_input('Data Inicial', value=datetime.date.today() - datetime.timedelta(days=30))
                data_final = st.date_input('Data Final', value=datetime.date.today())
                metodos = ['Cartão', 'Paypal', 'Transferência', 'Pix', 'Cripto']
                metodo_filtro = st.multiselect('Métodos', metodos, default=metodos)
                status_filtro = st.multiselect('Status', ['Aprovado', 'Recusado'], default=['Aprovado', 'Recusado'])
                filtrar = st.form_submit_button('Aplicar Filtros')
                
                if filtrar:
                    st.session_state['filtros'] = {
                        'data_inicial': data_inicial,
                        'data_final': data_final,
                        'metodo_filtro': metodo_filtro,
                        'status_filtro': status_filtro
                    }

    # adm
    if st.session_state['tipo_usuario'] == 'admin':
        st.header('Resumo Geral do Sistema')
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric('Usuários Cadastrados', contar_usuarios())
        col2.metric('Total Movimentado', f'R$ {valor_total_movimentado():.2f}')
        col3.metric('Método Mais Utilizado', metodo_mais_utilizado())
        col4.metric('Método Mais Aprovado', metodo_mais_aprovado())
        col5.metric('Método Mais Negado', metodo_mais_negado())
        st.metric('Método Menos Utilizado', metodo_menos_utilizado())

    # adm
    if st.session_state['tipo_usuario'] == 'admin' and st.session_state['opcao_admin'] == 'Dashboard Geral':
        st.header('Dashboard Geral')

        conn = sqlite3.connect('pagamentos.db')
        cursor = conn.cursor()
        cursor.execute('SELECT login FROM usuarios')
        usuarios = ['Todos os Usuários'] + [row[0] for row in cursor.fetchall()]
        conn.close()
        
        usuario_selecionado = st.selectbox('Selecione o Usuário', usuarios, key='usuario_dashboard')
        

        df = carregar_transacoes(None if usuario_selecionado == 'Todos os Usuários' else usuario_selecionado)
        
        if not df.empty:

            filtros = st.session_state.get('filtros', {})
            data_inicial = filtros.get('data_inicial', df['data'].min().date())
            data_final = filtros.get('data_final', df['data'].max().date())
            metodo_filtro = filtros.get('metodo_filtro', df['metodo'].unique())
            status_filtro = filtros.get('status_filtro', df['status'].unique())
            
            try:
                data_inicial = pd.to_datetime(data_inicial)
                data_final = pd.to_datetime(data_final) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            except Exception as e:
                st.error(f'Erro ao converter datas: {e}')
                data_inicial = pd.to_datetime(df['data'].min())
                data_final = pd.to_datetime(df['data'].max())
            
            df_filtrado = df[
                (df['data'] >= data_inicial) &
                (df['data'] <= data_final) &
                (df['metodo'].isin(metodo_filtro)) &
                (df['status'].isin(status_filtro))
            ]
            
            if not df_filtrado.empty:
                st.subheader('Transações Filtradas')
                st.dataframe(df_filtrado.sort_values('data', ascending=False), use_container_width=True)
                
                if usuario_selecionado != 'Todos os Usuários':
                    st.subheader(f'Análise do Usuário: {usuario_selecionado}')
                    colu1, colu2, colu3 = st.columns(3)
                    colu1.metric('Total Gasto', f'R$ {df_filtrado["valor"].sum():.2f}')
                    colu2.metric('Método Mais Usado', df_filtrado['metodo'].mode()[0] if not df_filtrado['metodo'].empty else 'N/A')
                    colu3.metric('Transações', len(df_filtrado))
                    
                    fig_usuario = px.pie(df_filtrado, names='metodo', values='valor', title=f'Distribuição por Método - {usuario_selecionado}')
                    st.plotly_chart(fig_usuario, use_container_width=True)
                
                st.subheader('Visualizações Gerais')
                tipo_grafico = st.selectbox('Escolha o Tipo de Gráfico', ['Barra', 'Pizza', 'Área', 'Linha'])
                if tipo_grafico == 'Barra':
                    fig = px.bar(df_filtrado.groupby('metodo')['valor'].sum().reset_index(), x='metodo', y='valor', title='Valor Total por Método')
                elif tipo_grafico == 'Pizza':
                    fig = px.pie(df_filtrado, names='metodo', values='valor', title='Distribuição por Método')
                elif tipo_grafico == 'Área':
                    df_filtrado_sorted = df_filtrado.sort_values('data').copy()
                    fig = px.area(df_filtrado_sorted, x='data', y='valor', color='metodo', title='Pagamentos Acumulados por Método')
                elif tipo_grafico == 'Linha':
                    df_filtrado_sorted = df_filtrado.sort_values('data').copy()
                    fig = px.line(df_filtrado_sorted, x='data', y='valor', color='metodo', title='Pagamentos por Método ao Longo do Tempo')
                st.plotly_chart(fig, use_container_width=True)
                
                buffer = io.BytesIO()
                df_filtrado.to_excel(buffer, index=False, engine='openpyxl')
                st.download_button('📥 Baixar Excel', data=buffer.getvalue(), file_name='transacoes.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            else:
                st.info('Nenhuma transação corresponde aos filtros selecionados.')
        else:
            st.info('Nenhuma transação registrada.')

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


        st.header('Suas Transações')
        df = carregar_transacoes(st.session_state['usuario'])
        
        if not df.empty:
            with st.expander('Filtro'):
                colf1, colf2, colf3 = st.columns(3)
                default_data_inicial = pd.to_datetime(df['data'].min()).date()
                default_data_final = pd.to_datetime(df['data'].max()).date()
                
                data_inicial = colf1.date_input('Data Inicial', value=default_data_inicial)
                data_final = colf2.date_input('Data Final', value=default_data_final)
                metodo_filtro = colf3.multiselect('Métodos', df['metodo'].unique(), default=df['metodo'].unique())
                status_filtro = colf3.multiselect('Status', df['status'].unique(), default=df['status'].unique())
                
                try:
                    data_inicial = pd.to_datetime(data_inicial)
                    data_final = pd.to_datetime(data_final) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                except Exception as e:
                    st.error(f'Erro ao converter datas: {e}')
                    data_inicial = pd.to_datetime(default_data_inicial)
                    data_final = pd.to_datetime(default_data_final)
                
                df_filtrado = df[
                    (df['data'] >= data_inicial) &
                    (df['data'] <= data_final) &
                    (df['metodo'].isin(metodo_filtro)) &
                    (df['status'].isin(status_filtro))
                ]
                
                st.dataframe(df_filtrado.sort_values('data', ascending=False), use_container_width=True)
                
                st.subheader('Visualizações')
                tipo_grafico = st.selectbox('Escolha o Tipo de Gráfico', ['Barra', 'Pizza', 'Área', 'Linha'])
                if tipo_grafico == 'Barra':
                    fig = px.bar(df_filtrado.groupby('metodo')['valor'].sum().reset_index(), x='metodo', y='valor', title='Valor por Método')
                elif tipo_grafico == 'Pizza':
                    fig = px.pie(df_filtrado, names='metodo', values='valor', title='Distribuição por Método')
                elif tipo_grafico == 'Área':
                    df_filtrado_sorted = df_filtrado.sort_values('data').copy()
                    fig = px.area(df_filtrado_sorted, x='data', y='valor', color='metodo', title='Pagamentos Acumulados por Método')
                elif tipo_grafico == 'Linha':
                    df_filtrado_sorted = df_filtrado.sort_values('data').copy()
                    fig = px.line(df_filtrado_sorted, x='data', y='valor', color='metodo', title='Pagamentos por Método ao Longo do Tempo')
                st.plotly_chart(fig, use_container_width=True)
                
                buffer = io.BytesIO()
                df_filtrado.to_excel(buffer, index=False, engine='openpyxl')
                st.download_button('📥 Baixar Excel', data=buffer.getvalue(), file_name='transacoes.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            st.info('Nenhuma transação registrada.')