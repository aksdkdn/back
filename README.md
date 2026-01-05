# FastAPI Movie Recommender (MySQL)
# ------------------------------------------------------------
# 🎬 FastAPI + SQLAlchemy + MySQL + scikit-learn 기반 영화 추천 시스템
# - 콘텐츠 기반 추천(Content-based Filtering)
# - React 프론트엔드와 연동 가능한 RESTful API 서버
# - Python 3.10+ / FastAPI 0.110+ / MySQL 8.0 이상 권장
# ------------------------------------------------------------


## 1) Setup
```bash
# 백엔드 프로젝트 디렉토리로 이동
cd backend_fastapi

# (1) 가상환경 생성
python -m venv venv

# (2) 가상환경 활성화
# - macOS/Linux: source venv/bin/activate
# - Windows PowerShell: venv\Scripts\activate
source venv/bin/activate  # Windows: venv\Scripts\activate

# (3) 패키지 설치 (requirements.txt 기준)
pip install -r requirements.txt

# (4) 환경설정 템플릿 복사 후 실제 값 편집
# - .env.example → .env로 복사 후 DB 계정 등 수정
cp .env.example .env  # then edit values

💡 설명:
.env에는 DB_USER, DB_PASSWORD, DB_HOST 등이 들어 있으며,
app/db.py에서 자동으로 읽어 MySQL 접속 URL을 구성합니다.
requirements.txt에는 fastapi, uvicorn, sqlalchemy, pymysql, scikit-learn 등이 포함됩니다.
가상환경은 프로젝트별 의존성 충돌 방지를 위해 필수로 설정합니다.



## 2) MySQL
Create DB + tables and seed sample data:
# (1) 데이터베이스 및 테이블 생성
mysql -u root -p < sql/schema.sql

# (2) 샘플 영화/사용자/평점 데이터 삽입 (seed.sql 사용)
mysql -u root -p moviesdb < sql/seed.sql

💡 설명:

schema.sql은 DB 스키마 정의 파일로, movies, users, ratings 테이블을 생성합니다.

seed.sql은 초기 데이터 삽입용 SQL (예: 영화 50개, 사용자 10명, 평점 랜덤 0~5).

moviesdb는 .env에 정의된 DB_NAME과 동일해야 합니다.

root 권한으로 실행 후, FastAPI 애플리케이션은 일반 계정(fastapiid)으로 접속합니다.






## 3) Run
# FastAPI 개발 서버 실행

uvicorn app.main:app --reload --port 8000

💡 설명:

app.main:app은 app 패키지 내부의 main.py에서 FastAPI() 인스턴스를 의미합니다.

--reload: 코드 변경 시 자동 재시작 (개발용 옵션)

실행 후 접속 주소: http://127.0.0.1:8000

OpenAPI 문서 확인: http://127.0.0.1:8000/docs


## 4) API
GET /api/movies — list movies (paged)
👉 등록된 영화 목록을 페이지 단위로 반환. (limit/offset 사용)

GET /api/users — list users
👉 전체 사용자 목록 반환.

GET /api/users/{user_id}/ratings — a user's ratings
👉 특정 사용자의 영화 평점 기록 조회.

POST /api/users/{user_id}/ratings — add/update a rating { "movie_id": 1, "rating": 4.5 }
👉 특정 사용자가 영화 평점을 새로 등록하거나 수정.

이미 존재하면 업데이트

없으면 새 레코드 생성

rating 범위: 0.0 ~ 5.0

GET /api/recommend?user_id=1&limit=12 — personalized recommendations
👉 사용자 ID 기반 개인화 추천 목록 반환.

limit: 반환 개수 (기본 12, .env의 DEFAULT_LIMIT 참고)

💡 설명:

모든 /api/... 엔드포인트는 CORS 허용(allow_origins=["*"])되어 있으므로
React/프론트엔드에서 자유롭게 호출 가능.

응답 데이터는 schemas.py의 Pydantic 모델(MovieOut, UserOut, RecommendationOut)로 직렬화됩니다.