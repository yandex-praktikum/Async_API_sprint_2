from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_cache.decorator import cache

from models.film import Film
from models.person import PersonDetail
from services.person import PersonService, get_person_service

router = APIRouter()


@router.get('/{person_id}',
            response_model=PersonDetail,
            description='Возвращает персону по её id',
            response_model_by_alias=False)
@cache(expire=600)
async def person_details(person_id: UUID,
                         person_service: PersonService = Depends(get_person_service)) -> PersonDetail:
    """
    Предоставляет информацию о жанре по его id
    :param person_service:
    :param person_id:
    """
    person = await person_service.get_by_id(person_id=person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')

    return person


@router.get('/{person_id}/film', response_model=list[Film],
            description='Возвращает список фильмов по персоне',
            response_model_by_alias=False)
@cache(expire=600)
async def person_films(person_id: UUID,
                       page: int = Query(1, alias='page[number]', ge=1),
                       size: int = Query(10, alias='page[size]', ge=1),
                       person_service: PersonService = Depends(get_person_service)) -> list[Film]:
    from_ = size * (page - 1)
    films = await person_service.get_person_films(person_id, from_, size)

    return films
