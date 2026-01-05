USE moviesdb;

INSERT INTO users (name) VALUES
  ('Alice'), ('Bob'), ('Charlie'), ('Dana');

INSERT INTO movies (title, genres, overview, year, poster_url, popularity) VALUES
  ('Inception', 'Action, Sci-Fi, Thriller', 'A thief who steals corporate secrets through dream-sharing technology is given a task of planting an idea into the mind of a CEO.', 2010, 'https://image.tmdb.org/t/p/w500/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg', 98.0),
  ('Interstellar', 'Adventure, Drama, Sci-Fi', 'A team travels through a wormhole in space in an attempt to ensure humanity's survival.', 2014, 'https://image.tmdb.org/t/p/w500/rAiYTfKGqDCRIIqo664sY9XZIvQ.jpg', 95.0),
  ('The Dark Knight', 'Action, Crime, Drama', 'Batman faces the Joker, a criminal mastermind who plunges Gotham into anarchy.', 2008, 'https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg', 99.0),
  ('La La Land', 'Comedy, Drama, Music, Romance', 'A jazz pianist and an aspiring actress fall in love while attempting to reconcile their aspirations for the future.', 2016, 'https://image.tmdb.org/t/p/w500/uDO8zWDhfWwoFdKS4fzkUJt0Rf0.jpg', 90.0),
  ('The Matrix', 'Action, Sci-Fi', 'A hacker learns the true nature of his reality and his role in the war against its controllers.', 1999, 'https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg', 97.0),
  ('Spirited Away', 'Animation, Family, Fantasy', 'A girl wanders into a world ruled by gods, witches, and spirits.', 2001, 'https://image.tmdb.org/t/p/w500/dL11DBPcRhWWnJcFXl9A07MrqTI.jpg', 93.0),
  ('Parasite', 'Comedy, Drama, Thriller', 'Greed and class discrimination threaten the newly formed symbiotic relationship between the wealthy and destitute.', 2019, 'https://image.tmdb.org/t/p/w500/7IiTTgloJzvGI1TAYymCfbfl3vT.jpg', 96.0),
  ('Your Name', 'Animation, Drama, Romance', 'Two teenagers share a profound connection upon discovering they are swapping bodies.', 2016, 'https://image.tmdb.org/t/p/w500/q719jXXEzOoYaps6babgKnONONX.jpg', 91.0),
  ('The Godfather', 'Crime, Drama', 'An organized crime dynasty's aging patriarch transfers control of his clandestine empire to his reluctant son.', 1972, 'https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg', 99.0),
  ('Mad Max: Fury Road', 'Action, Adventure, Sci-Fi', 'In a post-apocalyptic wasteland, Max teams up with a mysterious woman to escape a tyrant.', 2015, 'https://image.tmdb.org/t/p/w500/8tZYtuWezp8JbcsvHYO0O46tFbo.jpg', 89.0);

-- Seed a few ratings
INSERT INTO ratings (user_id, movie_id, rating) VALUES
  (1, 1, 5), (1, 2, 4.5), (1, 5, 5),
  (2, 3, 5), (2, 1, 4), (2, 10, 4.5),
  (3, 4, 5), (3, 6, 4.5), (3, 8, 4),
  (4, 7, 5), (4, 2, 4), (4, 9, 4.5);
