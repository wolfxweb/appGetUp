from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.database.db import engine, Base
from app.routes import auth, dashboard, admin, profile

# Criar tabelas no banco de dados
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Cadastro")

# Montar arquivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="app/templates")

# Incluir rotas
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(admin.router)
app.include_router(profile.router)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/login")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 