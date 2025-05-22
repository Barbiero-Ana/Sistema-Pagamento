import uuid
import random
import time
import datetime
from database import registrar_transacao

class Pagamento:
    def __init__(self, valor, usuario_login):
        self.id = str(uuid.uuid4())
        self.valor = valor
        self.usuario_login = usuario_login
        self.data = datetime.datetime.now()
        self.status = 'Pendente'

    def validar(self):
        raise NotImplementedError

    def processar(self):
        if not self.validar():
            self.status = 'Recusado'
            return False

        time.sleep(2)
        sucesso = random.choices([True, False], weights=[80, 20])[0]
        self.status = 'Aprovado' if sucesso else 'Recusado'
        return sucesso

    def registrar(self):
        registrar_transacao(
            id_transacao=self.id,
            usuario_login=self.usuario_login,
            metodo=self.__class__.__name__,
            valor=self.valor,
            data=self.data.strftime('%Y-%m-%d %H:%M:%S'),
            status=self.status
        )

class Cartao(Pagamento):
    def __init__(self, valor, usuario_login, numero, nome_titular, validade, cvv):
        super().__init__(valor, usuario_login)
        if len(cvv) not in [3, 4]:
            raise ValueError("CVV inválido.")
        self.numero = self._mascarar(numero)
        self.nome_titular = nome_titular
        self.validade = validade
        self.cvv = self._mascarar(cvv)

    def _mascarar(self, dado):
        return '*' * (len(dado) - 4) + dado[-4:]

    def validar(self):
        try:
            mes, ano = map(int, self.validade.split('/'))
            ano = ano if ano > 999 else 2000 + ano
            ultimo_dia = (datetime.datetime(ano, mes + 1, 1) - datetime.timedelta(days=1))
            if ultimo_dia < datetime.datetime.now():
                raise ValueError("Cartão expirado.")
            return True
        except ValueError as e:
            raise ValueError(f"Erro na validação do cartão: {str(e)}")

class Paypal(Pagamento):
    def __init__(self, valor, usuario_login, email, senha):
        super().__init__(valor, usuario_login)
        self.email = email
        self.senha = senha 

    def validar(self):
        import re
        padrao = r"[^@]+@[^@]+\.[^@]+"
        if not re.match(padrao, self.email):
            raise ValueError("Email inválido.")
        return True

class Transferencia(Pagamento):
    def __init__(self, valor, usuario_login, banco, conta_origem, conta_destino):
        super().__init__(valor, usuario_login)
        self.banco = banco
        self.conta_origem = conta_origem
        self.conta_destino = conta_destino

    def validar(self):
        if not (self.conta_origem.isdigit() and len(self.conta_origem) == 8):
            raise ValueError("Conta de origem inválida.")
        if not (self.conta_destino.isdigit() and len(self.conta_destino) == 8):
            raise ValueError("Conta de destino inválida.")
        return True

class Pix(Pagamento):
    def __init__(self, valor, usuario_login, chave):
        super().__init__(valor, usuario_login)
        self.chave = chave

    def validar(self):
        import re
        if '@' in self.chave:
            padrao = r"[^@]+@[^@]+\.[^@]+"
            if not re.match(padrao, self.chave):
                raise ValueError("Chave Pix (email) inválida.")
            return True
        elif self.chave.isdigit() and len(self.chave) in [11, 14]:
            return True
        elif len(self.chave) >= 8:
            return True
        else:
            raise ValueError("Chave Pix inválida.")

class Cripto(Pagamento):
    def __init__(self, valor, usuario_login, carteira, criptomoeda):
        super().__init__(valor, usuario_login)
        self.carteira = carteira
        self.criptomoeda = criptomoeda.lower()

    def validar(self):
        if not self.carteira or len(self.carteira) < 10:
            raise ValueError("Endereço da carteira inválido.")
        if self.criptomoeda not in ['btc', 'eth', 'usdt']:
            raise ValueError("Criptomoeda não suportada ou válida.")
        return True

def system(metodo: Pagamento):
    print(f'Processando pagamento de R$ {metodo.valor:.2f} via {metodo.__class__.__name__}...')
    if metodo.processar():
        print('Pagamento aprovado!')
    else:
        print('Pagamento recusado.')
    metodo.registrar()