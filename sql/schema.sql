-- ------------------------------------------------------------
-- 스키마 초기화 및 테이블 생성 스크립트 (moviesdb)
-- - 문자셋: utf8mb4 (이모지 포함 전체 유니코드 지원)
-- - 엔진: InnoDB (트랜잭션/외래키 지원)
-- - 테이블: movies, users, ratings(교차/평점)
-- ------------------------------------------------------------

-- 1) 데이터베이스가 없으면 생성 (문자셋: utf8mb4)
CREATE DATABASE IF NOT EXISTS moviesdb DEFAULT CHARACTER SET utf8mb4;

-- 2) 이후 쿼리의 대상 DB 선택
USE moviesdb;

-- ------------------------------------------------------------
-- 재생성 대비: 기존 테이블을 의존성 역순(자식→부모)으로 드롭
-- ratings → movies/users 순으로 제거
-- ------------------------------------------------------------
DROP TABLE IF EXISTS ratings;
DROP TABLE IF EXISTS movies;
DROP TABLE IF EXISTS users;

-- ------------------------------------------------------------
-- movies: 영화 메타데이터 테이블
--  - popularity: 추천/정렬에 활용 가능한 인기 점수(기본 0)
--  - overview: 긴 설명(텍스트)
--  - poster_url: 포스터 이미지 링크
-- ------------------------------------------------------------
CREATE TABLE movies (
  id INT AUTO_INCREMENT PRIMARY KEY,  -- PK, 자동 증가
  title VARCHAR(255) NOT NULL,        -- 영화 제목 (필수)
  genres VARCHAR(255) DEFAULT NULL,   -- 장르(쉼표 구분 문자열 등)
  overview TEXT,                      -- 영화 개요/설명(긴 텍스트)
  year INT DEFAULT NULL,              -- 개봉 연도
  poster_url VARCHAR(500) DEFAULT NULL, -- 포스터 이미지 URL
  popularity FLOAT DEFAULT 0          -- 인기 점수(정렬/콜드스타트용)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- users: 사용자 테이블
--  - 최소 컬럼: id, name (확장: email, created_at 등)
-- ------------------------------------------------------------
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,  -- PK, 자동 증가
  name VARCHAR(100) NOT NULL          -- 사용자 표시 이름
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- ratings: 사용자-영화 평점 교차 테이블 (N:M 관계를 평점으로 모델링)
--  - 복합 PK: (user_id, movie_id) → 동일 사용자/영화 중복 평점 방지
--  - CHECK 제약: rating은 0~5 범위 (MySQL 8.0 이상에서 유효)
--  - ON DELETE CASCADE: 부모 삭제 시 관련 평점 자동 삭제(고아 레코드 방지)
-- ------------------------------------------------------------
CREATE TABLE ratings (
  user_id INT NOT NULL,   -- FK → users.id
  movie_id INT NOT NULL,  -- FK → movies.id
  rating FLOAT NOT NULL CHECK (rating >= 0 AND rating <= 5), -- 평점 범위 제약(0~5)

  PRIMARY KEY (user_id, movie_id), -- 복합 기본키로 유니크 보장

  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ------------------------------------------------------------
-- [추가 팁]
-- 1) 인덱스: 조회 패턴에 따라 ratings(user_id), ratings(movie_id) 보조 인덱스가
--    이미 PK로 커버되지만, 별도 쿼리 패턴(예: movie_id 단일 검색)이 잦으면
--    추가 인덱스 고려 가능.
-- 2) 장르 정규화: genres를 문자열로 두면 간단하지만, 장르 필터/통계가 많으면
--    genres 테이블 + movie_genres(교차)로 정규화 권장.
-- 3) 타임스탬프: 운영에서는 created_at/updated_at(ON UPDATE CURRENT_TIMESTAMP) 등을
--    추가해 변경 추적을 쉽게 만들 수 있음.
-- 4) 기본 데이터: 초기 사용자/영화/평점 시드가 필요하면 별도 seed.sql에 INSERT 작성 권장.
-- ------------------------------------------------------------
