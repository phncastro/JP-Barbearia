import os

from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from Backend.auth import router as auth_router
from Backend.user import router as user_router
from Backend.database import Base, engine
from Backend import models

load_dotenv()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "Frontend"

app = FastAPI()

Base.metadata.create_all(bind=engine)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET")
)

app.include_router(auth_router)
app.include_router(user_router)

app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="Frontend")