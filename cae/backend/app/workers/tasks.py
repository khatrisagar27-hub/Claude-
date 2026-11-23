"""Celery background tasks.

Each task body is a plain function (``execute_*``) so the API can run it in-process when no
worker is reachable — see ``app.workers.dispatch``.
"""
import uuid
from datetime import datetime

from app.workers.celery_app import celery_app
from app.database import SessionLocal


def execute_audit_cycle(company_id: str, job_id: str | None = None, engagement_id: str | None = None) -> dict:
    """Every enabled rule (all frequencies, or the engagement's scope), then fraud analytics,
    risk scores and working-capital metrics. Progress and counts are written to the SyncJob."""
    from app.models.ingestion import SyncJob
    from app.models.engagement import AuditEngagement
    from app.engines.audit_engine import AuditEngine
    from app.engines.fraud_engine import FraudEngine
    from app.engines.risk_engine import RiskEngine
    from app.engines.wc_engine import WorkingCapitalEngine

    db = SessionLocal()
    job = None
    try:
        if job_id:
            job = db.query(SyncJob).filter(SyncJob.id == uuid.UUID(str(job_id))).first()
        if job:
            job.status = "running"
            job.started_at = datetime.utcnow()
            db.commit()
        engagement = None
        if engagement_id:
            engagement = db.query(AuditEngagement).filter(AuditEngagement.id == uuid.UUID(str(engagement_id))).first()
            if engagement and engagement.status == "planning":
                engagement.status = "fieldwork"
                db.commit()

        engine = AuditEngine(db, company_id, engagement)
        results = engine.run_all_rules()
        engine.close()

        fraud = FraudEngine(db, company_id)
        fraud_written = fraud.write_indicators(fraud.run_all())
        risk_written = RiskEngine(db, company_id).compute_and_store()
        wc = WorkingCapitalEngine(db, company_id).compute_and_store()

        summary = {
            "rules_run": results["rules_run"], "exceptions_raised": results["exceptions_raised"],
            "rule_errors": results["errors"], "load_errors": results.get("load_errors") or {},
            "failed_rules": [d for d in results["rule_details"] if d["status"] != "completed"],
            "fraud_indicators": fraud_written, "risk_scores": risk_written,
            "dso": wc.get("dso"), "wc_stress_score": wc.get("wc_stress_score"),
        }
        if job:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.records_processed = results.get("rules_run", 0)
            job.exceptions_raised = results.get("exceptions_raised", 0)
            job.result_json = summary
            db.commit()
        return summary
    except Exception as exc:
        db.rollback()
        if job_id:
            from app.models.ingestion import SyncJob
            job = db.query(SyncJob).filter(SyncJob.id == uuid.UUID(str(job_id))).first()
            if job:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                job.error_message = str(exc)[:500]
                db.commit()
        raise
    finally:
        db.close()


def execute_file_import(file_id: str, detected_type: str | None = None) -> dict:
    from app.models.ingestion import UploadedFile
    from app.connectors.excel_importer import ExcelImporter

    db = SessionLocal()
    try:
        uploaded = db.query(UploadedFile).filter(UploadedFile.id == uuid.UUID(str(file_id))).first()
        if not uploaded:
            return {"error": "file not found"}

        uploaded.status = "processing"
        db.commit()

        importer = ExcelImporter(db, str(uploaded.company_id))
        result = importer.import_file(uploaded.file_path, uploaded.file_type, detected_type)

        uploaded.rows_parsed = result.get("rows_parsed", result.get("rows_imported", 0))
        uploaded.rows_imported = result.get("rows_imported", 0)
        uploaded.parse_errors = result.get("errors", [])
        uploaded.status = "imported" if result.get("rows_imported", 0) or not result.get("errors") else "failed"
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        from app.models.ingestion import UploadedFile
        f = db.query(UploadedFile).filter(UploadedFile.id == uuid.UUID(str(file_id))).first()
        if f:
            f.status = "failed"
            f.parse_errors = [str(e)[:500]]
            db.commit()
        return {"error": str(e)}
    finally:
        db.close()


def execute_tally_import(job_id: str, cae_company_id: str, tally_company: str, from_date: str, to_date: str,
                         extended: bool = False) -> dict:
    from app.connectors.tally_live import run_import_job
    return run_import_job(job_id, cae_company_id, tally_company, from_date, to_date, extended)


@celery_app.task
def run_audit_cycle(company_id: str, job_id: str | None = None, engagement_id: str | None = None):
    return execute_audit_cycle(company_id, job_id, engagement_id)


@celery_app.task
def process_uploaded_file(file_id: str, detected_type: str | None = None):
    return execute_file_import(file_id, detected_type)


@celery_app.task
def import_from_tally(job_id: str, cae_company_id: str, tally_company: str, from_date: str, to_date: str,
                      extended: bool = False):
    return execute_tally_import(job_id, cae_company_id, tally_company, from_date, to_date, extended)


@celery_app.task
def daily_audit_all_companies():
    """Beat schedule: continuous-monitoring run for every active company, each with its own job row."""
    from app.models.tenant import Company
    from app.models.ingestion import SyncJob

    db = SessionLocal()
    try:
        companies = db.query(Company).filter(Company.is_active == True).all()  # noqa: E712
        for company in companies:
            job = SyncJob(id=uuid.uuid4(), company_id=company.id, job_type="scheduled_audit",
                          status="queued", triggered_by="scheduler")
            db.add(job)
            db.commit()
            run_audit_cycle.delay(str(company.id), str(job.id))
        return {"triggered": len(companies)}
    finally:
        db.close()
