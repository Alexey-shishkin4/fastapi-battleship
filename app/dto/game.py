from pydantic import BaseModel


class GameCreate(BaseModel):
    player_1_id: int
    player_2_id: int

    class Config:
        from_attributes = True


class GameResponse(BaseModel):
    id: int
    player_1_id: int
    player_2_id: int
    player_1_board: str
    player_2_board: str
    status: str
    winner_id: int

    class Config:
        from_attributes = True


class MoveCreate(BaseModel):
    position: str


class MoveResponse(BaseModel):
    id: int
    position: str
    result: str

    class Config:
        from_attributes = True
