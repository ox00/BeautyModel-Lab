from fastapi import APIRouter

from app.api.v1.accounts import router as accounts_router
from app.api.v1.keywords import router as keywords_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.data import router as data_router
from app.api.v1.system import router as system_router

api_router = APIRouter()

api_router.include_router(accounts_router)
api_router.include_router(keywords_router)
api_router.include_router(tasks_router)
api_router.include_router(data_router)
api_router.include_router(system_router)
