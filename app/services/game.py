from sqlalchemy.orm import Session
import random
from models.player import Player
from models.game import Game
from dto.game import GameCreate
from fastapi import APIRouter, Depends, HTTPException
from database import get_db


def generate_random_board(size: int = 10) -> str:
    board = [["~"] * size for _ in range(size)]
    ships = {
        "4": 1,  # 1 корабль размером 4 клетки
        "3": 2,  # 2 корабля размером 3 клетки
        "2": 3,  # 3 корабля размером 2 клетки
        "1": 4  # 4 корабля размером 1 клетка
    }

    def is_valid_position(board, x, y, length, orientation):
        """Проверка, можно ли разместить корабль на доске"""
        dx, dy = (1, 0) if orientation == 'horizontal' else (0, 1)

        for i in range(length):
            nx, ny = x + i * dx, y + i * dy
            if nx >= size or ny >= size or board[ny][nx] != "~":
                return False

            # Проверяем соседние клетки, чтобы корабли не касались
            for ix in range(-1, 2):
                for iy in range(-1, 2):
                    cx, cy = nx + ix, ny + iy
                    if 0 <= cx < size and 0 <= cy < size and board[cy][cx] != "~":
                        return False
        return True

    def place_ship(board, x, y, length, orientation):
        """Размещение корабля на доске"""
        dx, dy = (1, 0) if orientation == 'horizontal' else (0, 1)
        for i in range(length):
            nx, ny = x + i * dx, y + i * dy
            board[ny][nx] = "O"

    for length, count in ships.items():
        length = int(length)
        for _ in range(count):
            while True:
                x, y = random.randint(0, size - 1), random.randint(0, size - 1)
                orientation = random.choice(['horizontal', 'vertical'])
                if is_valid_position(board, x, y, length, orientation):
                    place_ship(board, x, y, length, orientation)
                    break

    # Преобразуем доску в строку для сохранения в базе данных
    return "\n".join(["".join(row) for row in board])


def new_game(player_1_id: int, player_2_id: int, db: Session = Depends(get_db)):
    player_1 = db.query(Player).filter(Player.id == player_1_id).first()
    player_2 = db.query(Player).filter(Player.id == player_2_id).first()

    if not player_1 or not player_2:
        raise HTTPException(status_code=400, detail="One or both players do not exist.")

    if player_1.is_playing or player_2.is_playing:
        raise HTTPException(status_code=400, detail="One or both players are already in a game.")

    player_1_board = generate_random_board()
    player_2_board = generate_random_board()
    game = Game(
        player_1_id=player_1_id,
        player_2_id=player_2_id,
        board_1=player_1_board,
        board_2=player_2_board,
        status="active"
    )

    player_1.is_playing = True
    player_2.is_playing = True

    db.add(game)
    db.commit()
    db.refresh(game)
    return game


def get_games(db: Session):
    return db.query(Game).filter(Game.status == "active").all()
