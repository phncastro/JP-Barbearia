
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

# Caminho do arquivo do banco
DATABASE_PATH = Path(__file__).resolve().parent.parent / "jp_barbearia.db"

# Conexão com o SQLite
engine = create_engine(
    f"sqlite:///{DATABASE_PATH.as_posix()}",
    connect_args={"check_same_thread": False},
)

# Fábrica de sessões para consultar e alterar o banco
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

# Classe-base dos nossos modelos
class Base(DeclarativeBase):
    pass

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()