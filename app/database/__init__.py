"""
Database package initialization.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Obter o caminho absoluto do diretório atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Configurar a URL do banco de dados
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'app.db')}"

# Criar o engine assíncrono
engine = create_async_engine(DATABASE_URL, echo=True)

# Criar o sessionmaker assíncrono
async_session = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Exportar o async_session para ser usado em outros módulos
__all__ = ['async_session']
