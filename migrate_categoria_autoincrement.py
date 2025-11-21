"""
Script para migrar a tabela categorias para usar codigo como Integer auto incremento
"""
import asyncio
from sqlalchemy import text
from app.database.db import engine
from app.models.categoria import Categoria

async def migrate_categoria_autoincrement():
    """Migra a tabela categorias para usar codigo como Integer auto incremento"""
    async with engine.begin() as conn:
        # Verificar se a tabela existe
        result = await conn.execute(text("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='categorias'
        """))
        table_info = result.fetchone()
        
        if table_info:
            sql = table_info[0]
            # Se a tabela tem codigo como VARCHAR, precisa recriar
            if 'codigo VARCHAR' in sql:
                print("Recriando tabela categorias com codigo como Integer auto incremento...")
                
                # Criar tabela temporária para salvar dados
                await conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS categorias_temp (
                        user_id INTEGER NOT NULL,
                        nome VARCHAR NOT NULL,
                        created_at DATETIME,
                        updated_at DATETIME,
                        FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """))
                
                # Copiar dados (exceto codigo, será gerado automaticamente)
                await conn.execute(text("""
                    INSERT INTO categorias_temp (user_id, nome, created_at, updated_at)
                    SELECT user_id, nome, created_at, updated_at
                    FROM categorias
                """))
                
                # Dropar tabela antiga
                await conn.execute(text("DROP TABLE IF EXISTS categorias"))
                
                # Criar nova tabela com codigo Integer auto incremento
                await conn.run_sync(Categoria.__table__.create)
                
                # Copiar dados de volta (codigo será gerado automaticamente)
                await conn.execute(text("""
                    INSERT INTO categorias (user_id, nome, created_at, updated_at)
                    SELECT user_id, nome, created_at, updated_at
                    FROM categorias_temp
                """))
                
                # Dropar tabela temporária
                await conn.execute(text("DROP TABLE IF EXISTS categorias_temp"))
                
                print("Tabela categorias recriada com sucesso! Código agora é Integer auto incremento.")
            else:
                print("Tabela categorias já está com a estrutura correta (codigo Integer).")
        else:
            print("Tabela categorias não existe. Criando...")
            await conn.run_sync(Categoria.__table__.create)
            print("Tabela categorias criada com sucesso!")

if __name__ == "__main__":
    asyncio.run(migrate_categoria_autoincrement())

