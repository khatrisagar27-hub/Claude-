"""Celery background tasks."""
from app.workers.celery_app import celery_app
from app.database import SessionLocal


@celery_app.task(bind=True, max_retries=3)
def run_audit_cycle(self, company_id: str, job_id: str):
    db = SessionLocal()
    try:
        from app.models.ingestion import SyncJob
        from app.engines.audit_engine import AuditEngine
        from app.engines.fraud_engine import FraudEngine
        from app.engines.risk_engine import RiskEngine
        from app.engines.wc_engine import WorkingCapitalEngine
        from datetime import datetime

        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
        if job:
            job.status = "running"
            job.started_at = datetime.utcnow()
            db.commit()

        engine = AuditEngine(db, company_id)
        results = engine.run_all_rules()
        engine.close()

        fraud = FraudEngine(db, company_id)
        indicators = fraud.run_all()
        fraud.write_indicators(indicators)

        risk = RiskEngine(db, company_id)
        risk.compute_and_store()

        wc = WorkingCapitalEngine(db, company_id)
        wc.compute_and_store()

        if job:
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.records_processed = results.get("rules_run", 0)
            job.exceptions_raised = results.get("exceptions_raised", 0)
            db.commit()

        return results
    except Exception as exc:
        db.rollback()
        from app.models.ingestion import SyncJob
        job = db.query(SyncJob).filter(SyncJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error_message = str(exc)[:500]
            db.commit()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()


@celery_app.task
def process_uploaded_file(file_id: str):
    db = SessionLocal()
    try:
        from app.models.ingestion import UploadedFile
        from app.connectors.excel_importer import ExcelImporter

        uploaded = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if not uploaded:
            return

        uploaded.status = "processing"
        db.commit()

        importer = ExcelImporter(db, str(uploaded.company_id))
        result = importer.import_file(uploaded.file_path, uploaded.file_type)

        uploaded.rows_parsed = result.get("rows_imported", 0)
        uploaded.rows_imported = result.get("rows_imported", 0)
        uploaded.parse_errors = result.get("errors", [])
        uploaded.status = "imported"
        db.commit()
    except Exception as e:
        db.rollback()
        from app.models.ingestion import UploadedFile
        f = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
        if f:
            f.status = "failed"
            f.parse_errors = [str(e)]
            db.commit()
    finally:
        db.close()


@celery_app.task
def daily_audit_all_companies():
    db = SessionLocal()
    try:
        from app.models.tenant import Company
        companies = db.query(Company).filter(Company.is_active == True).all()
        for company in companies:
            run_audit_cycle.delay(str(company.id), "daily_scheduled")
        return {"triggered": len(companies)}
    finally:
        db.close()
