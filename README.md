# Sistema de Cadastro com FastAPI e Bootstrap 5

Este é um sistema de cadastro, login e recuperação de senha usando FastAPI, Bootstrap 5 e SQLite.

## Funcionalidades

- Cadastro de usuários com campos para email, WhatsApp, tipo de atividade, etc.
- Login com email e senha
- Recuperação de senha via email
- Dashboard para usuários logados
- Autenticação via JWT

## Requisitos

- Python 3.7+
- Dependências listadas em `requirements.txt`

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```
   python -m venv venv
   python create_admin.py
   ```
3. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
5. Configure as variáveis de ambiente no arquivo `.env`:
   - Edite o arquivo `.env` com suas configurações de email para recuperação de senha

## Execução

1. Execute o servidor:
   ```
   python main.py
   ```
2. Acesse a aplicação em `http://localhost:8000`

## Estrutura do Projeto

- `app/`: Pacote principal da aplicação
  - `main.py`: Ponto de entrada da aplicação FastAPI
  - `database/`: Configuração do banco de dados
  - `models/`: Modelos de dados
  - `routes/`: Rotas da aplicação
  - `templates/`: Templates HTML
  - `static/`: Arquivos estáticos (CSS, JS)
  - `utils/`: Utilitários (autenticação, email, etc.)

## Tecnologias Utilizadas

- FastAPI: Framework web rápido para APIs
- SQLAlchemy: ORM para interação com o banco de dados
- Jinja2: Mecanismo de templates
- Bootstrap 5: Framework CSS para interface responsiva
- SQLite: Banco de dados leve e de fácil configuração 