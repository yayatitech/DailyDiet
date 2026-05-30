import subprocess
import sys
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_admin

router = APIRouter(prefix="/v1/admin", tags=["admin"])

ROOT = Path(__file__).resolve().parents[3]
BACKEND = Path(__file__).resolve().parents[2]


@router.post("/seed")
def admin_seed(
    _: None = Depends(require_admin),
    db: Session = Depends(get_db),
    run_import: bool = Query(default=False),
):
    if run_import:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "import_xlsm.py")],
            check=True,
            cwd=str(ROOT),
        )
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))
    import seed as seed_module

    seed_module.run_seed(db)
    return {"ok": True, "message": "Database seeded from meal-plan.json"}
