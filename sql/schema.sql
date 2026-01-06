-- Create DB and tables
CREATE DATABASE IF NOT EXISTS moviesdb DEFAULT CHARACTER SET utf8mb4;

USE moviesdb;

DROP TABLE IF EXISTS ratings;

DROP TABLE IF EXISTS movies;

DROP TABLE IF EXISTS users;

CREATE TABLE movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    genres VARCHAR(255) DEFAULT NULL,
    overview TEXT,
    year INT DEFAULT NULL,
    poster_url VARCHAR(500) DEFAULT NULL,
    popularity FLOAT DEFAULT 0
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE ratings (
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    rating FLOAT NOT NULL CHECK (
        rating >= 0
        AND rating <= 5
    ),
    PRIMARY KEY (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;