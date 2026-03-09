import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
load_dotenv()

from api.routes import router as http_router  # noqa: E402
from api.websocket import router as ws_router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Video Pipeline", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(http_router)
app.include_router(ws_router)
