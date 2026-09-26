from fastapi import APIRouter
from sqlalchemy import text

from app.api.deps import SessionDep

router = APIRouter(tags=["system"])


@router.get("/health")
async def health(session: SessionDep) -> dict[str, str]:
    """Жив ли сервис и доступна ли база. Удобно для healthcheck и мониторинга."""
    await session.execute(text("SELECT 1"))
    return {"status": "ok"}
