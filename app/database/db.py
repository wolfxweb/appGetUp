from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Obter o caminho absoluto do diretório atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configurar a URL do banco de dados
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'app.db')}"

# Criar o engine assíncrono
engine = create_async_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    },
    # Habilitar write-ahead logging para melhor concorrência
    pool_pre_ping=True,
    echo=True
)

# Criar o sessionmaker assíncrono
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

# Função para obter uma sessão de banco de dados
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close() 