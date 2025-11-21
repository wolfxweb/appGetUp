"""
Script para criar a tabela produtos
"""
import asyncio
from sqlalchemy import text
from app.database.db import engine
from app.models.produto import Produto

async def migrate_produto_table():
    """Cria a tabela produtos"""
    async with engine.begin() as conn:
        # Verificar se a tabela existe
        result = await conn.execute(text("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='produtos'
        """))
        table_info = result.fetchone()
        
        if not table_info:
            print("Criando tabela produtos...")
            await conn.run_sync(Produto.__table__.create)
            print("Tabela produtos criada com sucesso!")
        else:
            print("Tabela produtos já existe.")

if __name__ == "__main__":
    asyncio.run(migrate_produto_table())

