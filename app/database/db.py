from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Obter o caminho absoluto do diretório atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configurar a URL do banco de dados
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"

# Criar o engine com as configurações corretas para SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    },
    # Habilitar write-ahead logging para melhor concorrência
    pool_pre_ping=True,
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Função para obter uma sessão de banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 