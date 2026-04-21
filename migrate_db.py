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
        
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        for col_name, col_type in (
            ("ideal_profit_margin", "REAL"),
            ("service_capacity", "REAL"),
            ("ja_acessou", "INTEGER"),
            ("onboarding_completed", "INTEGER"),
        ):
            if col_name not in user_columns:
                print(f"Adicionando coluna {col_name} em users...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        
        # Commit das alterações
        conn.commit()
        
        # Verificar e adicionar colunas na analise_mensal
        print("Verificando colunas na tabela analise_mensal...")
        cursor.execute("PRAGMA table_info(analise_mensal)")
        analise_columns = [col[1] for col in cursor.fetchall()]
        
        # Se a tabela tem colunas antigas como 'competencia_mes', precisamos recriar
        if "competencia_mes" in analise_columns:
            print("Detectada estrutura antiga (competencia_mes). Recriando tabela analise_mensal...")
            cursor.execute("DROP TABLE analise_mensal")
            analise_columns = []
        
        if not analise_columns:
            # Tabela não existe, criar do zero
            print("Criando tabela analise_mensal do zero...")
            cursor.execute("""
                CREATE TABLE analise_mensal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mes INTEGER NOT NULL,
                    ano INTEGER NOT NULL,
                    capacidade_atendimento FLOAT,
                    faturamento FLOAT,
                    quant_clientes INTEGER,
                    gastos_vendas FLOAT,
                    custo_mercadorias FLOAT,
                    custo_fixo_total FLOAT,
                    ticket_medio FLOAT,
                    margem_bruta FLOAT,
                    ponto_equilibrio FLOAT,
                    margem_seguranca FLOAT,
                    custo_total FLOAT,
                    resultado FLOAT,
                    percentual_margem FLOAT,
                    corresponde_caixa BOOLEAN,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    UNIQUE (user_id, mes, ano)
                )
            """)
        else:
            # Tabela existe, adicionar colunas faltantes
            cols_to_add = {
                "mes": "INTEGER NOT NULL DEFAULT 1",
                "ano": "INTEGER NOT NULL DEFAULT 2024",
                "capacidade_atendimento": "FLOAT",
                "faturamento": "FLOAT",
                "quant_clientes": "INTEGER",
                "gastos_vendas": "FLOAT",
                "custo_mercadorias": "FLOAT",
                "custo_fixo_total": "FLOAT",
                "ticket_medio": "FLOAT",
                "margem_bruta": "FLOAT",
                "ponto_equilibrio": "FLOAT",
                "margem_seguranca": "FLOAT",
                "custo_total": "FLOAT",
                "resultado": "FLOAT",
                "percentual_margem": "FLOAT",
                "corresponde_caixa": "BOOLEAN"
            }
            for col, col_type in cols_to_add.items():
                if col not in analise_columns:
                    print(f"Adicionando coluna {col} em analise_mensal...")
                    cursor.execute(f"ALTER TABLE analise_mensal ADD COLUMN {col} {col_type}")

        # Tabela custo_fixo
        print("Verificando tabela custo_fixo...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custo_fixo (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                nome VARCHAR(255) NOT NULL,
                valor FLOAT NOT NULL,
                categoria VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        """)
        
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a migração: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database() 