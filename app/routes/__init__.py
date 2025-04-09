"""
Routes package initialization.
"""

# Este arquivo marca o diretório como um pacote Python 

from fastapi import APIRouter
from app.routes.auth import router as auth_router
from app.routes.basic_data import router as basic_data_router
from app.routes.basic_data_operations import router as basic_data_operations_router
from app.routes.priorities import router as priorities_router
from app.routes.calculator import router as calculator_router
from app.routes.diagnostico import router as diagnostico_router
from app.routes.profile import router as profile_router
from app.routes.admin import router as admin_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(basic_data_router)
router.include_router(basic_data_operations_router)
router.include_router(priorities_router)
router.include_router(calculator_router)
router.include_router(diagnostico_router)
router.include_router(profile_router)
router.include_router(admin_router) 