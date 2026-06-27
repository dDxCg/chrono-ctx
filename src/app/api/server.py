from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

local_ports = r"https?://(localhost|127\.0\.0\.1)(:\d+)?"

app = FastAPI()

origins = [
    local_ports
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
