from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from app.routes.auth import get_current_user
from app.database.db import get_db

async def check_license_middleware(request: Request, call_next):
    # Lista de rotas que não precisam de verificação de licença
    public_routes = [
        "/login",
        "/register",
        "/profile",
        "/profile/update",
        "/static",
        "/js",
        "/css"
    ]

    # Verificar se a rota atual é pública
    is_public = any(request.url.path.startswith(route) for route in public_routes)
    
    if is_public:
        return await call_next(request)

    # Get database session
    db = next(get_db())
    
    try:
        # Verificar se o usuário está autenticado
        current_user = await get_current_user(request, db)
        
        if not current_user:
            return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

        # Verificar se o usuário tem uma chave de ativação
        if not current_user.activation_key:
            return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

        return await call_next(request)
    finally:
        db.close() 