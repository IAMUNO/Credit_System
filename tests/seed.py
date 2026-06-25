import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import User


async def seed():
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM transactions"))
        await conn.execute(text("DELETE FROM users"))

    async with SessionLocal() as db:
        user = User(id=1, balance=10000)
        db.add(user)
        await db.commit()
        print("유저 생성 완료: id=1, balance=10000")

    await engine.dispose()


asyncio.run(seed())
