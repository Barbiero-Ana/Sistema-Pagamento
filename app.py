import uuid
import hashlib
import random
import csv
import re
import time
import datetime


class Pagamento:
    def __init__(self, valor):
        self.id = str(uuid.uuid4())
        self.valor = valor
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
        with open('pagamentos.csv', mode='a', newline='') as arquivo:
            writer = csv.writer(arquivo)
            writer.writerow([
                self.id,
                self.__class__.__name__,
                self.valor,
                self.data.strftime('%d-%m-%Y %H:%M:%S'),
                self.status
            ])


class Cartao(Pagamento):
    def __init__(self, valor, numero, nome_titular, validade, cvv):
        super().__init__(valor)
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
            validade = datetime.datetime(2000 + ano, mes, 1)
            if validade < datetime.datetime.now():
                print('Cartão expirado.')
                return False
            return True
        except:
            print("Formato de validade inválido.")
            return False


class Paypal(Pagamento):
    def __init__(self, valor, email, senha):
        super().__init__(valor)
        self.email = email
        self.senha = self._hash(senha)

    def _hash(self, senha):
        return hashlib.sha256(senha.encode()).hexdigest()

    def validar(self):
        padrao = r"[^@]+@[^@]+\.[^@]+"
        if not re.match(padrao, self.email):
            print('Email inválido...')
            return False
        return True


class Transferencia(Pagamento):
    def __init__(self, valor, banco, conta_origem, conta_destino):
        super().__init__(valor)
        self.banco = banco
        self.conta_origem = conta_origem
        self.conta_destino = conta_destino

    def validar(self):
        if not (self.conta_origem.isdigit() and len(self.conta_origem) == 8):
            print('Conta de origem inválida.')
            return False
        if not (self.conta_destino.isdigit() and len(self.conta_destino) == 8):
            print('Conta de destino inválida.')
            return False
        return True


class Pix(Pagamento):
    def __init__(self, valor, chave):
        super().__init__(valor)
        self.chave = chave

    def validar(self):
        if '@' in self.chave:
            return True
        elif self.chave.isdigit() and len(self.chave) in [11, 14]:  # CPF ou CNPJ
            return True
        elif len(self.chave) >= 8:
            return True
        else:
            print('Chave Pix inválida.')
            return False


class Cripto(Pagamento):
    def __init__(self, valor, carteira, criptomoeda):
        super().__init__(valor)
        self.carteira = carteira
        self.criptomoeda = criptomoeda.lower()

    def validar(self):
        if not self.carteira or len(self.carteira) < 10:
            print('Endereço da carteira inválido.')
            return False
        if self.criptomoeda not in ['btc', 'eth', 'usdt']:
            print('Criptomoeda não suportada ou válida.')
            return False
        return True


def system(metodo: Pagamento):
    print(f'Processando pagamento de R$ {metodo.valor:.2f} via {metodo.__class__.__name__}...')
    if metodo.processar():
        print('Pagamento aprovado!')
    else:
        print('Pagamento recusado.')
    metodo.registrar()


pag1 = Cartao(300.00, '4111111111111111', 'Ana Barbiero', '12/38', '123')
pag2 = Paypal(150.00, 'ana@email.com', 'senha123')
pag3 = Transferencia(420.00, 'Banco XYZ', '12345678', '87654321')
pag4 = Pix(85.00, 'ana@email.com')
pag5 = Cripto(999.00, '0xABCDEF1234567890', 'BTC')

for pagamento in [pag1, pag2, pag3, pag4, pag5]:
    system(pagamento)
