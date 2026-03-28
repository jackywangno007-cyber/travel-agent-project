from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.trip import router as trip_router
from app.utils.config import CORS_ALLOW_ORIGINS

app = FastAPI(
    title="Travel Agent API",
    description="智能旅行规划后端服务。",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_router)


@app.get("/")
def root():
    return {"message": "Travel Agent backend is running."}
