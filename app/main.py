import logging
import os
import asyncio
import httpx
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from starlette.middleware.sessions import SessionMiddleware
import secrets

from app.database.db import engine, Base
from app.routes import router as main_router
from app.routes.auth import get_current_user

# Importar modelos para garantir que as tabelas sejam criadas
from app.models import User, BasicData, License, Categoria, Produto

# Adicionar o Mangum como adaptador para a Vercel
from mangum import Mangum

# Criar diretório de logs se não existir
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, "app.log"), encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(title="GetUp Gestão")

# Função assíncrona para criar as tabelas
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Tabelas do banco de dados criadas com sucesso")

# Migração automática de colunas novas no banco SQLite
def run_column_migrations():
    import sqlite3 as _sqlite3
    db_path = os.path.join("app", "database", "app.db")
    if not os.path.exists(db_path):
        return
    try:
        conn = _sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Migrações da tabela users
        cursor.execute("PRAGMA table_info(users)")
        user_cols = {row[1] for row in cursor.fetchall()}
        for col, typ in [
            ("ideal_profit_margin",       "REAL"),
            ("service_capacity",          "REAL"),
            ("ja_acessou",                "INTEGER"),
            ("onboarding_completed",      "INTEGER"),
            ("production_hours",          "REAL"),
            ("estimated_loss_percentage", "REAL"),
            ("has_product_sheet",         "TEXT"),
        ]:
            if col not in user_cols:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {typ}")
                logger.info(f"Coluna adicionada: users.{col}")

        # Migrações da tabela basic_data
        cursor.execute("PRAGMA table_info(basic_data)")
        bd_cols = {row[1] for row in cursor.fetchall()}
        for col, typ in [
            ("other_fixed_costs",              "FLOAT"),
            ("ideal_service_profit_margin",    "FLOAT"),
        ]:
            if col not in bd_cols:
                cursor.execute(f"ALTER TABLE basic_data ADD COLUMN {col} {typ}")
                logger.info(f"Coluna adicionada: basic_data.{col}")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Migração automática: {e}")

# Evento de inicialização
@app.on_event("startup")
async def startup_event():
    try:
        run_column_migrations()
        await create_tables()
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
        raise

# Middleware de sessão
secret_key = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    session_cookie="session",
    max_age=31536000
)

# CORS
_cors_origins = [
    o.strip()
    for o in os.getenv("CORS_ORIGINS", "http://localhost:9090,http://127.0.0.1:9090").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Arquivos estáticos
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Diretório estático montado em: {static_dir}")
else:
    logger.warning(f"Diretório estático não encontrado: {static_dir}")

# Templates
templates_dir = "app/templates"
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
    logger.info(f"Diretório de templates configurado em: {templates_dir}")
else:
    logger.error(f"Diretório de templates não encontrado: {templates_dir}")
    raise FileNotFoundError(f"Diretório de templates não encontrado: {templates_dir}")

# Rotas
app.include_router(main_router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user=Depends(get_current_user)):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": current_user
    })

@app.get("/api/cities/{state}")
async def get_cities(state: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"https://viacep.com.br/ws/{state}/cidades/")
            if response.status_code == 200:
                data = response.json()
                cities = sorted([city["nome"] for city in data])
                return JSONResponse(content={"cities": cities})
            else:
                return JSONResponse(content={"cities": []}, status_code=response.status_code)
    except Exception as e:
        logger.error(f"Erro ao buscar cidades: {str(e)}")
        return JSONResponse(content={"cities": []}, status_code=500)

# Handler para Vercel
handler = Mangum(app, lifespan="off")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
