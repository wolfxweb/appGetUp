from app.database.db import engine
from app.models.basic_data import BasicData
from app.models.user import User

def update_database():
    print("Atualizando estrutura do banco de dados...")
    
    # Criar ou atualizar todas as tabelas
    BasicData.metadata.create_all(bind=engine)
    User.metadata.create_all(bind=engine)
    
    print("Banco de dados atualizado com sucesso!")

if __name__ == "__main__":
    update_database() 