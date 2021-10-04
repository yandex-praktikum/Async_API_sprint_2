import logging
import time
import typing
from datetime import datetime

import backoff
import psycopg2
from psycopg2._psycopg import connection as connetction_
from psycopg2.extras import DictCursor

from models import Movie, Person, Genre, BasePerson

BATCH_SIZE = 100


def pg_backoff():
    return backoff.on_exception(backoff.expo, psycopg2.OperationalError)


class PgCon:
    """Менеджер контекста для отслеживания состояния соединения"""

    def __init__(self,
                 dbname: str,
                 host: str = '127.0.0.1',
                 port: int = 5432,
                 user: str = 'postgres',
                 password: str = '',
                 options: str = None,
                 query_delay: float = 0.1):
        self.con_param = {
            'dbname': dbname,
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'options': options,
            'cursor_factory': DictCursor,
        }
        self.con: typing.Optional[connetction_] = None
        self.query_delay = query_delay

    def connect(self):
        self.con = psycopg2.connect(**self.con_param)
        self.con.readonly = True

    def query(self, sql: str, values: tuple) -> list:
        if self.con is None or self.con.closed:
            self.connect()

        with self.con.cursor() as cur:
            logging.debug('Sleep %ss', self.query_delay)
            time.sleep(self.query_delay)
            logging.debug('QUERY: %s, %s', sql, values)
            cur.execute(sql, values)
            for row in iter(cur.fetchone, None):
                yield row

    @pg_backoff()
    def get_movies(self, state: datetime) -> list[Movie]:
        sql: str = f'''
            SELECT id, title, description, rating, updated_at FROM movies_admin_filmwork
            WHERE updated_at > %s
            ORDER BY updated_at LIMIT {BATCH_SIZE};
            '''
        return [Movie.from_dict(movie) for movie in self.query(sql, (state,))]

    @pg_backoff()
    def get_persons(self, movie_id: str) -> list[Person]:
        sql: str = '''
            SELECT p.id, p.full_name, pm.role FROM movies_admin_person p
            JOIN movies_admin_personfilmwork pm ON pm.person_id=p.id
            JOIN movies_admin_filmwork m ON m.id=pm.film_work_id WHERE m.id=%s;
            '''
        return [Person.from_dict(person) for person in self.query(sql, (movie_id,))]

    @pg_backoff()
    def get_all_persons(self, state: datetime) -> list[BasePerson]:
        sql: str = f'''
            SELECT id, full_name, updated_at FROM movies_admin_person
            WHERE updated_at > %s
            ORDER BY updated_at LIMIT {BATCH_SIZE};
            '''
        return [BasePerson(**person) for person in self.query(sql, (state,))]

    @pg_backoff()
    def get_all_genres(self, state: datetime) -> list[Genre]:
        sql: str = f'''
            SELECT id, name, updated_at FROM movies_admin_genre
            WHERE updated_at > %s
            ORDER BY updated_at LIMIT {BATCH_SIZE};
            '''
        return [Genre(**genre) for genre in self.query(sql, (state,))]

    @pg_backoff()
    def get_genres(self, movie_id: str) -> list[Genre]:
        sql: str = '''
            SELECT g.id, g.name, g.updated_at FROM movies_admin_genre g
            JOIN movies_admin_genrefilmwork gm ON gm.genre_id=g.id
            JOIN movies_admin_filmwork m ON m.id=gm.film_work_id WHERE m.id=%s;
            '''
        return [Genre(**genre) for genre in self.query(sql, (movie_id,))]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.con is not None:
            self.con.close()
