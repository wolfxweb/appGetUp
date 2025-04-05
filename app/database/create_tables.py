from sqlalchemy import inspect
from app.database.db import engine, Base
from app.models.user import User
from app.models.basic_data import BasicData
from app.models.calculator import Calculator

def create_tables_if_not_exist():
    inspector = inspect(engine)
    
    # Verificar se a tabela calculator existe
    if "calculator" not in inspector.get_table_names():
        print("Criando tabela calculator...")
        Calculator.__table__.create(engine)
        print("Tabela calculator criada com sucesso!")
    else:
        print("Tabela calculator já existe.")
    
    # Verificar se a tabela users existe
    if "users" not in inspector.get_table_names():
        print("Criando tabela users...")
        User.__table__.create(engine)
        print("Tabela users criada com sucesso!")
    else:
        print("Tabela users já existe.")
    
    # Verificar se a tabela basic_data existe
    if "basic_data" not in inspector.get_table_names():
        print("Criando tabela basic_data...")
        BasicData.__table__.create(engine)
        print("Tabela basic_data criada com sucesso!")
    else:
        print("Tabela basic_data já existe.")

if __name__ == "__main__":
    create_tables_if_not_exist() 