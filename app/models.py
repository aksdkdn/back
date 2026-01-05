# ------------------------------------------------------------
# models.py — SQLAlchemy ORM 모델 정의 (movies/users/ratings)
# ------------------------------------------------------------

from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .db import Base  # Declarative Base: 모든 ORM 모델의 베이스 클래스

# ------------------------------
# Movie: 영화 테이블
# ------------------------------
class Movie(Base):
    __tablename__ = "movies"  # 실제 DB 테이블명

    # 기본 키(PK). index=True로 쿼리 탐색 최적화 (PK는 자동 인덱싱되지만 중복 무해)
    id = Column(Integer, primary_key=True, index=True)

    # NOT NULL 제약. 255자 제한(가변길이 문자열)
    title = Column(String(255), nullable=False)

    # 쉼표 구분 장르 문자열 등 간단 저장용
    genres = Column(String(255))

    # 긴 텍스트(줄바꿈 포함) 개요/설명 저장
    overview = Column(Text)

    # 개봉 연도
    year = Column(Integer)

    # 포스터 이미지 URL. 넉넉히 500자로 설정
    poster_url = Column(String(500))

    # 인기 점수(정렬/콜드스타트용). 기본값 0.0
    popularity = Column(Float, default=0.0)

    # 역참조 관계: Rating.movie 와의 1:N 관계를 나타냄
    # - back_populates="movie": Rating 모델의 movie 속성과 연결
    # - cascade="all, delete-orphan": 영화가 삭제되면 연결된 평점도 삭제(고아 레코드 방지)
    ratings = relationship("Rating", back_populates="movie", cascade="all, delete-orphan")


# ------------------------------
# User: 사용자 테이블
# ------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # 사용자 표시 이름

    # 사용자와 평점의 1:N 관계
    # - 사용자를 삭제하면 해당 사용자의 모든 평점도 함께 삭제
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")


# ------------------------------
# Rating: 평점 테이블 (교차 테이블)
# ------------------------------
class Rating(Base):
    __tablename__ = "ratings"

    # 복합 기본 키(PK): (user_id, movie_id)
    # - 동일 사용자가 동일 영화에 대해 한 번만 평가 가능
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    movie_id = Column(Integer, ForeignKey("movies.id"), primary_key=True)

    # 평점 값(예: 0~5 범위). 비즈니스 규칙은 스키마/서비스 레이어에서 추가 검증 권장
    rating = Column(Float, nullable=False)

    # 양방향 관계 매핑
    # - back_populates로 User.ratings / Movie.ratings와 연결
    user = relationship("User", back_populates="ratings")
    movie = relationship("Movie", back_populates="ratings")

    # 복합 유니크 제약 (PK로 이미 보장되지만, 명시적 UniqueConstraint도 가독성/이식성에 유익)
    __table_args__ = (UniqueConstraint('user_id', 'movie_id', name='uix_user_movie'),)
