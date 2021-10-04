import os
from datetime import datetime

from pydantic import BaseModel, Field


class StateModel(BaseModel):
    # Дата с которой будет происходить самое первое сканирование, когда у нас ещё нет стэйта
    movies: datetime = Field(datetime(1970, 1, 1))
    genres: datetime = Field(datetime(1970, 1, 1))
    persons: datetime = Field(datetime(1970, 1, 1))


class State:
    def __init__(self, file_name):
        self._file_name = file_name
        self._state = StateModel()
        self._loadstate()

    def _savestate(self):
        with open(self._file_name, 'w') as file:
            file.write(self._state.json())

    def _loadstate(self):
        if os.path.exists(self._file_name):
            self._state = StateModel.parse_file(self._file_name)
            return
        self._savestate()

    def __getattr__(self, item):
        return getattr(self._state, item)

    def set(self, key, value):
        setattr(self._state, key, value)
        self._savestate()
