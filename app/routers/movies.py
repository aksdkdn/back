# ---------------------------------------------
# movies.py — 영화 목록 조회 엔드포인트
# ---------------------------------------------

# FastAPI의 APIRouter: 라우터 분리/모듈화를 위한 도구
# Depends: 의존성 주입(Dependency Injection)을 위한 헬퍼 (예: DB 세션)
from fastapi import APIRouter, Depends

# SQLAlchemy의 ORM 세션 타입 힌트
from sqlalchemy.orm import Session

# typing: 응답 모델을 "리스트"로 명시하기 위해 사용
from typing import List

# get_db: DB 세션을 제공하는 의존성 (app/db.py의 generator 함수)
from ..db import get_db

# ORM 모델: movies 테이블과 매핑된 Movie 클래스
from ..models import Movie

# Pydantic 스키마: 응답으로 내보낼 필드/타입을 명시한 모델
from ..schemas import MovieOut


# APIRouter 인스턴스 생성
# - prefix: 이 라우터의 모든 엔드포인트 앞에 붙을 공통 경로
# - tags: 자동 문서화(Swagger UI)에서 그룹핑 이름
router = APIRouter(prefix="/api/movies", tags=["movies"])


@router.get(
    "",                          # 실제 경로는 prefix와 합쳐져 "/api/movies"가 됨
    response_model=List[MovieOut]  # 반환 형식을 Pydantic 스키마의 리스트로 명시 (자동 검증/직렬화)
)
def list_movies(
    skip: int = 0,               # 페이지네이션 오프셋 (기본 0)
    limit: int = 50,             # 페이지네이션 개수 제한 (기본 50)
    db: Session = Depends(get_db)  # 의존성 주입: 요청마다 DB 세션 1개를 주입하고, 응답 후 자동 close
):
    """
    영화 목록을 페이지네이션과 함께 반환합니다.

    - Query Params:
      - skip: 건너뛸 레코드 수 (OFFSET)
      - limit: 조회할 최대 레코드 수 (LIMIT)
    - Returns: MovieOut 스키마 리스트

    동작 흐름:
    1) SQLAlchemy ORM으로 movies 테이블에서 Movie 레코드를 조회
    2) offset/limit로 페이지네이션 적용
    3) .all()로 실제 쿼리를 수행해 파이썬 리스트 반환
    4) FastAPI가 List[MovieOut] 스키마에 맞게 자동 변환해서 응답(JSON)
    """
    # ORM 쿼리 구성: SELECT * FROM movies OFFSET :skip LIMIT :limit
    movies = db.query(Movie).offset(skip).limit(limit).all()

    # 반환: Pydantic가 MovieOut(from_attributes=True) 설정 덕분에
    # ORM 객체를 스키마로 직렬화해 JSON으로 응답
    return movies


# -----------------------------
# [추가 설명 / 실전 팁]
# -----------------------------
# 1) 유효성 검증
#    - skip, limit에 대한 범위 제한이 필요하면 Query(...)를 사용해 제약을 걸 수 있습니다.
#      예:
#        from fastapi import Query
#        def list_movies(
#            skip: int = Query(0, ge=0),
#            limit: int = Query(50, ge=1, le=200),
#            db: Session = Depends(get_db)
#        ):
#
# 2) 정렬 옵션
#    - 인기순/최신순 등의 정렬이 필요하면 order_by(...)를 연결하세요.
#      예: .order_by(Movie.popularity.desc())
#
# 3) 검색/필터
#    - 장르/연도 등의 필터가 필요하면 추가 쿼리파라미터를 받아 .filter(...)에 연결하세요.
#      예: if genre: query = query.filter(Movie.genres.ilike(f"%{genre}%"))
#
# 4) 응답 모델 유지
#    - response_model=List[MovieOut]는 API 문서화(Swagger)와 타입 안전성에 중요합니다.
#      DB 컬럼이 추가되어도 스키마에 정의한 필드만 노출되어 보안/일관성에 도움이 됩니다.
#
# 5) 예시 요청
#    - GET /api/movies            -> 기본 0~49건
#    - GET /api/movies?skip=50    -> 50번째부터 50건
#    - GET /api/movies?limit=10   -> 처음 10건
#
# 6) 성능 팁
#    - 대규모 데이터일 때는 인덱스/커버링 인덱스 설계가 중요합니다.
#    - 필요한 컬럼만 선택하려면 .with_entities(Movie.id, Movie.title, ...) 사용을 고려하세요.
#
# 7) 트랜잭션/세션 라이프사이클
#    - get_db 의존성은 요청마다 세션을 열고 finally에서 닫습니다.
#      읽기 전용 엔드포인트에서는 커밋이 필요 없습니다(자동 롤백/종료).
