from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi_cache.decorator import cache

from models.genre import Genre
from services.genre import GenreService, get_genre_service

router = APIRouter()


@router.get('/{genre_id}',
            response_model=Genre,
            description='Возвращает жанр по его id',
            response_model_by_alias=False)
@cache(expire=600)
async def genre_details(genre_id: UUID, genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    """
    Предоставляет информацию о жанре по его id
    :param genre_service:
    :param genre_id:
    """
    genre = await genre_service.get_by_id(genre_id=genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')

    return genre
