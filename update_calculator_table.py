import sqlite3
import os
from dotenv import load_dotenv

def update_calculator_table():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter o caminho do banco de dados
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Erro: DATABASE_URL não encontrada no arquivo .env")
        return
    
    # Extrair o caminho do banco de dados da URL
    db_path = database_url.replace("sqlite:///", "")
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se as colunas já existem
        cursor.execute("PRAGMA table_info(calculator)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar a coluna month se não existir
        if "month" not in columns:
            print("Adicionando coluna month...")
            cursor.execute("ALTER TABLE calculator ADD COLUMN month INTEGER")
        
        # Adicionar a coluna year se não existir
        if "year" not in columns:
            print("Adicionando coluna year...")
            cursor.execute("ALTER TABLE calculator ADD COLUMN year INTEGER")
        
        # Atualizar registros existentes com valores padrão
        cursor.execute("UPDATE calculator SET month = 1, year = 2024 WHERE month IS NULL OR year IS NULL")
        
        # Commit das alterações
        conn.commit()
        print("Tabela calculator atualizada com sucesso!")
        
    except Exception as e:
        print(f"Erro ao atualizar a tabela: {e}")
        conn.rollback()
    
    finally:
        # Fechar a conexão
        conn.close()

if __name__ == "__main__":
    update_calculator_table() 