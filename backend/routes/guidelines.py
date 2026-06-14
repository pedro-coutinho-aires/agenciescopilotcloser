"""Guidelines CRUD routes."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import get_db
from db.models import AgencyORM, GuidelineORM

router = APIRouter(tags=["guidelines"])


class GuidelineCreate(BaseModel):
    feature: str
    title: str
    content: str


class GuidelineUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


def _guideline_to_dict(g: GuidelineORM) -> dict:
    return {
        "id": g.id,
        "feature": g.feature,
        "title": g.title,
        "content": g.content,
        "is_active": g.is_active,
    }


async def _get_first_agency(db: AsyncSession) -> AgencyORM:
    result = await db.execute(select(AgencyORM).limit(1))
    agency = result.scalar_one_or_none()
    if not agency:
        raise HTTPException(500, "No agency found — database not seeded")
    return agency


@router.get("/guidelines")
async def list_guidelines(feature: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """List all active guidelines, optionally filtered by feature."""
    agency = await _get_first_agency(db)
    query = select(GuidelineORM).where(
        GuidelineORM.agency_id == agency.id,
        GuidelineORM.is_active == True,
    )
    if feature:
        query = query.where(GuidelineORM.feature == feature)

    result = await db.execute(query)
    guidelines = result.scalars().all()
    return [_guideline_to_dict(g) for g in guidelines]


@router.post("/guidelines")
async def create_guideline(body: GuidelineCreate, db: AsyncSession = Depends(get_db)):
    """Create a new guideline."""
    agency = await _get_first_agency(db)
    guideline = GuidelineORM(
        agency_id=agency.id,
        feature=body.feature,
        title=body.title,
        content=body.content,
    )
    db.add(guideline)
    await db.flush()
    return _guideline_to_dict(guideline)


@router.patch("/guidelines/{guideline_id}")
async def update_guideline(guideline_id: str, body: GuidelineUpdate, db: AsyncSession = Depends(get_db)):
    """Update a guideline (partial update)."""
    result = await db.execute(
        select(GuidelineORM).where(GuidelineORM.id == guideline_id)
    )
    guideline = result.scalar_one_or_none()
    if not guideline:
        raise HTTPException(404, "Guideline not found")

    if body.title is not None:
        guideline.title = body.title
    if body.content is not None:
        guideline.content = body.content
    if body.is_active is not None:
        guideline.is_active = body.is_active

    await db.flush()
    return _guideline_to_dict(guideline)


@router.delete("/guidelines/{guideline_id}")
async def delete_guideline(guideline_id: str, db: AsyncSession = Depends(get_db)):
    """Soft-delete a guideline (sets is_active=False)."""
    result = await db.execute(
        select(GuidelineORM).where(GuidelineORM.id == guideline_id)
    )
    guideline = result.scalar_one_or_none()
    if not guideline:
        raise HTTPException(404, "Guideline not found")

    guideline.is_active = False
    await db.flush()
    return {"ok": True}
