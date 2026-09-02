from fastapi import APIRouter

from app.api.v1 import analytics, auth, machines, plants, production, stock

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(plants.router)
api_router.include_router(machines.router)
api_router.include_router(stock.router)
api_router.include_router(production.router)
api_router.include_router(analytics.router)
