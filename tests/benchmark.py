import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.database import engine, SessionLocal, Base
from app.models import User
import app.models  # noqa: F401

BASE_URL = "http://localhost:8000"
AMOUNT = 100
COUNT = 100  # 유저 수 = 요청 수 (각 유저에게 1번씩)


async def reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as db:
        for i in range(1, COUNT + 1):
            db.add(User(id=i, balance=AMOUNT * 10))
        await db.commit()
    await engine.dispose()


async def run(endpoint: str) -> tuple[float, int, int]:
    # 요청마다 서로 다른 유저 — 충돌 없는 시나리오
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        tasks = [
            client.post(endpoint, json={"user_id": i, "amount": AMOUNT})
            for i in range(1, COUNT + 1)
        ]
        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start

    success = sum(1 for r in results if r.status_code == 200)
    fail = COUNT - success
    return elapsed, success, fail


async def main():
    print("=" * 50)
    print(f"시나리오: 유저 {COUNT}명에게 각 1번씩 차감 (충돌 없음)")
    print("=" * 50)

    await reset()
    elapsed, success, fail = await run("/credits/deduct")
    print(f"Pessimistic Lock")
    print(f"  시간: {elapsed:.2f}s  성공: {success}건  실패: {fail}건")

    print()

    await reset()
    elapsed, success, fail = await run("/credits/deduct/optimistic")
    print(f"Optimistic Lock")
    print(f"  시간: {elapsed:.2f}s  성공: {success}건  실패: {fail}건")

    print("=" * 50)


asyncio.run(main())
