# implementar o sistema de login e decodificiacao do sistema
# o codigo preciso codificar e durante o login decodificar para anlisar os dados com o do banco e validar
# criar um db para o sistema

import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
conexao = sqlite3.connect('Usuarios.db')
cursor = conexao.cursor()

cursor.execute("""

CREATE TABLE IF NO EXISTS Usuarios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Nome TEXT NOT NULL,
            Email TEXT UNIQUE NOT NULL,
            Idade INTEGER, 
            Senha TEXT NOT NULL
            )
""")