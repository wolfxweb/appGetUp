# Script para criar um usuário administrador padrão
import sys
import os
from datetime import datetime
from pathlib import Path

# Certificar-se de que o script pode importar os módulos da aplicação
current_dir = Path(__file__).resolve().parent
app_dir = current_dir
sys.path.append(str(app_dir))

# Importar componentes necessários da aplicação
from app.database.db import SessionLocal, engine, Base
from app.models.user import User
from app.utils.auth import get_password_hash

def create_admin_user():
    """Cria um usuário administrador padrão no sistema."""
    print("Criando usuário administrador padrão...")
    
    # Conectar ao banco de dados
    db = SessionLocal()
    
    try:
        # Verificar se o usuário já existe
        existing_user = db.query(User).filter(User.email == "adm@adm.com").first()
        
        if existing_user:
            print("O usuário administrador já existe!")
            return
        
        # Criar usuário administrador
        hashed_password = get_password_hash("123456")
        admin_user = User(
            email="adm@adm.com",
            whatsapp="48984192339",
            activity_type="Serviços",
            password=hashed_password,
            registration_date=datetime.now(),
            status="Ativo",
            access_level="Administrador",
            terms_accepted=True
        )
        
        # Adicionar ao banco de dados
        db.add(admin_user)
        db.commit()
        print("Usuário administrador criado com sucesso!")
        print("Email: adm@adm.com")
        print("Senha: 123456")
        
    except Exception as e:
        print(f"Erro ao criar usuário administrador: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    # Garantir que as tabelas foram criadas
    Base.metadata.create_all(bind=engine)
    
    # Criar o usuário administrador
    create_admin_user() 