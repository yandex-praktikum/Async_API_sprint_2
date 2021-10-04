from typing import List
from uuid import UUID

from pydantic import Field

from .basemodel import BaseModel, OrjsonBaseModel


class InnerPerson(BaseModel):
    full_name: str = Field(..., alias='name')


class Person(BaseModel):
    full_name: str


class Roles(OrjsonBaseModel):
    actor: List[UUID] = []
    writer: List[UUID] = []
    director: List[UUID] = []


class PersonDetail(BaseModel):
    uuid: UUID
    full_name: str
    roles: Roles = Roles()
