from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid
import random

app = FastAPI()

# <<-- PUT YOUR NETLIFY SITE URL HERE -->> (keep exact domain & protocol, no trailing /)
origins = [
    "https://roaring-beijinho-30faeb.netlify.app",   # Your live Netlify site
    "http://localhost:8000",                         # Local dev (optional, safe)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Fun avatar emoji set!
AVATARS = ["👧", "🧑", "👦", "👩‍🎤", "🦸", "🤴", "👩‍💻", "🦹", "🧙‍♂️", "🧞‍♂️", "🧝‍♀️"]

def assign_avatar(name: str):
    return AVATARS[hash(name) % len(AVATARS)]

class Table(BaseModel):
    id: str
    creator: str
    creator_avatar: str
    bet_amount: float
    status: str  # "open", "full", "completed"
    players: List[str]
    avatars: List[str] = []
    winner: Optional[str] = ""
    winning_side: Optional[str] = ""

tables = []

@app.get("/")
def root():
    return {"message": "Welcome to the Pi Toss Game API!"}

@app.get("/api/open_tables")
def get_open_tables():
    return {"tables": [table for table in tables if table.status in ["open", "full"]]}

@app.post("/api/create_table")
def create_table(data: dict):
    creator = data.get("creator")
    bet = data.get("bet_amount")
    if not creator or bet is None:
        raise HTTPException(status_code=400, detail="creator and bet_amount required")
    avatar = assign_avatar(creator)
    new_table = Table(
        id=str(uuid.uuid4())[:8],
        creator=creator,
        creator_avatar=avatar,
        bet_amount=float(bet),
        status="open",
        players=[creator],
        avatars=[avatar]
    )
    tables.append(new_table)
    return {"success": True, "table": new_table}

@app.post("/api/join_table")
def join_table(data: dict):
    table_id = data.get("table_id")
    player = data.get("player")
    for table in tables:
        if table.id == table_id and table.status == "open":
            if player in table.players:
                raise HTTPException(status_code=400, detail="Player already in table")
            if len(table.players) >= 2:
                raise HTTPException(status_code=400, detail="Table already full")
            avatar = assign_avatar(player)
            table.players.append(player)
            table.avatars.append(avatar)
            if len(table.players) == 2:
                table.status = "full"
            return {"success": True, "table": table}
    raise HTTPException(status_code=404, detail="Table not found or not open")

@app.post("/api/toss_coin")
def toss_coin(data: dict):
    table_id = data.get("table_id")
    for table in tables:
        if table.id == table_id:
            if table.status != "full":
                raise HTTPException(status_code=400, detail="Need 2 players to toss")
            side = random.choice(["Heads", "Tails"])
            winner_idx = 0 if side == "Heads" else 1
            winner = table.players[winner_idx]
            table.winner = winner
            table.winning_side = side
            table.status = "completed"
            return {
                "result": f"{side}: {winner} wins!",
                "winner": winner,
                "side": side,
                "avatars": table.avatars,
                "players": table.players
            }
    raise HTTPException(status_code=404, detail="Table not found")
