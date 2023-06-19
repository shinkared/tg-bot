from connect import connect
import math

users = {}


class Query:

    @staticmethod
    def top_10(user_id):
        return connect.get_data(f"""SELECT  f.title, f.small_image, f.id, f.tg_small
        FROM scores s
        JOIN films f ON s.film_id = f.id
        WHERE s.user_id = {user_id} AND s.score >= 0 
        ORDER BY s.score DESC
        LIMIT 10;""", 2)

    @staticmethod
    def get_film(user_id):
        film = connect.get_data(f"""SELECT f.*
    FROM films f
    JOIN users u ON f.year >= u.prefs_low and f.year <= u.prefs_hi
    WHERE u.id = {user_id} and f.id NOT IN (
        SELECT film_id 
        FROM scores
        WHERE user_id = {user_id} AND score < 0
    ) and f.id<=u.prefs_n
    ORDER BY random()
    LIMIT 2;""", mode=2)
        return film

    @staticmethod
    def get_n(user_id):
        return connect.get_data(f"""select rated_films from users
    where id = {user_id};""", 1)

    @staticmethod
    def update_n(user_id, k):
        connect.get_data(f"""UPDATE users u
    SET rated_films = u.rated_films + {k}
    where u.id = {user_id};""", 0)
        if user_id in users:
            users[user_id] += k
        else:
            users[user_id] = Query.get_n(user_id)[0]

    @staticmethod
    def get_film_10(user_id):
        return connect.get_data(f"""SELECT f.*
    FROM (
      (
        SELECT f.*
        FROM films f
        JOIN users u ON f.year >= u.prefs_low AND f.year <= u.prefs_hi
        WHERE u.id = {user_id} AND f.id NOT IN (
          SELECT film_id 
          FROM scores
          WHERE user_id = {user_id} AND score < 0
        ) AND f.id <= u.prefs_n
        ORDER BY random()
        LIMIT 4
      )
      UNION
      (select f.* 
       from (
        SELECT f.*
        FROM films f
        JOIN scores s ON f.id = s.film_id and s.user_id = {user_id}
        WHERE s.score > 0
        ORDER BY s.score DESC
        LIMIT 20
    
      ) f 
       order by random()
        limit 2)
    ) f
    limit 2;""", 2)

    @staticmethod
    def get_s_film(idd):
        return connect.get_data(f"""select * from films where id = {idd};""", 1)

    @staticmethod
    def get_search(s):
        s = s.replace(" ", "_")
        return connect.get_data(f"""SELECT f.id, f.title, f.year
    FROM films f
    WHERE to_tsvector('russian', f.title) @@ to_tsquery('russian', '{s}')
    ORDER BY ts_rank(to_tsvector('russian', f.title), to_tsquery('russian', '{s}')) DESC
    LIMIT 5;""", 2)

    @staticmethod
    def get_big_image(idd):
        return connect.get_data(f"""SELECT big_image FROM films where id={str(idd)};""", 1)[0]

    @staticmethod
    def calculate_elo(old_rating, opponent_rating, result, k_factor=32):
        expected_result = 1 / (1 + math.pow(10, (opponent_rating - old_rating) / 400))
        new_rating = old_rating + k_factor * (result - expected_result)
        return new_rating

    @staticmethod
    def update_scores(idd, a, b):
        a_score = (connect.get_data(f"""SELECT COALESCE(
        (SELECT score FROM scores WHERE film_id = {a} AND user_id = {idd}),
        1000
    ) AS score;""", 1)[0])
        b_score = (connect.get_data(f"""SELECT COALESCE(
            (SELECT score FROM scores WHERE film_id = {b} AND user_id = {idd}),
            1000
        ) AS score;""", 1)[0])
        Query.update_n(idd, 1)
        a_new_score = Query.calculate_elo(a_score, b_score, 1)
        b_new_score = Query.calculate_elo(b_score, a_score, 0)
        connect.get_data(f"""INSERT INTO scores (
        user_id, film_id, score) VALUES (
        {idd}, {a}, {a_new_score}::real)
        ON CONFLICT (film_id, user_id) DO UPDATE
        SET score = {a_new_score};""", 0)
        connect.get_data(f"""INSERT INTO scores (
        user_id, film_id, score) VALUES (
        {idd}, {b}, {b_new_score}::real)
        ON CONFLICT (film_id, user_id) DO UPDATE
        SET score = {b_new_score};""", 0)

    @staticmethod
    def update_nw(idd, a):
        connect.get_data(f"""INSERT INTO scores (
    user_id, film_id, score) VALUES (
    {idd}, {a}, -1::real)
    ON CONFLICT (film_id, user_id) DO UPDATE
    SET score = -1;""", 0)

    @staticmethod
    def update_image(n, idd, img):
        text = ['tg_small', 'tg_medium', 'tg_big']
        connect.get_data(f"""UPDATE films
    SET {text[n]} = '{img}'
    WHERE id = {idd};""", 0)

    @staticmethod
    def get_settings_n(user_id):
        return connect.get_data(f"""SELECT count(f.id)
FROM films f
JOIN users u ON f.year >= u.prefs_low and f.year <= u.prefs_hi
WHERE u.id = {user_id} and f.id NOT IN (
    SELECT film_id 
    FROM scores
    WHERE user_id = {user_id} AND score < 0
) and f.id<=u.prefs_n;""", mode=1)[0]

    @staticmethod
    def update_settings_hi(get, user_id):
        connect.get_data(f"""UPDATE users
        SET prefs_hi = {get}
        WHERE id = {user_id};""", 0)

    @staticmethod
    def update_settings_low(get, user_id):
        connect.get_data(f"""UPDATE users
        SET prefs_low = {get}
        WHERE id = {user_id};""", 0)

    @staticmethod
    def get_user_by_id(user_id):
        return connect.get_data(f"""select * from users
where id ={user_id}""", mode=1)

    @staticmethod
    def register_user(user_id):
        connect.get_data(f"""INSERT INTO users (id, prefs_low, prefs_hi)
        SELECT {user_id}, 1980, 2023
        WHERE NOT EXISTS (
          SELECT 1 FROM users WHERE id = {user_id}
        );""", 0)

    @staticmethod
    def get_settings(user_id):
        return connect.get_data(f"""select prefs_n
from users where id ={user_id}""", 1)[0]

    @staticmethod
    def update_settings(user_id, v):
        connect.get_data(f"""UPDATE users
                SET prefs_n = {v}
                WHERE id = {user_id};""", 0)
