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

# Adicionar o Mangum como adaptador para a Vercel
from mangum import Mangum

# Criar diretório de logs se não existir
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configuração de logging mais detalhada
logging.basicConfig(
    level=logging.DEBUG,  # Mudado para DEBUG para mais detalhes
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

# Evento de inicialização para criar as tabelas
@app.on_event("startup")
async def startup_event():
    try:
        await create_tables()
    except Exception as e:
        logger.error(f"Erro ao criar tabelas do banco de dados: {str(e)}")
        raise

# Configurar o middleware de sessão com uma chave secreta fixa para produção
secret_key = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
app.add_middleware(
    SessionMiddleware,
    secret_key=secret_key,
    session_cookie="session",
    max_age=1800  # 30 minutos
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar arquivos estáticos
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    logger.info(f"Diretório estático montado em: {static_dir}")
else:
    logger.warning(f"Diretório estático não encontrado: {static_dir}")

# Configurar templates
templates_dir = "app/templates"
if os.path.exists(templates_dir):
    templates = Jinja2Templates(directory=templates_dir)
    logger.info(f"Diretório de templates configurado em: {templates_dir}")
else:
    logger.error(f"Diretório de templates não encontrado: {templates_dir}")
    raise FileNotFoundError(f"Diretório de templates não encontrado: {templates_dir}")

# Incluir rotas
app.include_router(main_router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user = Depends(get_current_user)):
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
                # Ordenar cidades alfabeticamente
                cities = sorted([city["nome"] for city in data])
                return JSONResponse(content={"cities": cities})
            else:
                return JSONResponse(content={"cities": []}, status_code=response.status_code)
    except Exception as e:
        logger.error(f"Erro ao buscar cidades: {str(e)}")
        return JSONResponse(content={"cities": []}, status_code=500)

# Criar o handler para a Vercel com configurações específicas
handler = Mangum(app, lifespan="off")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 