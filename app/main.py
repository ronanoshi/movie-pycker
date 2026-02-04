"""FastAPI application entrypoint."""

from fastapi import FastAPI

from app.api.movies import router as movies_router

app = FastAPI(title="Movie Pycker")
app.include_router(movies_router)

