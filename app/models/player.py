from sqlalchemy import Column, Integer, String, Boolean
from database import Base


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_playing = Column(Boolean, default=False)