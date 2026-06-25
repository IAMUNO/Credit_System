"""
Week 3: 인덱스 학습
1. seed: user 1명 + transactions 10만 건 bulk insert
2. EXPLAIN: 인덱스 없는 Full Table Scan 확인
3. 복합 인덱스 (user_id, created_at) 추가 후 EXPLAIN 비교
4. Covering Index 확인 (Extra: Using index)
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.database import engine, SessionLocal, Base
from app.models import User, Transaction
import app.models  # noqa: F401

BULK_SIZE = 100_000


async def reset_and_seed():
    print("=" * 60)
    print(f"1단계: 테이블 초기화 + transactions {BULK_SIZE:,}건 insert")
    print("=" * 60)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        db.add(User(id=1, balance=9_999_999))
        await db.commit()

    # bulk insert: 1000건씩 나눠서 insert
    batch = 1000
    start = time.perf_counter()
    async with engine.begin() as conn:
        for offset in range(0, BULK_SIZE, batch):
            rows = [
                {"user_id": 1, "amount": -100, "idempotency_key": None}
                for _ in range(batch)
            ]
            await conn.execute(
                text(
                    "INSERT INTO transactions (user_id, amount) VALUES (:user_id, :amount)"
                ),
                rows,
            )
    elapsed = time.perf_counter() - start
    print(f"  insert 완료: {elapsed:.2f}s\n")


async def explain(label: str, query: str):
    async with engine.begin() as conn:
        result = await conn.execute(text(f"EXPLAIN {query}"))
        rows = result.fetchall()

    print(f"[{label}]")
    cols = result.keys()
    header = " | ".join(f"{c:<15}" for c in cols)
    print("  " + header)
    print("  " + "-" * len(header))
    for row in rows:
        print("  " + " | ".join(f"{str(v or ''):<15}" for v in row))
    print()


async def run_explains():
    print("=" * 60)
    print("2단계: EXPLAIN 비교 (인덱스 없음 vs 복합 인덱스 vs Covering)")
    print("=" * 60)

    # 1) 인덱스 없는 상태
    await explain(
        "인덱스 없음 — user_id로 필터",
        "SELECT * FROM transactions WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10",
    )

    # 복합 인덱스 추가
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "CREATE INDEX idx_transactions_user_created "
                "ON transactions (user_id, created_at)"
            )
        )
    print("  → 복합 인덱스 (user_id, created_at) 생성 완료\n")

    # 2) 복합 인덱스 후
    await explain(
        "복합 인덱스 후 — SELECT *",
        "SELECT * FROM transactions WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10",
    )

    # 3) Covering Index: SELECT 컬럼을 인덱스 컬럼만으로 구성
    await explain(
        "Covering Index — SELECT user_id, created_at (인덱스 컬럼만 선택)",
        "SELECT user_id, created_at FROM transactions WHERE user_id = 1 ORDER BY created_at DESC LIMIT 10",
    )


async def main():
    await reset_and_seed()
    await run_explains()
    await engine.dispose()


asyncio.run(main())
