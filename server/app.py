from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from server.canon import REPO_ROOT, Canon, default_db_path

RASTER_DIR = REPO_ROOT / "data" / "raster"
WEB_DIST = REPO_ROOT / "web" / "dist"


class MetaCounts(BaseModel):
    countries: int
    leagues: int
    clubs: int
    players: int
    national_teams: int
    stats_per_player: int
    free_agents: int
    free_agents_enriched: int


class MetaResponse(BaseModel):
    schema_version: int
    source_snapshot_date: str | None = None
    counts: MetaCounts


class Country(BaseModel):
    id: str
    name: str
    flag: str
    leagues_count: int
    clubs_count: int


class League(BaseModel):
    id: str
    name: str
    country_id: str
    country_name: str
    country_flag: str
    tier: str
    tier_rank: int
    logo: str
    clubs_count: int


class Stadium(BaseModel):
    name: str | None = None
    seats: int | None = None


class Club(BaseModel):
    id: str
    name: str
    league_id: str
    league_name: str
    tier: str
    tier_rank: int
    country_id: str
    country_name: str
    country_flag: str
    logo: str
    colors: list[str]
    stadium: Stadium
    founded_on: str | None = None


class PlayerSummary(BaseModel):
    id: str
    name: str
    first_name: str | None = None
    last_name: str | None = None
    birth_date: str | None = None
    age: int | None = None
    height: int | None = None
    foot: str = ""
    citizenship: list[str]
    position: str
    position_other: list[str]
    club_id: str | None = None
    national_team_id: str | None = None
    shirt_number: int | None = None
    market_value: int
    overall: float
    pot: int
    weight: int | None = None
    weak_foot: int | None = None
    skill_moves: int | None = None
    role: str | None = None
    photo: str


class PlayerDetail(PlayerSummary):
    stats: dict[str, float]


def create_app(db_path: Path | None = None) -> FastAPI:
    canon = Canon(db_path or default_db_path())
    app = FastAPI(title="GF Career Prototype API", version="0.2.0")
    app.state.canon = canon

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.mount("/raster", StaticFiles(directory=str(RASTER_DIR)), name="raster")

    @app.get("/api/meta", response_model=MetaResponse)
    def meta():
        return canon.meta()

    @app.get("/api/countries", response_model=list[Country])
    def countries():
        return canon.countries()

    @app.get("/api/leagues", response_model=list[League])
    def leagues(country_id: str | None = None):
        return canon.leagues(country_id)

    @app.get("/api/clubs", response_model=list[Club])
    def clubs(
        league_id: str | None = None,
        country_id: str | None = None,
        limit: int = Query(500, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ):
        return canon.clubs(league_id, country_id, limit, offset)

    @app.get("/api/clubs/{club_id}", response_model=Club)
    def club(club_id: str):
        result = canon.club(club_id)
        if result is None:
            raise HTTPException(status_code=404, detail="club not found")
        return result

    @app.get("/api/clubs/{club_id}/players", response_model=list[PlayerSummary])
    def squad(club_id: str):
        if canon.club(club_id) is None:
            raise HTTPException(status_code=404, detail="club not found")
        return canon.squad(club_id)

    @app.get("/api/players/{player_id}", response_model=PlayerDetail)
    def player(player_id: str):
        result = canon.player(player_id)
        if result is None:
            raise HTTPException(status_code=404, detail="player not found")
        return result

    if WEB_DIST.exists():
        app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
    else:

        @app.get("/")
        def root():
            return {"service": "gf-career-prototype-api", "web": "not built"}

    return app
