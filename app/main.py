# ------------------------------------------------------------
# main.py — FastAPI 앱 팩토리/미들웨어/라우터 등록 진입점
# ------------------------------------------------------------

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import movies, users, recommend     # 모듈화된 라우터들(영화/유저/추천)
from .db import Base, engine                      # SQLAlchemy Base/Engine (테이블 생성에 사용)

# 앱 시작 시점에 ORM 메타데이터 기준으로 테이블을 생성
# - Base.metadata.create_all()은 "존재하지 않는 테이블만" 생성하므로 안전
# - 마이그레이션 도구(예: Alembic)를 쓰기 전의 간편 초기화 용도로 유용
Base.metadata.create_all(bind=engine)

# FastAPI 애플리케이션 인스턴스 생성
# - title은 문서화(Swagger UI)에서 표시되는 서비스 제목
app = FastAPI(title="Movie Recommender API")

# -------------------------------
# CORS(Cross-Origin Resource Sharing) 설정
# -------------------------------
# - 프런트엔드(예: http://localhost:5173)와 백엔드(예: http://127.0.0.1:8000)가
#   서로 다른 오리진일 때 브라우저가 요청을 허용하도록 해주는 미들웨어
# - 개발 단계에서는 allow_* 를 "*" 로 넓게 두고, 운영에서는 특정 도메인으로 제한 권장
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # 허용할 오리진 목록 (운영에서는 구체 도메인으로 제한)
    allow_credentials=True,     # 쿠키/인증 포함 요청 허용 여부
    allow_methods=["*"],        # 허용할 HTTP 메서드 (GET/POST/PUT/DELETE/OPTIONS 등)
    allow_headers=["*"],        # 허용할 요청 헤더
)

# -------------------------------
# 라우터 등록
# -------------------------------
# - 각 도메인(영화/유저/추천)별로 APIRouter를 분리해 가독성/유지보수성 향상
# - movies:   /api/movies
# - users:    /api/users
# - recommend:/api/recommend
app.include_router(movies.router)
app.include_router(users.router)
app.include_router(recommend.router)

# -------------------------------
# 상태 확인(헬스체크)용 루트 엔드포인트
# -------------------------------
# - 배포 후 로드밸런서/모니터링에서 헬스체크로 사용하기 좋음
# - 간단한 서비스 메타 정보를 반환
@app.get("/")
def root():
    return {"ok": True, "service": "movie-recommender"}
