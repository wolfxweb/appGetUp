import sqlite3
import os
import shutil
import datetime

def migrate_database():
    print("Iniciando migracao do banco de dados...")

    db_path = os.path.join('app', 'database', 'app.db')
    print(f"Usando banco de dados: {db_path}")

    if not os.path.exists(db_path):
        print("Banco de dados nao encontrado. Sera criado pelo SQLAlchemy.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # --- basic_data ---
        cursor.execute("PRAGMA table_info(basic_data)")
        columns = [column[1] for column in cursor.fetchall()]

        for column_name, column_type in {
            'other_fixed_costs': 'FLOAT',
            'ideal_service_profit_margin': 'FLOAT'
        }.items():
            if column_name not in columns:
                print(f"Adicionando coluna {column_name} em basic_data...")
                cursor.execute(f"ALTER TABLE basic_data ADD COLUMN {column_name} {column_type}")

        # --- users ---
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]

        for col_name, col_type in [
            ("ideal_profit_margin",       "REAL"),
            ("service_capacity",          "REAL"),
            ("ja_acessou",                "INTEGER"),
            ("onboarding_completed",      "INTEGER"),
            ("production_hours",          "REAL"),
            ("estimated_loss_percentage", "REAL"),
            ("has_product_sheet",         "TEXT"),
        ]:
            if col_name not in user_columns:
                print(f"Adicionando coluna {col_name} em users...")
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")

        conn.commit()

        # --- analise_mensal ---
        print("Verificando tabela analise_mensal...")
        cursor.execute("PRAGMA table_info(analise_mensal)")
        analise_columns = [col[1] for col in cursor.fetchall()]

        if "competencia_mes" in analise_columns:
            print("Estrutura antiga detectada. Recriando tabela analise_mensal...")
            cursor.execute("DROP TABLE analise_mensal")
            analise_columns = []

        if not analise_columns:
            print("Criando tabela analise_mensal...")
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
                    margem_contribuicao_por_cliente FLOAT,
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
                "margem_contribuicao_por_cliente": "FLOAT",
                "ponto_equilibrio": "FLOAT",
                "margem_seguranca": "FLOAT",
                "custo_total": "FLOAT",
                "resultado": "FLOAT",
                "percentual_margem": "FLOAT",
                "corresponde_caixa": "BOOLEAN",
            }
            for col, col_type in cols_to_add.items():
                if col not in analise_columns:
                    print(f"Adicionando coluna {col} em analise_mensal...")
                    cursor.execute(f"ALTER TABLE analise_mensal ADD COLUMN {col} {col_type}")

        # --- custo_fixo ---
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
        print("Migracao concluida com sucesso!")

    except Exception as e:
        print(f"Erro durante a migracao: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
