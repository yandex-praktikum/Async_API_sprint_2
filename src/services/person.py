from functools import lru_cache
from typing import Optional, Union
from uuid import UUID

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film
from models.person import Person, PersonDetail


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: UUID) -> Optional[PersonDetail]:
        """
        Получить персону по id
        """
        person = await self._get_from_elastic(person_id)
        if not person:
            return None
        person_detail = PersonDetail.parse_obj(person)
        from_: int = 0
        page_size: int = 20
        while film_list := await self.get_person_films(person.uuid, from_, size=page_size):
            for film in film_list:
                for role in film.get_roles(person.uuid):
                    getattr(person_detail.roles, role).append(film.uuid)
            from_ += page_size
        return person_detail

    async def search_person(self, query, from_, size) -> list[Person]:
        """
        Поиск по персонам
        :param query: Строка которую ищем
        :param from_: С какой записи выдавать результат поиска
        :param size: Размер списка
        :return: Список Person
        """
        es_query = {
            'from': from_,
            'size': size,
            'query': {
                'match': {
                    'full_name': query
                }
            }
        }

        persons = await self._get_all_from_elastic('persons', Person, es_query)
        return persons

    async def get_person_films(self, person_id: UUID, from_: int, size: int) -> list[Film]:
        """
        Поиск всех фильмов связанных с персоной
        :param person_id: id персоны
        :param from_: С какой записи выдавать результат
        :param size: Размер списка
        :return: Список Film
        """
        persons_query: list = []
        for role in ('actors', 'writers', 'directors'):
            nested_query: dict = {'nested': {
                'path': role,
                'query': {
                    'match': {
                        f'{role}.id': person_id
                    }
                }
            }}
            persons_query.append(nested_query)
        es_query: dict = {
            'from': from_,
            'size': size,
            'query': {
                'bool': {
                    'should': persons_query
                }
            }}

        films = await self._get_all_from_elastic('movies', Film, es_query)
        return films

    async def _get_from_elastic(self, person_id: UUID) -> Optional[Person]:
        try:
            data = await self.elastic.get('persons', person_id)
        except NotFoundError:
            return None
        return Person(**data['_source'])

    async def _get_all_from_elastic(self, index: str,
                                    model: type[Union[Person, Film]],
                                    body: dict) -> Optional[list[Union[Person, Film]]]:
        data = await self.elastic.search(index=index, body=body)
        return [
            model(**item['_source'])
            for item in data.get('hits', {}).get('hits', [])
        ]


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)
