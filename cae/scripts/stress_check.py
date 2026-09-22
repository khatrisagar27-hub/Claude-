"""
Run every rule for the stress company twice and compare against stress_expected.json.
Pass: each rule stores exactly the expected number of exceptions, no rule errors, and
the second run raises nothing new (results are deterministic and deduplicated).
Run after scripts/stress_seed.py. Exit code 1 on any mismatch.
"""
import os
import sys
_backend = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, _backend if os.path.exists(_backend) else os.path.join(os.path.dirname(__file__), '..'))

import json
import time
import uuid

os.environ.setdefault("DATABASE_URL", "postgresql://cae_user:cae_password@localhost:5432/cae_db")
os.environ.setdefault("SECRET_KEY", "seed-script-secret-key-32chars-xx")

from sqlalchemy import func

from app.database import SessionLocal
from app.engines.audit_engine import AuditEngine
from app.models.audit import AuditException, AuditRule

cfg = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "stress_expected.json")))
CID, EXP = cfg["company_id"], cfg["expected"]
db = SessionLocal()
failures = []

for run_no in (1, 2):
    t = time.time()
    new = 0
    for freq in ("daily", "weekly", "monthly"):
        engine = AuditEngine(db, CID)
        res = engine.run_all_rules(freq)
        engine.close()
        new += res["exceptions_raised"]
        for d in res["rule_details"]:
            if d["status"] != "completed":
                failures.append(f"run {run_no}: {d['rule_code']} {d['status']}: {d.get('error', '')[:200]}")
    print(f"Run {run_no}: {time.time() - t:.1f}s, {new:,} new exceptions")
    if run_no == 2 and new:
        failures.append(f"run 2 raised {new} new exceptions on unchanged data")

stored = dict(
    db.query(AuditRule.rule_code, func.count(AuditException.id))
    .outerjoin(AuditException, AuditException.rule_id == AuditRule.id)
    .filter(AuditRule.company_id == uuid.UUID(CID))
    .group_by(AuditRule.rule_code).all()
)

print(f"\n{'Rule':<10}{'Expected':>10}{'Stored':>10}")
for code in sorted(set(EXP) | set(stored)):
    exp, got = EXP.get(code), stored.get(code, 0)
    flag = "" if exp == got else "   <-- MISMATCH"
    if flag:
        failures.append(f"{code}: expected {exp}, stored {got}")
    print(f"{code:<10}{str(exp):>10}{got:>10}{flag}")

print()
if failures:
    print("FAILED\n  " + "\n  ".join(failures))
    sys.exit(1)
print(f"PASSED: all {len(EXP)} rules match planted counts; rerun raised nothing new.")
