# -------------------------------------------------------
# db.py — SQLAlchemy 세션/엔진 및 FastAPI 의존성 정의
# -------------------------------------------------------

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# .env 파일의 환경변수를 현재 프로세스 환경에 주입
# - .env에 DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME 등을 정의
# - 운영환경에서는 .env 대신 실제 환경변수로 주입하는 것도 권장
load_dotenv()

# -----------------------------
# 환경변수 로딩 (기본값 포함)
# -----------------------------
# NOTE: 기본값은 로컬 개발 편의를 위한 것이며,
#       운영환경에서는 반드시 안전한 비밀값으로 대체해야 합니다.
DB_USER = os.getenv("DB_USER", "fastapiid")
DB_PASSWORD = os.getenv("DB_PASSWORD", "fastapipw")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "moviesdb")

# ----------------------------------------------
# SQLAlchemy Database URL
# ----------------------------------------------
# 기본 드라이버(mysqlclient / MySQLdb)를 쓰는 경우:
#   mysql://user:pass@host:port/db?charset=utf8mb4
#   → 윈도우/파이썬 버전에 따라 빌드 이슈가 잦음
# 아래는 순수 파이썬 드라이버(PyMySQL)를 지정한 형태:
#   mysql+pymysql://user:pass@host:port/db?charset=utf8mb4
# - utf8mb4: 이모지 포함 전체 유니코드 지원
# - PyMySQL은 윈도우 환경에서 설치가 쉬워 개발에 유리
# DATABASE_URL = f"mysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# ----------------------------------------------
# SQLAlchemy Engine 생성
# ----------------------------------------------
# - pool_pre_ping=True:
#     커넥션 풀에서 커넥션을 빌려오기 전에 'SELECT 1' 유사 ping으로
#     죽은 커넥션을 감지/재연결. MySQL의 wait_timeout 등으로 인한
#     'MySQL server has gone away' 문제를 줄여줌.
# - pool_recycle=3600:
#     커넥션을 재활용하기 전에 초 단위로 수명을 지정(여기서는 1시간).
#     DB/네트워크 환경에 맞게 조절 가능.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

# ----------------------------------------------
# 세션팩토리 생성
# ----------------------------------------------
# - autocommit=False:
#     명시적 commit() 호출 전까지 트랜잭션 커밋되지 않음.
# - autoflush=False:
#     쿼리 실행 시점에 변경사항 자동 flush 방지(필요 시 수동 flush).
#     대체로 API 요청 단위 트랜잭션에서는 False가 예측 가능성을 높임.
# - bind=engine:
#     이 세션이 사용할 엔진 지정.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ----------------------------------------------
# Declarative Base
# ----------------------------------------------
# - 모든 ORM 모델이 상속받는 베이스 클래스
# - models.py에서 class Model(Base): __tablename__=... 형태로 사용
Base = declarative_base()

def get_db():
    """
    FastAPI 의존성 주입용 DB 세션 제공자(Generator)

    사용법:
      from fastapi import Depends
      from sqlalchemy.orm import Session

      @app.get("/items")
      def handler(db: Session = Depends(get_db)):
          # 요청 수명주기(Lifespan)동안 db 세션 1개 할당
          # 반환 시 finally에서 자동 close
          return db.query(...).all()

    동작:
    1) 요청이 들어오면 SessionLocal()로 세션 생성
    2) 핸들러에 주입(yield)
    3) 응답 후 finally 블록에서 세션 종료(close)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------------------------------------
# [추가 설명 / 실전 팁]
# -------------------------------------------------------
# 1) 연결 계정/권한:
#    - MySQL에서 앱 전용 계정을 만들고 최소 권한을 부여하세요.
#      예) GRANT SELECT, INSERT, UPDATE, DELETE ON moviesdb.* TO 'fastapiid'@'%';
#
# 2) 트랜잭션 범위:
#    - 요청 당 1 트랜잭션 패턴: 핸들러 내에서 여러 작업을 수행 후 마지막에 commit()
#      예외 발생 시 롤백 처리(db.rollback())을 명시적으로 할 수도 있습니다.
#
# 3) 커넥션 풀:
#    - 대규모 트래픽 시 pool_size, max_overflow 등의 옵션을 추가해 조절하세요.
#      예) create_engine(..., pool_size=10, max_overflow=20)
#
# 4) 타임존/문자셋:
#    - MySQL 서버/세션 타임존과 애플리케이션 타임존(Asia/Seoul 등)을 일치시키는 게 안전합니다.
#    - utf8mb4를 사용하면 이모지/다국어 데이터 손실을 예방합니다.
#
# 5) 운영/개발 구성 분리:
#    - DATABASE_URL을 환경변수로 전적으로 제어(.env.dev, .env.prod 등 분리)
#    - 로컬/테스트/스테이징/운영에 따라 풀 정책과 로깅 레벨을 다르게 두는 것을 권장합니다.
#
# 6) 드라이버 교체 시:
#    - mysqlclient를 쓰고 싶다면 DATABASE_URL 스킴을 `mysql://`로 바꾸고,
#      윈도우에서는 C 빌드툴/Connector 설치가 필요한 점을 유의하세요.
