from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PlayerCreate(BaseModel):
    username: str
    password: str


class PlayerLogin(BaseModel):
    username: str
    password: str


class PlayerResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class GameStat(BaseModel):
    date: datetime
    status: str
    winner_id: Optional[int]

    class Config:
        from_attributes = True


class PlayerStatsResponse(BaseModel):
    games: list[GameStat]
