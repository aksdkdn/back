from pydantic import BaseModel
from typing import Optional, List

class MovieOut(BaseModel):
    id: int
    title: str
    genres: Optional[str] = None
    overview: Optional[str] = None
    year: Optional[int] = None
    poster_url: Optional[str] = None
    popularity: Optional[float] = 0

    class Config:
        from_attributes = True

class UserOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class RatingIn(BaseModel):
    movie_id: int
    rating: float

class RatingOut(BaseModel):
    user_id: int
    movie_id: int
    rating: float

    class Config:
        from_attributes = True

class RecommendationOut(BaseModel):
    movie: MovieOut
    score: float
