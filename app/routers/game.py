from models.player import Player
from models.game import Game
from dto.game import GameCreate, GameResponse
from database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException
from services.game import new_game, generate_random_board
from typing import List


router = APIRouter(prefix="", tags=["game"])


@router.post("/create", response_model=GameResponse)
def create_game(game_create: GameCreate, db: Session = Depends(get_db)):
    game = new_game(game_create.player_1_id, game_create.player_2_id, db)
    return GameResponse(
        id=game.id,
        player_1_id=game.player_1_id,
        player_2_id=game.player_2_id,
        player_1_board=game.board_1,
        player_2_board=game.board_2,
        status=game.status,
        winner_id=0,
    )


@router.get("/", response_model=List[GameResponse])
def get_active_games(db: Session = Depends(get_db)):
    active_games = db.query(Game).filter(Game.status == "active").all()
    return [
        GameResponse(
            id=game.id,
            player_1_id=game.player_1_id,
            player_2_id=game.player_2_id,
            player_1_board=game.board_1,
            player_2_board=game.board_2,
            status=game.status,
            winner_id=0,
        )
        for game in active_games
    ]


@router.patch("/status", response_model=GameResponse)
def update_status(game_id: int, winner_id: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == game_id).first()

    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    player_1 = db.query(Player).filter(Player.id == game.player_1_id).first()
    player_2 = db.query(Player).filter(Player.id == game.player_2_id).first()

    player_1.is_playing = False
    player_2.is_playing = False

    if winner_id not in [player_1.id, player_2.id]:
        raise HTTPException(status_code=404, detail="That player id not in this game")

    game.status = "finished"
    game.winner_id = winner_id
    db.commit()
    db.refresh(game)

    return GameResponse(
        id=game.id,
        player_1_id=game.player_1_id,
        player_2_id=game.player_2_id,
        player_1_board=game.board_1,
        player_2_board=game.board_2,
        status=game.status,
        winner_id=winner_id
    )