from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.license import License
from app.models.user import User


class LicenseActivationError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


async def get_license_by_key(db: AsyncSession, license_key: str) -> Optional[License]:
    if not license_key or not license_key.strip():
        return None
    result = await db.execute(
        select(License).filter(License.activation_key == license_key.strip().upper())
    )
    return result.scalar_one_or_none()


async def activate_license_for_user(
    db: AsyncSession,
    license_key: str,
    user: User,
    *,
    commit: bool = True,
) -> License:
    key = (license_key or "").strip().upper()
    if not key:
        raise LicenseActivationError("Chave de ativação é obrigatória")

    result = await db.execute(
        select(License).filter(
            License.activation_key == key,
            License.status == "Disponível",
        )
    )
    license_row = result.scalar_one_or_none()
    if not license_row:
        raise LicenseActivationError("Chave de ativação inválida ou já utilizada")

    license_row.status = "Utilizada"
    license_row.activation_email = user.email
    license_row.activation_date = datetime.now()
    license_row.client_user_id = user.id
    user.activation_key = key

    if commit:
        await db.commit()
        await db.refresh(license_row)
    else:
        await db.flush()
    return license_row


async def get_partner_license(
    db: AsyncSession,
    license_id: int,
    partner_user_id: int,
) -> License:
    result = await db.execute(
        select(License).filter(
            License.id == license_id,
            License.partner_id == partner_user_id,
        )
    )
    license_row = result.scalar_one_or_none()
    if not license_row:
        raise HTTPException(status_code=403, detail="Licença não encontrada ou sem permissão")
    if license_row.status != "Utilizada" or not license_row.client_user_id:
        raise HTTPException(
            status_code=400,
            detail="Licença ainda não foi ativada por um cliente",
        )
    return license_row
