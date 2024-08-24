from models.player import Player
from dto.player import PlayerCreate
from sqlalchemy.orm import Session
import uuid
import hashlib


def hash_password(password):
    salt = uuid.uuid4().hex
    return hashlib.sha256(salt.encode() + password.encode()).hexdigest() + ':' + salt


def check_password(hashed_password, user_password):
    password, salt = hashed_password.split(':')
    return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()


def register(data: PlayerCreate, db: Session):
    hashed_password = hash_password(data.password)
    player = Player(username=data.username, password_hash=hashed_password)
    try:
        db.add(player)
        db.commit()
        db.refresh(player)
    except Exception as e:
        print(e)

    return player


def login(username: str, password: str, db: Session):
    player = db.query(Player).filter(Player.username==username).first()
    if not player:
        return
    if not check_password(player.password_hash, password):
        return
    return player


def get_players(db: Session):
    players = db.query(Player).all()
    return players
