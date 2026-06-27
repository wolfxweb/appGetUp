from fastapi import APIRouter, Depends, Request, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

from app.database.db import get_db
from app.models.user import User
from app.models.license import License
from app.routes.auth import get_current_user
from app.utils.license_activation import activate_license_for_user, LicenseActivationError

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

logger = logging.getLogger(__name__)


def _dashboard_now():
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(
    request: Request,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    success_message: Optional[str] = None,
    error_message: Optional[str] = None,
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    if (
        current_user.access_level not in ("Administrador", "Parceiro")
        and getattr(current_user, "onboarding_completed", None) is False
    ):
        return RedirectResponse(url="/onboarding", status_code=status.HTTP_303_SEE_OTHER)

    now = _dashboard_now()
    template_context = {
        "request": request,
        "user": current_user,
        "now": now,
        "success_message": success_message,
        "error_message": error_message,
    }

    if current_user.access_level == "Parceiro":
        result = await db.execute(
            select(License)
            .filter(License.partner_id == current_user.id)
            .order_by(License.created_at.desc())
        )
        licenses = result.scalars().all()

        client_ids = [lic.client_user_id for lic in licenses if lic.client_user_id]
        clients_by_id = {}
        if client_ids:
            clients_result = await db.execute(select(User).filter(User.id.in_(client_ids)))
            clients_by_id = {u.id: u for u in clients_result.scalars().all()}

        template_context.update({
            "is_partner_dashboard": True,
            "licenses": licenses,
            "clients_by_id": clients_by_id,
        })
        return templates.TemplateResponse("dashboard.html", template_context)

    # Se o usuário não tiver uma chave de ativação, mostrar apenas a mensagem de ativação
    if not current_user.activation_key:
        return templates.TemplateResponse("dashboard.html", template_context)

    if current_user.access_level in ["Administrador", "Administrador"]:
        total_users = await db.execute(select(User).count())
        active_licenses = await db.execute(select(License).filter(License.status == "Utilizada").count())
        available_licenses = await db.execute(select(License).filter(License.status == "Disponível").count())

        # Logs de depuração
        logger.warning(f"Dashboard Statistics - Total Users: {total_users.scalar()}")
        logger.warning(f"Dashboard Statistics - Active Licenses: {active_licenses.scalar()}")
        logger.warning(f"Dashboard Statistics - Available Licenses: {available_licenses.scalar()}")

        template_context.update({
            "total_users": total_users.scalar(),
            "active_licenses": active_licenses.scalar(),
            "available_licenses": available_licenses.scalar()
        })

    return templates.TemplateResponse(
        "dashboard.html",
        template_context
    )

@router.post("/activate-license")
async def activate_license(
    request: Request,
    activation_key: str = Form(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Logs de depuração
    logger.warning(f"License Activation - Current User: {current_user}")
    logger.warning(f"License Activation - Current User Email: {current_user.email}")
    logger.warning(f"License Activation - Activation Key: {activation_key}")

    # Verificar se a chave existe e está disponível
    try:
        await activate_license_for_user(db, activation_key, current_user)
    except LicenseActivationError:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": current_user,
                "now": _dashboard_now(),
                "error_message": "Chave de ativação inválida ou já utilizada",
            },
        )

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER) 