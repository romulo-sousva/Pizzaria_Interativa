# 🍕 Pizzaria Interativa - Sistema Desktop de Gestão de Pedidos

![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![GUI Framework](https://img.shields.io/badge/GUI-Tkinter-green)
![Database](https://img.shields.io/badge/Database-SQLite3-lightgrey?logo=sqlite)
![PMBOK Standards](https://img.shields.io/badge/Project_Management-PMBOK%C2%AE-orange)

Sistema Desktop interno para gerenciamento e automação de pedidos de pizzaria desenvolvido como projeto da disciplina de **Gerência de Projeto de Software** na **Universidade Federal do Maranhão (UFMA)** sob orientação do **Prof. MSc. Lucas Reis**.

---

## 👥 Equipe do Projeto

* **Racielle Freitas dos Santos** — Gerente de Projeto & Desenvolvedora Frontend GUI (Tkinter)
* **Rômulo de Sousa Vale** — Líder Técnico & Desenvolvedor Backend / Banco de Dados (SQLite)

---

## 🎯 Finalidade do Sistema

> **Atenção:** Este sistema **NÃO** é uma plataforma e-commerce ou aplicativo móvel para uso direto pelo cliente final. Trata-se de uma **ferramenta de uso interno (PDV / Caixa)** operada pelos funcionários e atendentes da pizzaria para lançamento de vendas, gestão de estoque por tamanho e controle financeiro.

---

## ✨ Funcionalidades Principais

* **Catálogo por Sabor Único:** Exibição limpa de sabores de pizzas e adicionais sem redundância visual.
* **Seleção Reativa de Tamanho (P, M, G):** Atualização dinâmica de preços na tabela conforme o tamanho selecionado no painel.
* **Estoque Discriminado por Tamanho:** Controle individual de saldos no SQLite para massas P, M e G.
* **Alerta Visual de Estoque Zerado (Mudança CR-01):** Produtos e tamanhos esgotados são destacados em **cor vermelha em destaque** (`⚠️ ESGOTADO`) na tabela.
* **Regra de Fidelidade (5% de Desconto):** Aplicação automática de 5% de desconto sobre o subtotal sempre que houver 2 ou mais pizzas no carrinho.
* **Painel de Reposição de Estoque:** Interface gráfica direta para o operador reabastecer o estoque de qualquer tamanho específico do catálogo.
* **Checkout e Resumo do Pedido:** Coleta de nome/endereço de entrega e registro do pedido com confirmação na tela e decremento imediato no banco de dados.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.12.3
* **Interface Gráfica (GUI):** Tkinter (`ttk`)
* **Banco de Dados:** SQLite3 (`pizzaria.db`)

---

## 🚀 Como Executar o Software

### 1. Pré-requisitos (Linux / Ubuntu / Debian)
No Linux, o módulo `tkinter` pode exigir a instalação do pacote do sistema operacional para o Python 3.12:

```bash
sudo apt update
sudo apt install python3.12-tk -y
```

### 2. Clonar o Repositório e Rodar o Código
```bash
# Clone o repositório
git clone https://github.com/seu-usuario/pizzaria-interativa.git

# Acesse a pasta do projeto
cd pizzaria-interativa

# Execute a aplicação
python3 main.py
```

> **Nota:** O banco de dados SQLite (`pizzaria.db`) é inicializado e populado automaticamente na primeira execução do script.

---

## 📋 Como Utilizar a Interface (Passo a Passo)

1. **Seleção de Produtos:**
   * Clique em qualquer sabor da tabela de catálogo.
   * Selecione o tamanho desejado (**P**, **M** ou **G**) no campo *Tamanho*. Observe que o preço na tabela e o saldo disponível atualizarão automaticamente.
   * Escolha a quantidade de venda e clique em **`🛒 Adicionar Item`**.

2. **Reposição de Estoque (Uso Operacional Interno):**
   * Selecione o produto desejado na tabela.
   * Escolha o tamanho (**P**, **M** ou **G**) no painel de *Reposição de Estoque*.
   * Digite a quantidade a ser adicionada e clique em **`➕ Reabastecer`**.

3. **Finalização do Pedido (Checkout):**
   * Verifique o carrinho de compras e certifique-se de que a mensagem do **Desconto de 5%** foi acionada (caso haja 2 ou mais pizzas).
   * Preencha obrigatoriamente o **Nome do Cliente** e o **Endereço de Entrega**.
   * Selecione a **Forma de Pagamento** (PIX, Cartão ou Boleto).
   * Clique em **`✅ FINALIZAR E CONFIRMAR PEDIDO`**.

---

## ⚠️ O Que Fazer e O Que NÃO Fazer

### ✅ O QUE FAZER:
* **Conferir o estoque antes da venda:** O próprio sistema avisará se a quantidade solicitada exceder o saldo disponível.
* **Aproveitar a seleção dinâmica:** Alterne entre P, M e G na caixa de seleção para consultar rapidamente os valores antes de adicionar ao carrinho.
* **Preencher todos os dados de checkout:** O endereço e nome do cliente são obrigatórios para liberar o botão de confirmação.

### ❌ O QUE NÃO FAZER:
* **NÃO apagar o arquivo `pizzaria.db` enquanto a aplicação estiver em execução.**
* **NÃO tentar instalar gateways reais de pagamento:** Este projeto opera com simulação acadêmica de pagamentos.
* **NÃO tentar acessar o sistema por navegadores web ou celulares:** O software foi arquitetado como aplicação desktop nativa.

---

## 📄 Documentação Acadêmica (PMBOK®)

Este repositório contém a suíte completa dos entregáveis de gestão do projeto conforme o PMBOK®:
* **Projeto 1:** TAP, Registro de Stakeholders, Ciclo de Vida Incremental/Ágil e EAP Inicial.
* **Projeto 2:** Declaração de Escopo Refinada, Dicionário da EAP, Cronograma e Linha de Base de Custos (76h / R$ 2.635,00).
* **Projeto 3:** Status Report, Registro de Mudanças (CR-01 e CR-02), Termo de Aceite Formal, Relatório Final e Registro de Lições Aprendidas.