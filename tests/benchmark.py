import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from sqlalchemy import text
from app.database import engine, SessionLocal, Base
from app.models import User
import app.models  # noqa: F401

BASE_URL = "http://localhost:8000"
USER_ID = 1
AMOUNT = 100
COUNT = 100


async def reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        db.add(User(id=USER_ID, balance=COUNT * AMOUNT))
        await db.commit()
    await engine.dispose()


async def run(endpoint: str) -> tuple[float, int, int]:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        tasks = [
            client.post(endpoint, json={"user_id": USER_ID, "amount": AMOUNT})
            for _ in range(COUNT)
        ]
        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

    success = sum(1 for r in results if r.status_code == 200)
    fail = COUNT - success
    return elapsed, success, fail


async def main():
    print("=" * 45)

    await reset()
    elapsed, success, fail = await run("/credits/deduct")
    print(f"Pessimistic Lock")
    print(f"  시간: {elapsed:.2f}s  성공: {success}건  실패: {fail}건")

    print()

    await reset()
    elapsed, success, fail = await run("/credits/deduct/optimistic")
    print(f"Optimistic Lock")
    print(f"  시간: {elapsed:.2f}s  성공: {success}건  실패: {fail}건")

    print("=" * 45)


asyncio.run(main())
