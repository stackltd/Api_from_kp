import datetime
import sqlite3
import json
from dataclasses import dataclass
from typing import Optional, Union


CREATE_DATABASE_QUERY = """
CREATE TABLE IF NOT EXISTS 'short' (
    id INTEGER PRIMARY KEY,
    id_movie INTEGER,
    name VARCHAR(200),
    countries VARCHAR(200),
    year INTEGER,
    genres VARCHAR(200),
    votes INTEGER
);

CREATE TABLE IF NOT EXISTS 'long' (
    id INTEGER PRIMARY KEY,
    id_movie INTEGER,
    dict_info VARCHAR(200)
);
"""


@dataclass
class Short:
    id_movie: int
    name: str
    countries: str
    year: int
    genres: str
    votes: int
    id: Optional[int] = None

    def __getitem__(self, item: str) -> Union[int, str]:
        return getattr(self, item)


def _get_author_obj_from_row(row: tuple) -> Short:
    return Short(id=row[0], id_movie=row[1], name=row[2], countries=row[3], year=row[4], genres=row[5], votes=row[6])


def db_create():
    with sqlite3.connect('kino.db') as conn:
        cursor = conn.cursor()
        cursor.executescript(CREATE_DATABASE_QUERY)


def get_field(field="*", genres=("", )):
    with sqlite3.connect('kino.db') as conn:
        cursor = conn.cursor()
        sub_comm = ' AND '.join([f"genres LIKE '%{x}%'" for x in genres])
        result = cursor.execute(f"""SELECT {field} FROM short WHERE {sub_comm}""").fetchall()
        return result

def get_info(genres=("", )):
    with sqlite3.connect('kino.db') as conn:
        cursor = conn.cursor()
        sub_comm = ' AND '.join([f"genres LIKE '%{x}%'" for x in genres])
        result = cursor.execute(f"""SELECT * FROM short WHERE {sub_comm}""").fetchall()
        return [_get_author_obj_from_row(row) for row in result]

def get_long_info(id_movie):
    with sqlite3.connect('kino.db') as conn:
        cursor = conn.cursor()
        result = cursor.execute(f"""SELECT * FROM long WHERE id_movie = ?""", (id_movie, )).fetchone()
        return json.loads(result[2]) if result else {}

def get_all_mov_id():
    with sqlite3.connect('kino.db') as conn:
        cursor = conn.cursor()
        result = cursor.execute(f"""SELECT id_movie FROM short""").fetchall()
        return {str(x[0]) for x in result}


def json_to_sql_short(json_info):
    params = []

    for id_movie in json_info:
        list_of_dict = json_info[id_movie]["Общая информация о фильме"]

        name = str(list_of_dict["name"])
        countries = ', '.join(country['name'] for country in list_of_dict['countries']) if list_of_dict['countries'] else "неизвестно"
        year = str(list_of_dict['year']) if list_of_dict['year'] else '0'
        genres = ', '.join(country['name'] for country in list_of_dict['genres']) if list_of_dict['genres'] else "неизвестно"
        votes = str(list_of_dict["votes"].get('kp', 0))

        params.append((id_movie, name, countries, year, genres, votes))

    with sqlite3.connect('kino.db') as conn:
        cursor = conn.cursor()
        cursor.executemany(
            f"""INSERT INTO short (id_movie, name, countries, year, genres, votes) VALUES(?, ?, ?, ?, ?, ?)""", params)


def json_to_sql_long(json_info):
    params = [(id_movie, json.dumps(json_info[id_movie])) for id_movie in json_info]

    with sqlite3.connect('kino.db') as conn:
        cursor = conn.cursor()
        cursor.executemany(
            f"""INSERT INTO long (id_movie, dict_info) VALUES(?, ?)""", params)

def json_to_sql(json_info):
    json_to_sql_short(json_info)
    json_to_sql_long(json_info)


def delete(id_movie):
    query = f"""DELETE FROM short WHERE id_movie = {id_movie};
                DELETE FROM long WHERE id_movie = {id_movie};"""
    with sqlite3.connect('kino.db') as conn:
        cursor = conn.cursor()
        cursor.executescript(query)

if __name__ == "__main__":
    db_create()

