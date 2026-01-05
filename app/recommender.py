from __future__ import annotations
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .models import Movie, Rating

class ContentRecommender:
    def __init__(self):
        # TF-IDF 벡터라이저 설정
        # - stop_words='english' : 영어 불용어 제거
        # - max_features=20000    : 상위 2만개의 토큰만 사용(메모리/속도 균형)
        # - ngram_range=(1,2)     : 유니그램+바이그램(단어 1개/2개 묶음)까지 고려 → 표현력↑
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=20000,
            ngram_range=(1,2)
        )
        self.movie_ids: List[int] = []  # 인덱스↔영화ID 매핑을 위한 ID 리스트
        self.tfidf_matrix = None        # 모든 영화의 TF-IDF 행렬(희소행렬)

    def _build_corpus_row(self, m: Movie) -> str:
        # 한 영화의 텍스트 코퍼스(입력 문서) 구성
        # - 제목(title), 장르(genres), 개요(overview)를 공백으로 이어붙여 한 문서로 사용
        fields = [m.title or "", m.genres or "", (m.overview or "")]
        return " ".join(fields)

    def fit(self, movies: List[Movie]):
        # 전체 영화 목록으로부터 TF-IDF 모델을 학습(fit)하고 행렬 생성
        self.movie_ids = [m.id for m in movies]
        corpus = [self._build_corpus_row(m) for m in movies]
        if len(corpus) == 0:
            # 영화가 하나도 없는 경우
            self.tfidf_matrix = None
        else:
            # TF-IDF 학습 및 변환
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def scores_for_movies(self, liked_movie_ids: List[int], weights: List[float]|None=None) -> Dict[int, float]:
        # 사용자가 좋아한 영화(liked_movie_ids)를 기준으로 전체 후보 영화 점수 계산
        # - liked_movie_ids: 사용자 상위 평점 영화들의 ID 목록
        # - weights: 각 영화의 가중치(보통 평점값)를 동일 길이로 전달(없으면 1.0)
        if self.tfidf_matrix is None or not self.movie_ids:
            return {}

        # 영화ID → TF-IDF 행렬 인덱스 매핑 사전
        id_to_index = {mid: idx for idx, mid in enumerate(self.movie_ids)}
        # 사용자가 좋아한 영화들의 행렬 인덱스 집합
        indices = [id_to_index[mid] for mid in liked_movie_ids if mid in id_to_index]
        if not indices:
            # 좋아한 영화가 현재 TF-IDF에 존재하지 않는다면 스코어 계산 불가
            return {}

        # 모든 영화(행)와, 사용자가 좋아한 영화(열들) 간의 코사인 유사도 행렬 계산
        # sims.shape = (num_movies, num_liked)
        sims = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix[indices])

        # 가중치 준비(없다면 동일 가중치)
        if weights is None:
            weights = [1.0] * len(indices)
        # 가중치 정규화(합이 1이 되도록)하여 가중합을 계산할 준비
        w = np.array(weights) / (np.sum(weights) + 1e-12)

        # 각 후보 영화에 대해: liked 영화들과의 유사도를 가중 평균
        # scores.shape = (num_movies,)
        scores = sims @ w

        # 영화ID → 스코어 사전으로 변환
        result = {mid: float(scores[i]) for i, mid in enumerate(self.movie_ids)}

        # 이미 사용자가 좋아한(평가한) 영화는 추천 후보에서 제거
        for mid in liked_movie_ids:
            result.pop(mid, None)

        return result

# 전역 싱글턴식 추천기(간단 캐시)
_recommender = ContentRecommender()

def ensure_model(db: Session):
    # 간단한 Lazy-fit 정책:
    # - 최초 호출이거나, 영화 수가 바뀐 경우에만 다시 fit 수행
    movies = db.query(Movie).all()
    if (_recommender.tfidf_matrix is None) or (len(_recommender.movie_ids) != len(movies)):
        _recommender.fit(movies)
    return _recommender

def recommend_for_user(db: Session, user_id: int, limit: int = 12) -> List[Tuple[Movie, float]]:
    # 1) 대상 사용자의 모든 평점 조회
    ratings = db.query(Rating).filter(Rating.user_id == user_id).all()

    if not ratings:
        # Cold-start(해당 유저의 평점이 없는 경우): 인기(popularity) 상위 영화로 대체
        movies = db.query(Movie).order_by(Movie.popularity.desc()).limit(limit).all()
        return [(m, float(m.popularity or 0.0)) for m in movies]

    # 2) 평점이 높은 순으로 정렬 후 상위 N(최대 10개)만 사용 → 노이즈 완화
    ratings_sorted = sorted(ratings, key=lambda r: r.rating, reverse=True)
    top = ratings_sorted[: min(10, len(ratings_sorted))]
    liked_ids = [r.movie_id for r in top]   # 상위 평점 영화들의 ID 목록
    weights = [r.rating for r in top]       # 평점을 가중치로 사용

    # 3) TF-IDF 기반 콘텐츠 추천 점수 계산
    rec = ensure_model(db)                  # 필요 시 모델 fit
    score_map = rec.scores_for_movies(liked_ids, weights)  # {movie_id: score}

    # 4) 점수가 너무 희소하거나 계산에 실패했다면 인기 점수로 대체(fallback)
    if not score_map:
        movies = db.query(Movie).order_by(Movie.popularity.desc()).limit(limit).all()
        return [(m, float(m.popularity or 0.0)) for m in movies]

    # 5) 콘텐츠 점수에 소량의 인기 priors를 블렌딩(0.9*콘텐츠 + 0.1*인기)
    #    - 극단값/스파스 문제를 완화하고, 대중성이 높은 아이템을 약간 끌어올림
    pop_map = {m.id: (m.popularity or 0.0) for m in db.query(Movie).all()}
    blended = [(mid, s * 0.9 + 0.1 * pop_map.get(mid, 0.0)) for mid, s in score_map.items()]
    blended.sort(key=lambda x: x[1], reverse=True)  # 점수 내림차순 정렬

    # 6) 상위 limit개의 movie_id에 해당하는 Movie ORM 객체를 한 번에 조회하여 매핑
    id_to_movie = {
        m.id: m
        for m in db.query(Movie).filter(Movie.id.in_([mid for mid,_ in blended[:limit]])).all()
    }

    # 7) (Movie, score) 튜플 리스트로 최종 반환 (limit개까지만)
    out: List[Tuple[Movie,float]] = [
        (id_to_movie[mid], float(score))
        for mid, score in blended
        if mid in id_to_movie
    ][:limit]
    return out
