from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.db import get_db
from app.models.user import User
from app.utils.auth import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    email = None
    token = request.cookies.get("access_token")

    if token:
        try:
            token_type, token_value = token.split(" ", 1)
            if token_type.lower() == "bearer":
                payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
                email = payload.get("sub")
        except (JWTError, ValueError):
            email = None

    if not email:
        email = request.session.get("user_email")

    if not email:
        return None

    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none() 