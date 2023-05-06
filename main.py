# basic fastapi server with a single endpoint
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from aiortc import RTCSessionDescription

# create app object
app = FastAPI()

# add CORS middleware
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def signaling(websocket: WebSocket):
    await websocket.accept()
    while True:
        message = await websocket.receive_text()
        # health check endpoint
        if message.startswith("offer:"):
            offer = RTCSessionDescription(sdp=message[6:], type="offer")
            print(offer)


@ app.get("/api/ping")
async def ping():
    return {
        "message": "Application server is up and running",
        "timestamp": datetime.now().isoformat()
    }
