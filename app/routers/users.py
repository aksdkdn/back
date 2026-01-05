# -----------------------------------------------------------
# users.py — 유저 및 평점 관련 REST 엔드포인트
# -----------------------------------------------------------

from fastapi import APIRouter, Depends, HTTPException  # APIRouter: 라우팅 모듈화 / Depends: 의존성 주입 / HTTPException: 에러 응답
from sqlalchemy.orm import Session                     # SQLAlchemy ORM 세션 타입 힌트
from typing import List                                # 응답 타입: List[...] 명시
from ..db import get_db                                # DB 세션 의존성 (요청마다 세션 열고 응답 후 닫음)
from ..models import User, Rating, Movie               # ORM 모델: users / ratings / movies 테이블
from ..schemas import UserOut, RatingIn, RatingOut     # Pydantic 스키마: 응답·요청 페이로드 구조

# 이 모듈의 엔드포인트는 "/api/users"로 시작
# Swagger/OpenAPI 문서에서 "users" 그룹으로 묶음
router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    """
    전체 사용자 목록을 반환합니다.
    - DB 세션은 Depends(get_db)로 주입되어, 요청 생명주기와 함께 안전하게 관리됩니다.
    - response_model=List[UserOut] 덕분에 ORM 객체가 Pydantic 스키마로 직렬화되어 노출 필드가 통제됩니다.
    """
    return db.query(User).all()  # SELECT * FROM users


@router.get("/{user_id}/ratings", response_model=List[RatingOut])
def get_ratings(user_id: int, db: Session = Depends(get_db)):
    """
    특정 사용자(user_id)의 평점 목록을 반환합니다.
    - URL 경로 파라미터로 user_id를 받습니다.
    - RatingOut 스키마 리스트로 직렬화되어 반환됩니다.
    """
    # SELECT * FROM ratings WHERE user_id = :user_id
    return db.query(Rating).filter(Rating.user_id == user_id).all()


@router.post("/{user_id}/ratings", response_model=RatingOut)
def upsert_rating(user_id: int, payload: RatingIn, db: Session = Depends(get_db)):
    """
    특정 사용자(user_id)에 대해, (movie_id, rating)을 업서트합니다.
    - 이미 해당 (user_id, movie_id) 평점이 있으면 UPDATE
    - 없으면 INSERT
    - 성공 시, 최종 저장된 Rating 레코드를 반환합니다.

    요청 바디(JSON) 예:
    {
      "movie_id": 1,
      "rating": 4.5
    }
    """
    # (주의) SQLAlchemy 2.0에서는 Query.get()가 deprecated 경고가 있습니다.
    #   Session.get(Model, pk) 형태가 신 API이지만, 여기서는 '원본 유지' 요구에 따라 그대로 둡니다.
    user = db.query(User).get(user_id)               # 사용자 존재 확인
    movie = db.query(Movie).get(payload.movie_id)    # 영화 존재 확인

    if not user or not movie:
        # 사용자 또는 영화가 존재하지 않으면 404 반환
        raise HTTPException(status_code=404, detail="User or movie not found")

    # 기존 평점이 있는지 조회 (user_id + movie_id 복합 PK로 정의되어 있음)
    r = (
        db.query(Rating)
        .filter(Rating.user_id == user_id, Rating.movie_id == payload.movie_id)
        .one_or_none()
    )

    if r:
        # 이미 존재: UPDATE
        r.rating = payload.rating
    else:
        # 존재하지 않음: INSERT
        r = Rating(user_id=user_id, movie_id=payload.movie_id, rating=payload.rating)
        db.add(r)

    db.commit()   # 트랜잭션 커밋 (INSERT/UPDATE 반영)
    db.refresh(r) # 세션에 반영된 최신 상태로 새로고침 (DB DEFAULT/trigger 반영 시 유용)

    # Pydantic 모델(RatingOut)로 직렬화되어 반환 (response_model 지정 덕분에 자동 변환)
    return r


# -----------------------------------------------------------
# [추가 설명 / 실전 팁]
# -----------------------------------------------------------
# 1) 입력값 검증 강화
#    - RatingIn 스키마에서 rating의 범위(예: 0~5)를 명확히 검증하세요.
#    - FastAPI Query/Path 파라미터에 ge/le를 걸어 범위를 제어할 수 있습니다.
#
# 2) SQLAlchemy 2.0 스타일 권장 포인트(참고)
#    - Query.get() 대신 Session.get(Model, pk) 사용:
#        user = db.get(User, user_id)
#        movie = db.get(Movie, payload.movie_id)
#      (본 예제는 "원본 코드 유지" 요청으로 기존 코드 유지)
#
# 3) 동시성(낙관적 잠금) 고려
#    - 동시 업서트 요청이 경쟁할 수 있는 환경이라면, UNIQUE 제약(복합 PK) + 예외 처리/재시도 로직 고려
#
# 4) 성능/보안
#    - list_users는 전체 목록을 노출하므로, 실제 서비스에서는 페이지네이션/검색 필터를 권장
#    - RatingOut/ UserOut 스키마로 노출 컬럼을 통제하여 과다 노출 방지
#
# 5) 예시 호출
#    - GET  /api/users
#    - GET  /api/users/1/ratings
#    - POST /api/users/1/ratings   (JSON: {"movie_id": 3, "rating": 4.0})
#
# 6) 에러 응답 메시지 현지화
#    - 사용자 대상 서비스라면 detail 메시지를 한글로 바꾸는 것도 좋습니다.
#      예: "사용자 또는 영화를 찾을 수 없습니다."
