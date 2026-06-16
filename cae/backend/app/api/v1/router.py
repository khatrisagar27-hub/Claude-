"""Aggregate all v1 API routers."""
from fastapi import APIRouter

from app.api.v1 import auth, companies, ingestion, rules, exceptions, queries, remediation, risk, gst, dashboard, reports

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(companies.router, prefix="/companies", tags=["Companies"])
api_router.include_router(ingestion.router, prefix="/ingestion", tags=["Ingestion"])
api_router.include_router(rules.router, prefix="/rules", tags=["Rules"])
api_router.include_router(exceptions.router, prefix="/exceptions", tags=["Exceptions"])
api_router.include_router(queries.router, prefix="/queries", tags=["Queries"])
api_router.include_router(remediation.router, prefix="/remediation", tags=["Remediation"])
api_router.include_router(risk.router, prefix="/risk", tags=["Risk"])
api_router.include_router(gst.router, prefix="/gst", tags=["GST"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
