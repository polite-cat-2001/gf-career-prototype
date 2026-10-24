from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import json
from pathlib import Path

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
JSON_DIR = DATA_DIR / "json"
RASTER_DIR = DATA_DIR / "raster"

# ── Load canon data ─────────────────────────────────────────────────────────

def load_json(name: str):
    p = JSON_DIR / name
    if not p.exists():
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)

PLAYERS = load_json("players.json")
CLUBS = load_json("clubs.json")
NATIONAL_TEAMS = load_json("national_teams.json")
COMPETITIONS = load_json("competitions.json")
COACHES = load_json("coaches.json")
MARKET_VALUES = load_json("players_market_value.json")

# Build lookup maps
PLAYERS_BY_ID = {str(p["id"]): p for p in PLAYERS}
CLUBS_BY_ID = {str(c["id"]): c for c in CLUBS}
TEAMS_BY_ID = {str(t["id"]): t for t in NATIONAL_TEAMS}

# ── Static files ────────────────────────────────────────────────────────────

app.mount("/raster", StaticFiles(directory=str(RASTER_DIR)), name="raster")

# ── Models ──────────────────────────────────────────────────────────────────

class PlayerSummary(BaseModel):
    id: int
    name: str
    position: str
    age: int
    rating: Optional[int] = None
    club_id: Optional[int] = None
    photo: Optional[str] = None

class ClubSummary(BaseModel):
    id: int
    name: str
    logo: Optional[str] = None
    league: Optional[str] = None

class LeagueSummary(BaseModel):
    id: int
    name: str
    country: str
    logo: Optional[str] = None

class NationalTeamSummary(BaseModel):
    id: int
    name: str
    flag: Optional[str] = None

# ── Endpoints ───────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "gf-career-prototype-api",
        "counts": {
            "players": len(PLAYERS),
            "clubs": len(CLUBS),
            "national_teams": len(NATIONAL_TEAMS),
            "competitions": len(COMPETITIONS),
            "coaches": len(COACHES),
        },
    }

@app.get("/api/players", response_model=list[PlayerSummary])
def all_players(skip: int = 0, limit: int = 100):
    from datetime import date
    today = date.today()
    result = []
    for p in PLAYERS[skip : skip + limit]:
        age = 0
        if p.get("birth_date"):
            try:
                bd = date.fromisoformat(p["birth_date"])
                age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
            except:
                pass
        photo_path = f"/raster/players_faces/{p['id']}.jpg"
        result.append({
            "id": int(p["id"]),
            "name": p.get("name", "Unknown"),
            "position": p.get("position", {}).get("main", "") if isinstance(p.get("position"), dict) else p.get("position", ""),
            "age": age,
            "rating": p.get("rating"),
            "club_id": int(p["club_id"]) if p.get("club_id") else None,
            "photo": photo_path,
        })
    return result

@app.get("/api/players/{player_id}", response_model=PlayerSummary)
def player_detail(player_id: int):
    from datetime import date
    pid = str(player_id)
    p = PLAYERS_BY_ID.get(pid)
    if not p:
        return {"id": player_id, "name": "Not found", "position": "", "age": 0}
    age = 0
    if p.get("birth_date"):
        try:
            bd = date.fromisoformat(p["birth_date"])
            today = date.today()
            age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
        except:
            pass
    return {
        "id": int(p["id"]),
        "name": p.get("name", "Unknown"),
        "position": p.get("position", {}).get("main", "") if isinstance(p.get("position"), dict) else p.get("position", ""),
        "age": age,
        "rating": p.get("rating"),
        "club_id": int(p["club_id"]) if p.get("club_id") else None,
        "photo": f"/raster/players_faces/{p['id']}.jpg",
    }

@app.get("/api/clubs", response_model=list[ClubSummary])
def all_clubs(skip: int = 0, limit: int = 100):
    return [
        {
            "id": int(c["id"]),
            "name": c.get("name", "Unknown"),
            "logo": f"/raster/teams_emblems/{c['id']}.png",
            "league": c.get("league_name"),
        }
        for c in CLUBS[skip : skip + limit]
    ]

@app.get("/api/clubs/{club_id}", response_model=ClubSummary)
def club_detail(club_id: int):
    c = CLUBS_BY_ID.get(str(club_id))
    if not c:
        return {"id": club_id, "name": "Not found"}
    return {
        "id": int(c["id"]),
        "name": c.get("name", "Unknown"),
        "logo": f"/raster/teams_emblems/{c['id']}.png",
        "league": c.get("league_name"),
    }

@app.get("/api/clubs/{club_id}/players", response_model=list[PlayerSummary])
def club_players(club_id: int):
    from datetime import date
    today = date.today()
    cid = str(club_id)
    result = []
    for p in PLAYERS:
        if p.get("club_id") == cid:
            age = 0
            if p.get("birth_date"):
                try:
                    bd = date.fromisoformat(p["birth_date"])
                    age = today.year - bd.year - ((today.month, today.day) < (bd.month, bd.day))
                except:
                    pass
            result.append({
                "id": int(p["id"]),
                "name": p.get("name", "Unknown"),
                "position": p.get("position", {}).get("main", "") if isinstance(p.get("position"), dict) else p.get("position", ""),
                "age": age,
                "rating": p.get("rating"),
                "club_id": club_id,
                "photo": f"/raster/players_faces/{p['id']}.jpg",
            })
    return result

@app.get("/api/competitions", response_model=list[LeagueSummary])
def all_competitions():
    return [
        {
            "id": c.get("id", i),
            "name": c.get("name", "Unknown"),
            "country": c.get("country", ""),
            "logo": f"/raster/leagues/{c.get('id', i)}.png",
        }
        for i, c in enumerate(COMPETITIONS)
    ]

@app.get("/api/national-teams", response_model=list[NationalTeamSummary])
def all_national_teams():
    return [
        {
            "id": int(t["id"]),
            "name": t.get("name", "Unknown"),
            "flag": f"/raster/teams_flags/{t['id']}.png",
        }
        for t in NATIONAL_TEAMS
    ]

@app.get("/api/coaches")
def all_coaches():
    return COACHES[:100]
