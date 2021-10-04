from collections import defaultdict
from functools import lru_cache
from typing import Optional, Union

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import NotFoundError
from fastapi import Depends
from pydantic import parse_obj_as

from db.elastic import get_elastic
from db.redis import get_redis
from models.film import Film

ORDER_FIELDS = ('id', 'rating')


class FilmService:
    elastic_index_name = 'movies'
    model = Film

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        try:
            film = await self._get_film_from_elastic(film_id)
        except NotFoundError:
            return None

        return film

    async def get_all(self, search_params: Optional[dict]) -> Union[list[Film]]:
        """
        Получение записей по поисковой строке
        """

        body = defaultdict(lambda: defaultdict(dict))
        body['from'] = (search_params['from'] - 1) * search_params['size']
        body['size'] = search_params['size']

        if search_params['sort']:
            body = self.search_params_sort(body, search_params)

        if search_params['query']:
            body = self.search_params_query(body, search_params)

        else:
            body['query']['match_all'] = {}

        data = await self.elastic.search(
            index=self.elastic_index_name,
            body=body
        )
        items = map(
            lambda item: {'id': item['_id'], **item['_source']},
            data.get('hits', {}).get('hits', [])
        )

        return parse_obj_as(list[self.model], list(items))

    def search_params_query(self, body, search_params):

        body['query']['bool']['should'] = []
        search_fields = {'title': 5, 'actors': 3, 'description': 1}
        for field, weight in search_fields.items():
            match = defaultdict(lambda: defaultdict(dict))
            match['match'][field]['query'] = search_params['query']
            match['match'][field]['boost'] = weight
            body['query']['bool']['should'].append(match)
        return body

    def search_params_sort(self, body, search_params):
        for field_by_order in search_params['sort'].split(','):
            if field_by_order in ORDER_FIELDS or field_by_order[1:] in ORDER_FIELDS:
                field = field_by_order.lstrip('-')
                if field not in ORDER_FIELDS:
                    continue

                body['sort'][field] = 'desk' if field_by_order.startswith('-') else 'asc'
        return body

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        doc = await self.elastic.get('movies', film_id)
        return Film(**doc['_source'])


@lru_cache()
def get_film_service(redis: Redis = Depends(get_redis),
                     elastic: AsyncElasticsearch = Depends(get_elastic), ) -> FilmService:
    return FilmService(redis, elastic)
