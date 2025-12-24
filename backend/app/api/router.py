from fastapi import APIRouter

from app.api.routes import admin_documents, auth, search, users
from app.api.routes.health import router as health_router
from app.api.routes.admin_users import router as admin_users_router
from app.api.routes.admin_metrics import router as admin_metrics_router
from app.api.routes.baseline import router as baseline_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(auth.router)
api_router.include_router(search.router)
api_router.include_router(admin_documents.router)
api_router.include_router(users.router)
api_router.include_router(admin_users_router)
api_router.include_router(admin_metrics_router)
api_router.include_router(baseline_router)
