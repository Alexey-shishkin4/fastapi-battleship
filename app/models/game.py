from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Text, DateTime
from sqlalchemy.sql import func
from database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    player_1_id = Column(Integer, ForeignKey("players.id"))
    player_2_id = Column(Integer, ForeignKey("players.id"))

    board_1 = Column(Text)  # Сериализованное представление доски
    board_2 = Column(Text)

    status = Column(String, default="waiting")
    winner_id = Column(Integer, ForeignKey("players.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Move(Base):
    __tablename__ = "moves"

    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    player_id = Column(Integer, ForeignKey("players.id"))
    position = Column(String)  # A1 B2 etc
    result = Column(String)  # miss hit sink
    created_at = Column(DateTime(timezone=True), server_default=func.now())