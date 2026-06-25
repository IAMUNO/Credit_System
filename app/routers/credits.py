from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Transaction, User

router = APIRouter(prefix="/credits", tags=["credits"])


class DeductRequest(BaseModel):
    user_id: int
    amount: Decimal
    idempotency_key: str | None = None


# Week 1: 의도적으로 Lock 없이 작성 — Race Condition 확인용
@router.post("/deduct")
async def deduct(req: DeductRequest, db: AsyncSession = Depends(get_db)):
    # Week 2: idempotency_key가 있으면 중복 요청 체크
    if req.idempotency_key:
        existing = await db.execute(
            select(Transaction).where(Transaction.idempotency_key == req.idempotency_key)
        )
        if existing.scalar_one_or_none():
            balance = await db.execute(select(User).where(User.id == req.user_id))
            user = balance.scalar_one()
            return {"user_id": user.id, "balance": float(user.balance), "cached": True}

    result = await db.execute(select(User).where(User.id == req.user_id).with_for_update())
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.balance < req.amount:
        raise HTTPException(status_code=422, detail="Insufficient balance")

    user.balance -= req.amount
    db.add(Transaction(user_id=user.id, amount=-req.amount, idempotency_key=req.idempotency_key))
    await db.commit()

    return {"user_id": user.id, "balance": float(user.balance)}


# Week 2: Optimistic Lock — version 컬럼으로 충돌 감지 후 retry
@router.post("/deduct/optimistic")
async def deduct_optimistic(req: DeductRequest, db: AsyncSession = Depends(get_db)):
    max_retries = 3
    for _ in range(max_retries):
        result = await db.execute(select(User).where(User.id == req.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if user.balance < req.amount:
            raise HTTPException(status_code=422, detail="Insufficient balance")

        current_version = user.version

        # 저장 시점에 version이 그대로인지 확인 — 달라지면 누군가 먼저 수정한 것 -> Optimistic lock 
        result = await db.execute(
            update(User)
            .where(User.id == req.user_id, User.version == current_version)
            .values(balance=user.balance - req.amount, version=current_version + 1)
        )
        await db.commit()

        if result.rowcount == 0:
            # 충돌 발생 — 재시도
            await db.rollback()
            continue

        db.add(Transaction(user_id=user.id, amount=-req.amount))
        await db.commit()
        return {"user_id": user.id, "balance": float(user.balance - req.amount)}

    raise HTTPException(status_code=409, detail="Too many conflicts, try again")


@router.get("/balance/{user_id}")
async def get_balance(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {"user_id": user.id, "balance": float(user.balance)}
