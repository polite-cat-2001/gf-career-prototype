from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from server.canon import REPO_ROOT, Canon, default_db_path
from server.career import (
    ActionError,
    SaveFormatError,
    SaveNotFound,
    SaveStore,
    SaveVersionError,
    build_snapshot,
    create_career,
    swap_players,
)

RASTER_DIR = REPO_ROOT / "data" / "raster"
WEB_DIST = REPO_ROOT / "web" / "dist"
SAVES_DIR = REPO_ROOT / "saves"


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
    fatigue: int = 100
    stats: dict[str, float] | None = None


class PlayerDetail(PlayerSummary):
    stats: dict[str, float]


class CreateCareerRequest(BaseModel):
    club_id: str
    manager_name: str = Field(min_length=1, max_length=80)
    manager_nationality_id: str
    seed: int | None = Field(default=None, ge=0, le=4_294_967_295)


class CareerActionRequest(BaseModel):
    type: str
    player_a: str | None = None
    player_b: str | None = None


class ManagerInfo(BaseModel):
    name: str
    nationality_id: str
    nationality: str


class SquadSummary(BaseModel):
    squad_size: int
    average_overall: float
    average_age: float | None = None
    total_market_value: int


class SquadGroup(BaseModel):
    role: str
    players: list[PlayerSummary]


class LineupSlot(BaseModel):
    position: str
    role: str
    x: int
    y: int
    player: PlayerSummary


class Lineup(BaseModel):
    formation: str
    slots: list[LineupSlot]
    bench: list[PlayerSummary]


class SquadBlock(BaseModel):
    summary: SquadSummary
    groups: list[SquadGroup]
    lineup: Lineup


class CareerSnapshot(BaseModel):
    version: int
    id: str
    seed: int
    date: str
    created_at: str
    updated_at: str
    manager: ManagerInfo
    club: Club
    squad: SquadBlock


def _int_or_zero(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


class CareerListItem(BaseModel):
    id: str
    version: int
    seed: int
    date: str
    created_at: str
    updated_at: str
    manager_name: str
    club_id: str
    club_name: str
    club_logo: str
    league_name: str
    country_name: str
    compatible: bool = True
    problem: str | None = None


def create_app(db_path: Path | None = None, saves_dir: Path | None = None) -> FastAPI:
    canon = Canon(db_path or default_db_path())
    saves = SaveStore(saves_dir or SAVES_DIR)
    app = FastAPI(title="GF Career Prototype API", version="0.3.0")
    app.state.canon = canon
    app.state.saves = saves

    def load_career(career_id: str):
        try:
            return saves.load(career_id)
        except SaveNotFound as error:
            raise HTTPException(status_code=404, detail="career save not found") from error
        except SaveVersionError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except SaveFormatError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error

    def snapshot(career):
        club = canon.club(career.club_id)
        if club is None:
            raise HTTPException(
                status_code=409,
                detail=f"club {career.club_id} from career {career.id} is missing from canon.db",
            )
        players = canon.players_by_ids(career.player_ids, with_stats=True)
        if not players:
            raise HTTPException(
                status_code=409,
                detail=f"career {career.id} has no players in canon.db",
            )
        return build_snapshot(career, club, players)

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

    @app.post("/api/careers", response_model=CareerSnapshot, status_code=201)
    def create_career_endpoint(payload: CreateCareerRequest):
        club = canon.club(payload.club_id)
        if club is None:
            raise HTTPException(status_code=404, detail="club not found")
        nationality = canon.country(payload.manager_nationality_id)
        if nationality is None:
            raise HTTPException(status_code=404, detail="manager nationality not found")
        manager_name = payload.manager_name.strip()
        if not manager_name:
            raise HTTPException(status_code=422, detail="manager name must not be blank")
        squad = canon.squad(payload.club_id)
        if not squad:
            raise HTTPException(
                status_code=422,
                detail="selected club has no players in canon.db",
            )
        career = create_career(
            manager_name=manager_name,
            manager_nationality_id=nationality["id"],
            manager_nationality=nationality["name"],
            club_id=club["id"],
            player_ids=[player["id"] for player in squad],
            seed=payload.seed,
        )
        saves.save(career)
        return snapshot(career)

    @app.get("/api/careers", response_model=list[CareerListItem])
    def careers():
        items = []
        for entry in saves.scan():
            career = entry["career"]
            if career is not None:
                club = canon.club(career.club_id)
                if club is None:
                    continue
                items.append(
                    {
                        "id": career.id,
                        "version": career.version,
                        "seed": career.seed,
                        "date": career.date,
                        "created_at": career.created_at,
                        "updated_at": career.updated_at,
                        "manager_name": career.manager.name,
                        "club_id": club["id"],
                        "club_name": club["name"],
                        "club_logo": club["logo"],
                        "league_name": club["league_name"],
                        "country_name": club["country_name"],
                        "compatible": True,
                    }
                )
                continue

            raw = entry["raw"] or {}
            manager = raw.get("manager") or {}
            club_id = raw.get("club_id")
            club = canon.club(str(club_id)) if club_id else None
            items.append(
                {
                    "id": entry["id"],
                    "version": _int_or_zero(raw.get("version")),
                    "seed": _int_or_zero(raw.get("seed")),
                    "date": str(raw.get("date") or ""),
                    "created_at": str(raw.get("created_at") or ""),
                    "updated_at": str(raw.get("updated_at") or ""),
                    "manager_name": str(manager.get("name") or "Неизвестный менеджер"),
                    "club_id": club["id"] if club else "",
                    "club_name": club["name"] if club else "Неизвестный клуб",
                    "club_logo": club["logo"] if club else "",
                    "league_name": club["league_name"] if club else "",
                    "country_name": club["country_name"] if club else "",
                    "compatible": False,
                    "problem": str(entry["error"]),
                }
            )

        items.sort(key=lambda item: (item["updated_at"], item["id"]), reverse=True)
        return items

    @app.get("/api/careers/latest", response_model=CareerSnapshot)
    def latest_career():
        career = saves.latest()
        if career is None:
            raise HTTPException(status_code=404, detail="no career saves yet")
        return snapshot(career)

    @app.get("/api/careers/{career_id}", response_model=CareerSnapshot)
    def career(career_id: str):
        return snapshot(load_career(career_id))

    @app.post("/api/careers/{career_id}/save", response_model=CareerSnapshot)
    def save_career(career_id: str):
        career = load_career(career_id)
        career.touch()
        saves.save(career)
        return snapshot(career)

    @app.post("/api/careers/{career_id}/actions", response_model=CareerSnapshot)
    def apply_action(career_id: str, payload: CareerActionRequest):
        career = load_career(career_id)
        if payload.type != "swap":
            raise HTTPException(status_code=422, detail=f"unknown action type: {payload.type}")
        if not payload.player_a or not payload.player_b:
            raise HTTPException(status_code=422, detail="swap requires player_a and player_b")
        players = canon.players_by_ids(career.player_ids)
        try:
            swap_players(career, players, payload.player_a, payload.player_b)
        except ActionError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        career.touch()
        saves.save(career)
        return snapshot(career)

    if WEB_DIST.exists():
        app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="web")
    else:

        @app.get("/")
        def root():
            return {"service": "gf-career-prototype-api", "web": "not built"}

    return app
