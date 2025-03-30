# Script para criar um usuário administrador padrão
import sys
import os
from datetime import datetime
from pathlib import Path
import bcrypt
from sqlalchemy.orm import Session

# Certificar-se de que o script pode importar os módulos da aplicação
current_dir = Path(__file__).resolve().parent
app_dir = current_dir
sys.path.append(str(app_dir))

# Importar componentes necessários da aplicação
from app.database.db import SessionLocal, engine, Base
from app.models.user import User

def create_admin():
    """Cria um usuário administrador padrão no sistema."""
    print("Criando usuário administrador padrão...")
    
    # Criar uma sessão do banco de dados
    db = SessionLocal()
    
    try:
        # Verificar se já existe um usuário administrador
        admin = db.query(User).filter(User.email == "adm@adm.com").first()
        
        if admin:
            print("Usuário administrador já existe.")
            return
        
        # Criar hash da senha
        password = "123456"
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Criar usuário administrador
        admin = User(
            name="Administrador",
            email="adm@adm.com",
            whatsapp="48984192339",
            activity_type="Serviços",
            password=hashed_password.decode('utf-8'),
            access_level="Administrador",
            terms_accepted=True,
            registration_date=datetime.now()
        )
        
        # Adicionar à sessão e salvar
        db.add(admin)
        db.commit()
        
        print("Usuário administrador criado com sucesso!")
        
    except Exception as e:
        print(f"Erro ao criar usuário administrador: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Garantir que as tabelas foram criadas
    Base.metadata.create_all(bind=engine)
    
    # Criar o usuário administrador
    create_admin() 