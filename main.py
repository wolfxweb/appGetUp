import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.routes import auth, dashboard, admin, profile
from app.database.db import engine, Base
from app.models.user import User
from app.models.license import License
from app.middleware.auth import check_license_middleware

# Configurar logging
import os

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

app = FastAPI()

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Adicionar middleware de verificação de licença
app.middleware("http")(check_license_middleware)

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/js", StaticFiles(directory="app/static/js"), name="js")

# Incluir rotas
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(profile.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 