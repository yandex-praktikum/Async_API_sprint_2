from dataclasses import dataclass
from datetime import datetime

from pydantic import BaseModel


class BasePerson(BaseModel):
    id: str
    full_name: str
    updated_at: datetime

    def to_dict(self):
        return self.dict(exclude={'updated_at'})


class Genre(BaseModel):
    id: str
    name: str
    updated_at: datetime

    def to_dict(self):
        return self.dict(exclude={'updated_at'})


@dataclass
class Person:
    id: str
    name: str
    role: str

    @classmethod
    def from_dict(cls, dict_: dict):
        return cls(
            id=str(dict_['id']),
            name=dict_['full_name'],
            role=dict_['role'],
        )


@dataclass
class Movie:
    id: str
    title: str
    description: str
    rating: float
    genre: list[str]
    genres: list[Genre]
    actors_names: list[str]
    writers_names: list[str]
    directors_names: list[str]
    directors_names: list[str]
    actors: list[dict]
    writers: list[dict]
    directors: list[dict]
    updated_at: datetime

    @classmethod
    def from_dict(cls, dict_: dict) -> 'Movie':
        """Испорт из  словаря"""

        return cls(
            id=str(dict_['id']),
            title=dict_['title'],
            description=dict_['description'],
            rating=dict_['rating'],
            genre=[],
            genres=[],
            actors_names=[],
            writers_names=[],
            directors_names=[],
            actors=[],
            writers=[],
            directors=[],
            updated_at=dict_['updated_at']
        )

    @staticmethod
    def _get_person_names(persons: list[Person], role: str):
        """Список имён нужной роли"""

        return [person.name for person in persons if person.role == role]

    @staticmethod
    def _filter_person(persons: list[Person], role):
        """Список персон нужной роли"""
        return [
            {
                'id': person.id,
                'name': person.name,
            }
            for person in persons if person.role == role]

    def fill_persons(self, persons: list[Person]):
        """Заполнение всех персон данного фильма"""
        self.actors_names = self._get_person_names(persons, 'actor')
        self.writers_names = self._get_person_names(persons, 'writer')
        self.directors_names = self._get_person_names(persons, 'director')
        self.actors = self._filter_person(persons, 'actor')
        self.writers = self._filter_person(persons, 'writer')
        self.directors = self._filter_person(persons, 'director')
