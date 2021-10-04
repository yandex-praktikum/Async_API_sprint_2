from http import HTTPStatus
from typing import List, Optional

from fastapi import Depends, HTTPException, Query, APIRouter
from fastapi_cache.decorator import cache

from models.film import Film
from services.film import FilmService, get_film_service

router = APIRouter()


@router.get('/{film_id}', response_model=Film, description='Возвращает фильм по его id',
            response_description='Описание ответа', tags=['Поиск по id'], response_model_by_alias=False)
@cache(expire=600)
async def film_details(film_id: str, film_service: FilmService = Depends(get_film_service)) -> Film:
    """
    Предоставляет информацию о кинопроизведении по его id
    :param film_service:
    :param film_id:
    """
    film = await film_service.get_by_id(film_id=film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return film


@router.get('', response_model=List[Film], description='Полнотекстовый поиск по фильмам',
            response_description='Описание ответа', tags=['Полнотекстовый поиск'], response_model_by_alias=False)
@cache(expire=600)
async def movies_list(film_service: FilmService = Depends(get_film_service),
                      from_: Optional[int] = Query(1, title='Номер страницы (первая страгица 1)',
                                                   alias='page[number]', gt=0),
                      size_: Optional[int] = Query(10, title='Размер страницы', alias='page[size]', gt=0),
                      sort_: Optional[str] = Query(None, title='Поле сортировки (id, rating)', alias='sort'),
                      query_: Optional[str] = Query(None, title='Поисковая строка', alias='query')):
    """
    Предоставляет информацию о фильмах
    Параметры поиска:
    - from: int начиная с какого элемента начинаем показ выдачи
    - size: int количество элементов в выдаче
    - sort: str поле для сортировки
    - query: str поисковая строка
    """

    search_params = {'from': from_, 'size': size_, 'sort': sort_, 'query': query_}

    films = await film_service.get_all(search_params=search_params)
    return films
