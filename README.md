# Credit System

백엔드 CS 이론을 직접 코드로 체득하기 위한 프로젝트.

FastAPI + MySQL + Redis로 크레딧 차감 시스템을 구현하면서 동시성, 트랜잭션, 인덱스, 캐싱, 네트워크를 다룬다.

## 스택

- Python 3.14 / FastAPI / SQLAlchemy (async)
- MySQL 8.0 / Redis 7
- pytest / httpx

## 실행

```bash
# 인프라
docker-compose up -d

# 서버
PIPENV_VENV_IN_PROJECT=1 pipenv run uvicorn app.main:app --reload
```
