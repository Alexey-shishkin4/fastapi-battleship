from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

#SQLALCHEMY_URL = "sqlite:///./sql_app.db"
SQLALCHEMY_URL = "postgresql://djazzy:123@localhost/battleship"

engine = create_engine(SQLALCHEMY_URL)
Sessionlocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base = declarative_base()

def get_db():
    db = Sessionlocal()

    try:
        yield db
    finally:
        db.close()