# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 목적

백엔드 CS 이론을 직접 코드로 체득하기 위한 6주 학습 프로젝트. 매 단계마다 "의도적으로 망가진 코드 → 깨달음 → 수정" 사이클로 진행한다. 이론 설명보다 코드로 직접 확인하는 것을 우선한다.

## 명령어

```bash
# 인프라 (Docker Desktop 실행 필요)
docker-compose up -d

# 서버
PIPENV_VENV_IN_PROJECT=1 pipenv run uvicorn app.main:app --reload

# DB 초기화 + 시드 (테이블 DROP → CREATE → 유저 1명 생성)
PIPENV_VENV_IN_PROJECT=1 pipenv run python tests/seed.py

# Race Condition 테스트 (동시 100번 차감)
PIPENV_VENV_IN_PROJECT=1 pipenv run python tests/race_condition.py

# Pessimistic vs Optimistic Lock 벤치마크
PIPENV_VENV_IN_PROJECT=1 pipenv run python tests/benchmark.py

# 인덱스 학습 (10만 건 insert + EXPLAIN 비교)
PIPENV_VENV_IN_PROJECT=1 pipenv run python tests/index_study.py
```

## 아키텍처

```
FastAPI (app/main.py)
  └── lifespan: 서버 시작 시 Base.metadata.create_all 실행
  └── router: app/routers/credits.py

DB 연결 (app/database.py)
  └── AsyncEngine (aiomysql 드라이버)
  └── get_db(): FastAPI Depends로 세션 주입

테이블 (app/models.py)
  └── User: id, balance (Decimal), version (Optimistic Lock용)
  └── Transaction: id, user_id, amount, idempotency_key, created_at
```

## 엔드포인트별 학습 포인트

- `POST /credits/deduct` — Pessimistic Lock (`SELECT FOR UPDATE`) + idempotency_key 중복 방지
- `POST /credits/deduct/optimistic` — Optimistic Lock (version 컬럼 + retry 3회)
- `GET /credits/balance/{user_id}` — 단순 잔액 조회

## 주의사항

- `database.py`의 `DATABASE_URL`은 하드코딩되어 있음. `.env`의 값을 직접 읽지 않으므로 DB 접속 정보 변경 시 함께 수정 필요.
- `seed.py`는 실행 시 **테이블을 DROP하고 재생성**한다. 스키마 변경(컬럼 추가 등) 후에는 seed.py 실행으로 반영.
- `tests/`의 스크립트들은 pytest가 아닌 직접 실행용(`asyncio.run`)이며, 서버가 `localhost:8000`에 실행 중이어야 한다.
- 매 단계 완료 후 git commit + push.

## 주차별 진행 현황

| 주차 | 주제 | 상태 |
|------|------|------|
| Week 1 | Race Condition 확인 (Lock 없는 코드) | ✅ 완료 |
| Week 2 | Pessimistic Lock, Optimistic Lock, idempotency_key | ✅ 완료 |
| Week 3 | 인덱스 (EXPLAIN, Covering Index) | ✅ 완료 |
| Week 4 | Redis 캐싱, 분산 락 | 🔜 |
| Week 5 | 네트워크 (WebSocket, REST) | 🔜 |
| Week 6 | pytest, README 마무리 | 🔜 |
