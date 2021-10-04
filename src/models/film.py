import typing
from typing import List
from uuid import UUID

from pydantic import Field

from .basemodel import BaseModel
from .genre import Genre
from .person import InnerPerson


class Film(BaseModel):
    title: str
    imdb_rating: float = Field(..., alias='rating')
    description: str
    genre: typing.List[Genre] = Field(..., alias='genres')
    actors: typing.List[InnerPerson]
    writers: typing.List[InnerPerson]
    directors: typing.List[InnerPerson]

    def get_roles(self, person_id: UUID) -> List[str]:
        roles: List = []
        roles_list = ('actor', 'writer', 'director')
        for role in roles_list:
            for person in getattr(self, role + 's'):
                if person.uuid == person_id:
                    roles.append(role)
                    break
        return roles
