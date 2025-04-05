import os
import sys
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

def run_migration():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter a URL do banco de dados do arquivo .env
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Erro: DATABASE_URL não encontrada no arquivo .env")
        sys.exit(1)
    
    # Criar configuração do Alembic
    alembic_cfg = Config()
    alembic_cfg.set_main_option("script_location", "migrations")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    
    # Executar a migração
    try:
        command.upgrade(alembic_cfg, "head")
        print("Migração executada com sucesso!")
    except Exception as e:
        print(f"Erro ao executar a migração: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration() 