import sqlite3
import os

def add_is_current_column():
    # Caminho para o banco de dados
    db_path = os.path.join('app', 'database', 'app.db')
    
    try:
        # Conecta ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se a coluna já existe
        cursor.execute("PRAGMA table_info(basic_data)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_current' in columns:
            print("A coluna 'is_current' já existe na tabela 'basic_data'")
            return
        
        # Adiciona a nova coluna
        cursor.execute("ALTER TABLE basic_data ADD COLUMN is_current BOOLEAN")
        
        # Commit das alterações
        conn.commit()
        print("Coluna 'is_current' adicionada com sucesso!")
        
    except sqlite3.Error as e:
        print(f"Erro SQLite: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_is_current_column()
