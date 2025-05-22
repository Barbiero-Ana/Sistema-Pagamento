import sqlite3
import bcrypt
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()
SENHA_MESTRA = os.environ.get('adm_password', 'senha_mestra_padrao')

def init_db():
    conn = sqlite3.connect('pagamentos.db')
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            login TEXT PRIMARY KEY,
            senha TEXT NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('normal', 'admin'))
        )
    ''')
    
    # Tabela de transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            id TEXT PRIMARY KEY,
            usuario_login TEXT,
            metodo TEXT,
            valor REAL,
            data TEXT,
            status TEXT,
            FOREIGN KEY (usuario_login) REFERENCES usuarios (login)
        )
    ''')
    
    # Criar ou atualizar administrador padrão
    admin_login = 'Adm@2025'
    admin_senha = bcrypt.hashpw('administrador@pgt'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    cursor.execute('''
        INSERT OR REPLACE INTO usuarios (login, senha, tipo)
        VALUES (?, ?, ?)
    ''', (admin_login, admin_senha, 'admin'))
    
    conn.commit()
    conn.close()

def cadastrar_usuario(login, senha, tipo='normal'):
    conn = sqlite3.connect('pagamentos.db')
    cursor = conn.cursor()
    
    try:
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor.execute('''
            INSERT INTO usuarios (login, senha, tipo)
            VALUES (?, ?, ?)
        ''', (login, senha_hash, tipo))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Login já existe
    finally:
        conn.close()

def verificar_login(login, senha):
    conn = sqlite3.connect('pagamentos.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT senha, tipo FROM usuarios WHERE login = ?', (login,))
    result = cursor.fetchone()
    conn.close()
    
    if result:
        senha_hash, tipo = result
        if bcrypt.checkpw(senha.encode('utf-8'), senha_hash.encode('utf-8')):
            return tipo
    return None

def verificar_senha_mestra(senha):
    return bcrypt.checkpw(senha.encode('utf-8'), bcrypt.hashpw(SENHA_MESTRA.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'))

def redefinir_senha_admin(login, nova_senha, senha_mestra):
    if not verificar_senha_mestra(senha_mestra):
        return False
    conn = sqlite3.connect('pagamentos.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT tipo FROM usuarios WHERE login = ?', (login,))
        result = cursor.fetchone()
        if result and result[0] == 'admin':
            nova_senha_hash = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cursor.execute('''
                UPDATE usuarios SET senha = ? WHERE login = ?
            ''', (nova_senha_hash, login))
            conn.commit()
            return True
        return False  # Usuário não é admin ou não existe
    finally:
        conn.close()

def listar_administradores():
    conn = sqlite3.connect('pagamentos.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT login FROM usuarios WHERE tipo = "admin"')
    admins = [row[0] for row in cursor.fetchall()]
    conn.close()
    return admins

def registrar_transacao(id_transacao, usuario_login, metodo, valor, data, status):
    conn = sqlite3.connect('pagamentos.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transacoes (id, usuario_login, metodo, valor, data, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (id_transacao, usuario_login, metodo, valor, data, status))
    
    conn.commit()
    conn.close()

def carregar_transacoes(usuario_login=None):
    conn = sqlite3.connect('pagamentos.db')
    query = '''
        SELECT id, usuario_login, metodo, valor, data, status
        FROM transacoes
    '''
    params = []
    if usuario_login:
        query += ' WHERE usuario_login = ?'
        params = (usuario_login,)
    
    df = pd.read_sql_query(query, conn, params=params, parse_dates=['data'])
    conn.close()
    return df