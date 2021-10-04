#!/usr/bin/env python3

import functools
import json
import logging
from dataclasses import asdict

import backoff
import requests
from config import config

from pgcon import PgCon
from state import State

logging.basicConfig(level=config['main']['log_level'] * 10)
if config['main']['log_to_file']:
    logging.basicConfig(filename=config['main']['log_filename'])


class ETLException(Exception):
    pass


class EsAddDocErrorException(ETLException):
    pass


def coroutine(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        fn = func(*args, **kwargs)
        next(fn)
        return fn

    return inner


@backoff.on_exception(backoff.expo,
                      requests.exceptions.RequestException)
def load_to_es(data):
    url = config['elasticsearch']['url'] + '/_bulk'
    headers: dict = {
        'Content-Type': 'application/json'
    }
    req = requests.post(url, data=data, headers=headers)
    req_dict = req.json()
    logging.debug(req_dict)
    if req_dict['errors']:
        logging.error('Error add doc to ES')
        raise EsAddDocErrorException('Error add doc to ES')


@coroutine
def es_load():
    def create_cmd(id_, index_name):
        dict_ = {
            'index': {
                '_index': index_name,
                '_id': id_,
            }
        }
        return json.dumps(dict_)

    while index_data := (yield):
        logging.debug('======= Loop ES =======')
        rows, index_name = index_data
        logging.debug('Index name: %s', index_name)
        data = '\n'.join(
            create_cmd(row['id'], index_name) + '\n' + json.dumps(row)
            for row in rows
        ) + '\n'
        logging.debug(data)
        load_to_es(data)


@coroutine
def movies_transform(target):
    """Подготовка данных"""
    while movies := (yield):
        logging.debug('======= Loop movies transform =======')
        movies_list: list = []
        for movie in movies:
            movie_dict = asdict(movie)
            del movie_dict['updated_at']
            movies_list.append(movie_dict)
        target.send((movies_list, 'movies'))


@coroutine
def transform(target):
    while transform_data := (yield):
        rows, index_name = transform_data
        logging.debug('======= Loop genres/person transform =======')
        row_list = (row.to_dict() for row in rows)
        target.send((row_list, index_name))


def pg_extract(movies_transformer, transformer):
    """
    Забираем данные из postgresql

    При обновлении любых связанных строк в любых таблицах, обновляется поле updated_at в таблице filmwork. Поэтому
    итерируемся сразу по таблице filmwork и собираем все связи.
    """
    state = State(config['main']['state_filename'])
    logging.debug('State: %s', state._state)
    with PgCon(dbname=config['postgresql']['dbname'],
               host=config['postgresql']['host'],
               port=config['postgresql']['port'],
               user=config['postgresql']['user'],
               password=config['postgresql']['password'],
               options=config['postgresql']['options'],
               query_delay=config['postgresql']['query_delay'],
               ) as con:
        while movies := con.get_movies(state.movies):
            logging.info('Get movies from %s to %s', movies[0].updated_at, movies[-1].updated_at)
            for movie in movies:
                movie.genre = [genre.name for genre in con.get_genres(movie.id)]
                movie.genres = [genre.to_dict() for genre in con.get_genres(movie.id)]
                movie.fill_persons(con.get_persons(movie.id))
            movies_transformer.send(movies)
            state.set('movies', movie.updated_at)

        while persons := con.get_all_persons(state.persons):
            logging.info('Get persons from %s to %s', persons[0].updated_at, persons[-1].updated_at)
            transformer.send((persons, 'persons'))
            logging.debug(state.persons)
            logging.debug(persons[-1].updated_at)
            state.set('persons', persons[-1].updated_at)

        while genres := con.get_all_genres(state.genres):
            logging.info('Get genres from %s to %s', genres[0].updated_at, genres[-1].updated_at)
            transformer.send((genres, 'genres'))
            state.set('genres', genres[-1].updated_at)


def main():
    es_loader = es_load()
    movies_transformer = movies_transform(es_loader)
    transformer = transform(es_loader)
    pg_extract(movies_transformer, transformer)


if __name__ == '__main__':
    main()
