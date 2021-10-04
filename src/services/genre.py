from functools import lru_cache
from typing import Optional
from uuid import UUID

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import Genre


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: UUID) -> Optional[Genre]:
        """
        Жанр по id
        """
        genre = await self._get_from_elastic(genre_id)
        if not genre:
            return None

        return genre

    async def _get_from_elastic(self, genre_id: UUID) -> Optional[Genre]:
        doc = await self.elastic.get('genres', genre_id)
        return Genre(**doc['_source'])


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
