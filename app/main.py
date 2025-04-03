import logging
import os
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
import secrets

from app.database.db import engine, Base
from app.routes import auth, dashboard, admin, profile, basic_data, diagnostico
from app.routes.auth import get_current_user

# Criar diretório de logs se não existir
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Configuração de logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # Log para o console
        logging.StreamHandler(),
        # Log para arquivo
        logging.FileHandler(os.path.join(log_dir, "app.log"), encoding='utf-8')
    ]
)

# Criar as tabelas no banco de dados
Base.metadata.create_all(bind=engine)

app = FastAPI(title="GetUp Gestão")

# Configurar o middleware de sessão
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_urlsafe(32),
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
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")), name="static")

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

# Incluir rotas
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(profile.router)
app.include_router(basic_data.router)
app.include_router(diagnostico.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user = Depends(get_current_user)):
    return templates.TemplateResponse("home.html", {
        "request": request,
        "current_user": current_user
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 