from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
from routers import player as PlayerRouter
from routers import game as GameRouter
from database import engine, Base
from fastapi.middleware.cors import CORSMiddleware
from websocket_manager import websocket_endpoint, html
import uvicorn


Base.metadata.create_all(bind=engine)
app = FastAPI()
app.include_router(PlayerRouter.router, prefix="/player")
app.include_router(GameRouter.router, prefix="/game")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def get():
    return HTMLResponse(html)


app.websocket("/ws/{client_id}")(websocket_endpoint)


#if __name__ == '__main__':
#    uvicorn.run("main:app", host='127.0.0.1', port=8000)
