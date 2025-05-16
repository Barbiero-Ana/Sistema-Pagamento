# Sistema de pagamentos

Você foi contratado para desenvolver um sistema de pagamentos para uma fintech. O objetivo
é criar uma solução que gerencie diferentes métodos de pagamento (cartão de crédito, PayPal,
transferência bancária), garantindo segurança, rastreabilidade das transações e flexibilidade
para adicionar novos métodos no futuro. O sistema deve seguir os princípios de Programação
Orientada a Objetos (POO) e simular comportamentos reais, como validações, processamento
e registro de transações.



Requisitos Funcionais
1. Suporte a Múltiplos Métodos de Pagamento
○ O sistema deve permitir processar pagamentos via:
    ■ Cartão de Crédito: Coletar número do cartão, nome do titular, data de
    validade e CVV.
    ■ PayPal: Coletar e-mail e senha (autenticação simulada).
    ■ Transferência Bancária: Coletar código do banco, conta de origem e
    conta de destino.

○ Cada método deve ter regras específicas de processamento (ex: comunicação
com gateway de pagamento fictício).


2. Fluxo de Processamento
○ Todas as transações devem ter:
    ■ Valor monetário.
    ■ Data/hora do pagamento.
    ■ Status (Pendente, Aprovado, Recusado).

○ Simular uma taxa de sucesso/falha (ex: 80% de aprovação, 20% de recusa
aleatória para testes).


3. Validações Obrigatórias
○ Cartão de Crédito:
    ■ CVV deve ter exatamente 3 dígitos.
    ■ Data de validade não pode estar expirada.
○ PayPal:
    ■ E-mail deve seguir formato válido (ex: usuario@dominio.com).
○ Transferência Bancária:
    ■ Contas devem ter números válidos (ex: 8 dígitos).
○ Caso alguma validação falhe, o pagamento deve ser recusado com mensagem
clara de erro.


4. Registro e Rastreamento
○
Todas as transações devem ser registradas em um histórico, incluindo:
■ ID único da transação.
■ Método utilizado.
■ Valor, data e status.

○ Gerar um arquivo de log (em csv ou em sqlite3) com detalhes das operações.


5. DESAFIO: Segurança de Dados
○ Dados sensíveis (CVV, senha do PayPal, número do cartão) devem ser
armazenados e exibidos de forma mascarada ou protegida.

○ Dica: pesquise bibliotecas para mascaramento e hash


6. Extensibilidade
○ O sistema deve ser projetado para facilitar a adição de novos métodos de
pagamento (ex: pix, criptomoedas, etc) sem alterar o núcleo existente.
Dicas

● Utilize classes para representar métodos de pagamento e o processador de transações. 
● Pode-se simular "atrasos" no processamento para dar realismo (ex: time.sleep(2)).
● Chame o professor sempre que tiver dúvidas.

Desafio

● Frontend: Construa uma interface interativa e amigável usando Streamlit, integrando-a
ao sistema de pagamentos para simular uma experiência real de usuário.

● Banco de Dados: Projete um modelo de dados robusto com SQLite3, garantindo
armazenamento eficiente de transações, consultas complexas e histórico rastreável.

● Análise de Dados: Desenvolva um dashboard completo (com bibliotecas como Plotly
ou Seaborn) para visualizar métricas financeiras, como volume de transações e taxas
de sucesso.

● Backend: Implemente integrações com outros serviços, como notificações por
e-mail, relatórios automatizados ou bot do telegram.