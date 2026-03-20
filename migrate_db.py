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
                print(f"Adicionando coluna {column_name} em basic_data...")
                cursor.execute(f"ALTER TABLE basic_data ADD COLUMN {column_name} {column_type}")
        
        # Migrar tabela users - adicionar campos de onboarding
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        user_new_columns = {
            'ideal_profit_margin': 'REAL',
            'service_capacity': 'REAL',
            'ja_acessou': 'INTEGER',
            'onboarding_completed': 'INTEGER'
        }
        for column_name, column_type in user_new_columns.items():
            if column_name not in user_columns:
                print(f"Adicionando coluna {column_name} em users...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {column_name} {column_type}")
        
        # Migrar colunas existentes para REAL (ideal_profit_margin, service_capacity)
        # SQLite 3.35+ suporta DROP COLUMN e RENAME COLUMN
        user_col_info = {col[1]: col[2].upper() for col in cursor.execute("PRAGMA table_info(users)").fetchall()}
        for col_name in ('ideal_profit_margin', 'service_capacity'):
            if col_name in user_col_info and user_col_info[col_name] not in ('REAL', 'FLOAT', 'DOUBLE'):
                try:
                    print(f"Migrando coluna {col_name} para REAL...")
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name}_new REAL")
                    cursor.execute(f"UPDATE users SET {col_name}_new = CAST({col_name} AS REAL)")
                    cursor.execute(f"ALTER TABLE users DROP COLUMN {col_name}")
                    cursor.execute(f"ALTER TABLE users RENAME COLUMN {col_name}_new TO {col_name}")
                except Exception as e:
                    print(f"Aviso: não foi possível migrar {col_name} para REAL: {e}")
        
        # Migrar basic_data.service_capacity para REAL se for TEXT
        cursor.execute("PRAGMA table_info(basic_data)")
        bd_col_info = {col[1]: col[2].upper() for col in cursor.fetchall()}
        if 'service_capacity' in bd_col_info and bd_col_info['service_capacity'] not in ('REAL', 'FLOAT', 'DOUBLE'):
            try:
                print("Migrando coluna service_capacity em basic_data para REAL...")
                cursor.execute("ALTER TABLE basic_data ADD COLUMN service_capacity_new REAL")
                cursor.execute("UPDATE basic_data SET service_capacity_new = CAST(service_capacity AS REAL)")
                cursor.execute("ALTER TABLE basic_data DROP COLUMN service_capacity")
                cursor.execute("ALTER TABLE basic_data RENAME COLUMN service_capacity_new TO service_capacity")
            except Exception as e:
                print(f"Aviso: não foi possível migrar basic_data.service_capacity para REAL: {e}")
        
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