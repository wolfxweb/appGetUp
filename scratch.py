import asyncio
from app.database.db import SessionLocal
from app.models.analise_mensal import AnaliseMensal
from sqlalchemy import select, func

async def main():
    async with SessionLocal() as db:
        query = select(AnaliseMensal).filter(AnaliseMensal.user_id == 1)
        count_query = select(func.count()).select_from(query.subquery())
        try:
            total_result = await db.execute(count_query)
            print("Sucesso!")
        except Exception as e:
            print("Erro:", str(e))

asyncio.run(main())
