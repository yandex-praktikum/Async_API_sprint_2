from logging import config as logging_config

import aioredis
import uvicorn as uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

from api.v1 import film, genre, person
from core import config
from core.logger import LOGGING
from db import elastic, redis

app = FastAPI(title=config.PROJECT_NAME, docs_url='/api/openapi', openapi_url='/api/openapi.json',
              default_response_class=ORJSONResponse, )


@app.on_event('startup')
async def startup():
    redis.redis = await aioredis.from_url(f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}', encoding="utf8",
                                          decode_responses=True)
    elastic.es = AsyncElasticsearch(hosts=[f'{config.ELASTIC_HOST}:{config.ELASTIC_PORT}'])
    FastAPICache.init(RedisBackend(redis.redis), prefix='movieapi-cache')


@app.on_event('shutdown')
async def shutdown():
    await redis.redis.close()
    await elastic.es.close()


app.include_router(film.router, prefix='/api/v1/film', tags=['film'])
app.include_router(genre.router, prefix='/api/v1/genre', tags=['genre'])
app.include_router(person.router, prefix='/api/v1/person', tags=['person'])

if __name__ == '__main__':
    # Применяем настройки логирования
    logging_config.dictConfig(LOGGING)

    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=config.PROJECT_PORT,
        log_config=LOGGING,
        log_level=config.PROJECT_LOG_LEVEL,
    )
