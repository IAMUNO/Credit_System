from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Transaction, User

router = APIRouter(prefix="/credits", tags=["credits"])


class DeductRequest(BaseModel):
    user_id: int
    amount: Decimal


# Week 1: 의도적으로 Lock 없이 작성 — Race Condition 확인용
@router.post("/deduct")
async def deduct(req: DeductRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == req.user_id).with_for_update())
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.balance < req.amount:
        raise HTTPException(status_code=422, detail="Insufficient balance")

    # read-modify-write: 여기서 Race Condition 발생
    user.balance -= req.amount
    db.add(Transaction(user_id=user.id, amount=-req.amount))
    await db.commit()

    return {"user_id": user.id, "balance": float(user.balance)}


@router.get("/balance/{user_id}")
async def get_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user_id": user.id, "balance": float(user.balance)}
