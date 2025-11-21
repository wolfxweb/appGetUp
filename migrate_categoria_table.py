"""
Script para migrar a tabela categorias para usar codigo como chave primária
"""
import asyncio
from sqlalchemy import text
from app.database.db import engine, async_session
from app.models.categoria import Categoria

async def migrate_categoria_table():
    """Migra a tabela categorias para usar codigo como PK"""
    async with engine.begin() as conn:
        # Verificar se a tabela existe e tem o campo id
        result = await conn.execute(text("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='categorias'
        """))
        table_info = result.fetchone()
        
        if table_info:
            sql = table_info[0]
            # Se a tabela tem id como PK, precisa recriar
            if 'PRIMARY KEY (id)' in sql:
                print("Recriando tabela categorias com codigo como PK...")
                # Dropar tabela antiga
                await conn.execute(text("DROP TABLE IF EXISTS categorias"))
                # Criar nova tabela
                await conn.run_sync(Categoria.__table__.create)
                print("Tabela categorias recriada com sucesso!")
            else:
                print("Tabela categorias já está com a estrutura correta.")
        else:
            print("Tabela categorias não existe. Criando...")
            await conn.run_sync(Categoria.__table__.create)
            print("Tabela categorias criada com sucesso!")

if __name__ == "__main__":
    asyncio.run(migrate_categoria_table())

