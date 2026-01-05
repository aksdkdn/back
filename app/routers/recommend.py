# --------------------------------------------------------------
# recommend.py — 사용자 맞춤 영화 추천 엔드포인트
# --------------------------------------------------------------

import os
from typing import List

# FastAPI
# - APIRouter: 라우터 모듈화를 위한 객체
# - Depends: 의존성 주입(Dependency Injection)
# - HTTPException: HTTP 상태코드와 함께 에러 응답을 보낼 때 사용
from fastapi import APIRouter, Depends, HTTPException

# SQLAlchemy ORM 세션 타입
from sqlalchemy.orm import Session

# DB 세션 팩토리 의존성 (요청마다 세션을 열고, 응답 후 닫는 generator)
from ..db import get_db

# 추천 로직 함수 (콘텐츠 기반 TF-IDF + 코사인 유사도, popularity fallback 등 구현)
from ..recommender import recommend_for_user

# 응답 스키마
# - RecommendationOut: { movie: MovieOut, score: float } 구조
# - MovieOut: 영화 정보를 직렬화하는 Pydantic 모델
from ..schemas import RecommendationOut, MovieOut


# 환경변수 DEFAULT_LIMIT 값을 읽어 기본 추천 개수로 사용
# - .env에 DEFAULT_LIMIT가 없으면 기본값 "12" 사용
# - int(...)로 문자열을 정수로 변환
DEFAULT_LIMIT = int(os.getenv("DEFAULT_LIMIT", "12"))

# 이 라우터에서 제공하는 모든 엔드포인트의 공통 prefix와 Swagger 태그
# 최종 경로는 "/api/..." 형태가 됨
router = APIRouter(prefix="/api", tags=["recommend"])


@router.get(
    "/recommend",                        # 최종 URL: /api/recommend
    response_model=List[RecommendationOut]  # 응답을 RecommendationOut 리스트로 문서화/검증
)
def recommend(
    user_id: int,                        # 쿼리 파라미터: 추천 대상 사용자 ID (필수)
    limit: int = DEFAULT_LIMIT,          # 쿼리 파라미터: 최대 추천 개수 (기본값: DEFAULT_LIMIT)
    db: Session = Depends(get_db)        # 의존성 주입: SQLAlchemy 세션 (요청 생명주기와 함께 관리)
):
    """
    주어진 user_id에 대해 상위 'limit'개의 영화 추천을 반환합니다.

    동작 개요
    --------
    1) recommend_for_user(...) 호출:
       - 사용자의 고평점 영화(상위 N개)를 기반으로 TF-IDF 임베딩 유사도를 계산
       - 코사인 유사도 가중합으로 후보 점수 산출
       - 사용자 평점이 전혀 없으면 popularity 기반 추천으로 대체

    2) 추천 결과(recs)는 (Movie, score)의 튜플 리스트 형태
       - 여기서 Movie는 SQLAlchemy ORM 객체
       - Pydantic 스키마(MovieOut)로 안전하게 직렬화해야 함

    3) 추천 결과가 비어 있으면 404로 응답
    """

    # 추천 결과를 계산 (List[Tuple[Movie, float]])
    recs = recommend_for_user(db, user_id=user_id, limit=limit)

    # 추천 결과가 없을 때: 404 Not Found 반환
    if not recs:
        raise HTTPException(status_code=404, detail="No recommendations available")

    # 응답 스키마 형태에 맞게 변환
    # - MovieOut.model_validate(m): ORM 객체 m을 Pydantic 모델로 변환(from_attributes=True 필요)
    # - score는 float로 캐스팅하여 JSON 직렬화 안정성 확보
    return [{"movie": MovieOut.model_validate(m), "score": float(score)} for m, score in recs]


# --------------------------------------------------------------
# [추가 설명 / 실전 팁]
# --------------------------------------------------------------
# 1) 입력 검증 강화(Query 사용)
#    - limit의 허용 범위를 제한하고 싶다면 fastapi.Query를 사용할 수 있습니다.
#      예)
#        from fastapi import Query
#        def recommend(user_id: int, limit: int = Query(DEFAULT_LIMIT, ge=1, le=100), db: Session = Depends(get_db)):
#          ...
#
# 2) Cold-start 전략
#    - 현재 로직은 사용자의 평점 데이터가 없을 때 popularity 기반으로 대체합니다.
#    - 추가로 최근 인기, 연도/장르별 인기, 인기+콘텐츠 혼합 가중치 등 다양화 가능.
#
# 3) 성능 최적화
#    - 추천 계산에서 전체 영화 임베딩을 자주 재구성한다면, fit 캐싱/invalidaton 정책 적용 권장
#    - 벡터를 메모리에 유지하고, 영화 수 변경(INSERT/DELETE) 시에만 재학습하도록 관리
#
# 4) 응답 필드 제어
#    - MovieOut 스키마에 노출할 필드만 선언되어 있으므로, DB 컬럼이 더 많아도 응답은 안전하게 제한됩니다.
#
# 5) 에러 메시지 현지화
#    - 사용자 대상 서비스라면 detail에 한글 메시지 지원도 고려 (예: "추천 결과가 없습니다.")
#
# 6) 예시 호출
#    - GET /api/recommend?user_id=1
#    - GET /api/recommend?user_id=2&limit=20
