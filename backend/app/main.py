from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.trip import router as trip_router

app = FastAPI(
    title="Travel Agent API",
    description="一个基于多 Agent 思想的智能旅行规划后端服务",
    version="0.1.0",
)

# 先全部放开，方便前后端联调
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trip_router)


@app.get("/")
def root():
    return {"message": "Travel Agent backend is running."}
