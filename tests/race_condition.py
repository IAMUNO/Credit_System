import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx

BASE_URL = "http://localhost:8000"
USER_ID = 1
AMOUNT = 100
COUNT = 100


ENDPOINT = "/credits/deduct/optimistic"


async def deduct(client: httpx.AsyncClient, i: int):
    res = await client.post(ENDPOINT, json={"user_id": USER_ID, "amount": AMOUNT})
    return res.status_code


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        tasks = [deduct(client, i) for i in range(COUNT)]
        results = await asyncio.gather(*tasks)

    success = results.count(200)
    fail = len(results) - success
    print(f"성공: {success}건 / 실패: {fail}건")

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        res = await client.get(f"/credits/balance/{USER_ID}")
        balance = res.json()["balance"]

    expected = 10000 - (success * AMOUNT)
    print(f"최종 잔액: {balance}")
    print(f"예상 잔액: {expected}")

    if balance != expected:
        print(f"Race Condition 발생! 차이: {balance - expected}원 더 남음")
    else:
        print("정상 (Race Condition 없음)")


asyncio.run(main())
