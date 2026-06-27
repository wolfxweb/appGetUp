from fastapi import Request, HTTPException, status, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from app.routes.auth import get_current_user
from app.database.db import get_db

async def check_license_middleware(request: Request, call_next):
    # Lista de rotas que não precisam de verificação de licença
    public_routes = [
        "/",  # Página home pública
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

        # Parceiro: sem acesso ao fluxo do cliente (analise-mensal, dados básicos próprios)
        if current_user.access_level == "Parceiro":
            path = request.url.path
            if path.startswith("/analise-mensal"):
                if path.startswith("/analise-mensal/api"):
                    return JSONResponse(
                        status_code=403,
                        content={
                            "success": False,
                            "message": "Parceiros devem usar Minhas Licenças no dashboard.",
                        },
                    )
                return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
            if path.startswith("/basic-data"):
                return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

        # Se o usuário for admin ou parceiro, permitir acesso sem verificar chave de ativação
        if current_user.access_level in ("Administrador", "Parceiro"):
            return await call_next(request)

        # Fluxo pós-cadastro (Ana) — permitir antes de licença
        if request.url.path.startswith("/onboarding"):
            return await call_next(request)

        # Para usuários não-admin, verificar se tem chave de ativação
        if not current_user.activation_key:
            return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

        return await call_next(request)
    finally:
        db.close() 