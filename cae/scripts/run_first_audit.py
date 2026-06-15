"""
Run the first audit cycle on seeded data.
Executes all enabled rules and prints summary.
Run: python scripts/run_first_audit.py
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

os.environ.setdefault("DATABASE_URL", "postgresql://cae_user:cae_password@localhost:5432/cae_db")
os.environ.setdefault("SECRET_KEY", "seed-script-secret-key-32chars-xx")

from app.database import SessionLocal
from app.models.tenant import Company
from app.engines.audit_engine import AuditEngine
from app.engines.fraud_engine import FraudEngine
from app.engines.risk_engine import RiskEngine
from app.engines.wc_engine import WorkingCapitalEngine

db = SessionLocal()

company = db.query(Company).filter(Company.name == "Bharat Steel & Alloys Pvt Ltd").first()
if not company:
    print("Company not found. Run seed_data.py first.")
    sys.exit(1)

company_id = str(company.id)
print(f"Running audit for: {company.name} ({company_id})")
print()

print("Step 1/4: Running audit rules…")
engine = AuditEngine(db, company_id)
results = engine.run_all_rules()
engine.close()
print(f"  Rules run: {results['rules_run']}")
print(f"  Exceptions raised: {results['exceptions_raised']}")
print(f"  Errors: {results['errors']}")

print()
print("Step 2/4: Fraud analytics…")
fraud = FraudEngine(db, company_id)
indicators = fraud.run_all()
written = fraud.write_indicators(indicators)
print(f"  Fraud indicators detected: {written}")
for ind in indicators[:5]:
    print(f"    [{ind['severity'].upper()}] {ind['indicator_type']}: {ind['description'][:80]}…")

print()
print("Step 3/4: Risk scoring…")
risk = RiskEngine(db, company_id)
scores_written = risk.compute_and_store()
print(f"  Risk scores computed: {scores_written}")

print()
print("Step 4/4: Working capital metrics…")
wc = WorkingCapitalEngine(db, company_id)
wc_metrics = wc.compute_and_store()
print(f"  DSO: {wc_metrics.get('dso', 'N/A')} days")
print(f"  DPO: {wc_metrics.get('dpo', 'N/A')} days")
print(f"  CCC: {wc_metrics.get('ccc', 'N/A')} days")
print(f"  Stress Score: {wc_metrics.get('stress_score', 'N/A')}")

print()
print("✅ First audit complete!")
print()
print("Open: http://localhost:3000")
print("Login: sagar@ska.in / CAE@2024")
print()

# Summary by severity
from app.models.audit import AuditException
from sqlalchemy import func
for sev in ["critical", "high", "medium", "low"]:
    cnt = db.query(func.count(AuditException.id)).filter(
        AuditException.company_id == company.id,
        AuditException.severity == sev,
    ).scalar()
    print(f"  {sev.upper():8s}: {cnt} exceptions")

db.close()
