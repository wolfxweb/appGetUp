from app.database.db import engine
import sqlite3
import os

def migrate_database():
    print("Iniciando migração para adicionar coluna percentual_faturamento...")
    
    # Caminho correto do banco de dados
    db_path = os.path.join('app', 'database', 'app.db')
    print(f"Usando banco de dados: {db_path}")
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna existe antes de adicionar
        cursor.execute("PRAGMA table_info(produtos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar nova coluna se não existir
        if 'percentual_faturamento' not in columns:
            print("Adicionando coluna percentual_faturamento...")
            cursor.execute("ALTER TABLE produtos ADD COLUMN percentual_faturamento FLOAT")
            print("Coluna percentual_faturamento adicionada com sucesso!")
        else:
            print("Coluna percentual_faturamento já existe.")
        
        # Commit das alterações
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()

