from app.database.db import engine
import sqlite3
import os

def migrate_database():
    print("Iniciando migração do banco de dados...")
    
    # Caminho correto do banco de dados
    db_path = os.path.join('app', 'database', 'app.db')
    print(f"Usando banco de dados: {db_path}")
    
    # Conectar ao banco de dados
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Verificar se as colunas existem antes de adicionar
        cursor.execute("PRAGMA table_info(basic_data)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Adicionar novas colunas se não existirem
        new_columns = {
            'other_fixed_costs': 'FLOAT',
            'ideal_service_profit_margin': 'FLOAT'
        }
        
        for column_name, column_type in new_columns.items():
            if column_name not in columns:
                print(f"Adicionando coluna {column_name}...")
                cursor.execute(f"ALTER TABLE basic_data ADD COLUMN {column_name} {column_type}")
        
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