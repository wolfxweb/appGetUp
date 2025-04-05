from app.database.db import engine, Base
from app.models.calculator import Calculator

def create_calculator_table():
    # Criar a tabela
    Calculator.__table__.create(engine)
    print("Tabela calculator criada com sucesso!")

if __name__ == "__main__":
    create_calculator_table() 