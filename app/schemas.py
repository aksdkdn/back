from pydantic import BaseModel
from typing import Optional, List

# ------------------------------------------------------------
# MovieOut: 클라이언트로 내보낼 "영화" 데이터의 응답 스키마
# ------------------------------------------------------------
class MovieOut(BaseModel):
    # DB의 movies 테이블에서 노출할 필드들
    id: int
    title: str
    genres: Optional[str] = None      # 쉼표 분리 문자열 등 간단 표기
    overview: Optional[str] = None    # 줄바꿈 포함 상세 설명
    year: Optional[int] = None        # 개봉 연도(없을 수 있음)
    poster_url: Optional[str] = None  # 포스터 이미지 URL
    popularity: Optional[float] = 0   # 인기 점수 (기본 0)

    class Config:
        # ORM 객체(예: SQLAlchemy 모델)로부터 필드 맵핑 허용
        # Pydantic v2: from_attributes=True (v1의 orm_mode=True 대체)
        from_attributes = True


# ------------------------------------------------------------
# UserOut: 클라이언트로 내보낼 "사용자" 데이터의 응답 스키마
# ------------------------------------------------------------
class UserOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ------------------------------------------------------------
# RatingIn: 평점 등록/수정 시 요청 바디(JSON) 스키마
# ------------------------------------------------------------
class RatingIn(BaseModel):
    movie_id: int    # 어느 영화에 대한 평점인지
    rating: float    # 몇 점을 매겼는지 (예: 0.0 ~ 5.0)
    # NOTE: 범위 검증을 강화하려면 Pydantic의 Field를 사용해 제약을 줄 수 있음
    # 예) rating: float = Field(..., ge=0.0, le=5.0)


# ------------------------------------------------------------
# RatingOut: 클라이언트로 내보낼 "평점" 데이터의 응답 스키마
# ------------------------------------------------------------
class RatingOut(BaseModel):
    user_id: int
    movie_id: int
    rating: float

    class Config:
        from_attributes = True


# ------------------------------------------------------------
# RecommendationOut: 추천 결과 1건의 스키마
#  - movie: 추천된 영화의 상세(위의 MovieOut 스키마)
#  - score: 추천 점수(콘텐츠 유사도/블렌딩 결과 등)
# ------------------------------------------------------------
class RecommendationOut(BaseModel):
    movie: MovieOut
    score: float
