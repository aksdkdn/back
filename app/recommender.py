from __future__ import annotations
from typing import List, Tuple, Dict
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from .models import Movie, Rating

class ContentRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            max_features=20000,
            ngram_range=(1,2)
        )
        self.movie_ids: List[int] = []
        self.tfidf_matrix = None

    def _build_corpus_row(self, m: Movie) -> str:
        fields = [m.title or "", m.genres or "", (m.overview or "")]
        return " ".join(fields)

    def fit(self, movies: List[Movie]):
        self.movie_ids = [m.id for m in movies]
        corpus = [self._build_corpus_row(m) for m in movies]
        if len(corpus) == 0:
            self.tfidf_matrix = None
        else:
            self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def scores_for_movies(self, liked_movie_ids: List[int], weights: List[float]|None=None) -> Dict[int, float]:
        if self.tfidf_matrix is None or not self.movie_ids:
            return {}
        id_to_index = {mid: idx for idx, mid in enumerate(self.movie_ids)}
        indices = [id_to_index[mid] for mid in liked_movie_ids if mid in id_to_index]
        if not indices:
            return {}
        sims = cosine_similarity(self.tfidf_matrix, self.tfidf_matrix[indices])
        if weights is None:
            weights = [1.0] * len(indices)
        w = np.array(weights) / (np.sum(weights) + 1e-12)
        scores = sims @ w
        result = {mid: float(scores[i]) for i, mid in enumerate(self.movie_ids)}
        for mid in liked_movie_ids:
            result.pop(mid, None)  # remove already liked
        return result

_recommender = ContentRecommender()

def ensure_model(db: Session):
    # Lazy fit each time if movie count changed (simple approach)
    movies = db.query(Movie).all()
    if (_recommender.tfidf_matrix is None) or (len(_recommender.movie_ids) != len(movies)):
        _recommender.fit(movies)
    return _recommender

def recommend_for_user(db: Session, user_id: int, limit: int = 12) -> List[Tuple[Movie, float]]:
    # 1) get user's top-rated movies
    ratings = db.query(Rating).filter(Rating.user_id == user_id).all()
    if not ratings:
        # cold-start: top popular
        movies = db.query(Movie).order_by(Movie.popularity.desc()).limit(limit).all()
        return [(m, float(m.popularity or 0.0)) for m in movies]

    ratings_sorted = sorted(ratings, key=lambda r: r.rating, reverse=True)
    top = ratings_sorted[: min(10, len(ratings_sorted))]
    liked_ids = [r.movie_id for r in top]
    weights = [r.rating for r in top]

    rec = ensure_model(db)
    score_map = rec.scores_for_movies(liked_ids, weights)

    # Fallback: if too sparse, blend with popularity
    if not score_map:
        movies = db.query(Movie).order_by(Movie.popularity.desc()).limit(limit).all()
        return [(m, float(m.popularity or 0.0)) for m in movies]

    # Rank by score (blend small popularity prior)
    pop_map = {m.id: (m.popularity or 0.0) for m in db.query(Movie).all()}
    blended = [(mid, s * 0.9 + 0.1 * pop_map.get(mid, 0.0)) for mid, s in score_map.items()]
    blended.sort(key=lambda x: x[1], reverse=True)

    id_to_movie = {m.id: m for m in db.query(Movie).filter(Movie.id.in_([mid for mid,_ in blended[:limit]])).all()}
    out: List[Tuple[Movie,float]] = [(id_to_movie[mid], float(score)) for mid, score in blended if mid in id_to_movie][:limit]
    return out
