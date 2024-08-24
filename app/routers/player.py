from dto.player import PlayerResponse, PlayerCreate, PlayerLogin, GameStat, PlayerStatsResponse
from services.player import register, login
from models.player import Player
from models.game import Game
from database import get_db
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Response
from typing import List
from sqlalchemy import or_


router = APIRouter(prefix="", tags=["players"])


@router.post("/register", response_model=PlayerResponse)
def register_player(player: PlayerCreate, db: Session = Depends(get_db)):
    db_player = register(player, db)
    return db_player


@router.post("/login", response_model=PlayerResponse)
def login_player(player: PlayerLogin, response: Response, db: Session = Depends(get_db)):
    db_player = login(player.username, player.password, db)

    if not db_player:
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    response.set_cookie(key="id", value=str(db_player.id), httponly=False)

    # Возвращаем данные пользователя, куки будут включены в этот ответ
    return db_player


@router.get("/", response_model=List[PlayerResponse])
def get_available_players(db: Session = Depends(get_db)):
    available_players = db.query(Player).filter(Player.is_playing == False).all()
    return available_players


@router.get("/{player_id}/stats", response_model=PlayerStatsResponse)
def get_player_stats(player_id: int, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

    games = db.query(Game).filter(
        or_(Game.player_1_id == player_id, Game.player_2_id == player_id)
    ).all()

    # Формирование списка статистики игр
    game_stats = [
        GameStat(
            date=game.created_at,
            status=game.status,
            winner_id=game.winner_id
        )
        for game in games
    ]

    return PlayerStatsResponse(games=game_stats)
