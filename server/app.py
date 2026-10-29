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
    SeasonError,
    advance_to,
    build_lineup,
    build_match_setup,
    build_match_simulation,
    build_snapshot,
    create_career,
    ensure_schedule,
    next_fixture,
    next_season,
    play_next_match,
    season_transition,
    squad_strength,
    swap_players,
)
from server.career.condition import (
    apply_match_outcome,
    blocked_player_ids,
    ensure_player_states,
    recover_condition,
)
from server.career.snapshot import lineup_for, lineup_strength

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


class PlayerInjury(BaseModel):
    type: str
    until: str


class PlayerSuspension(BaseModel):
    matches: int
    reason: str


class PlayerSeasonStats(BaseModel):
    apps: int = 0
    starts: int = 0
    minutes: int = 0
    goals: int = 0
    assists: int = 0
    yellow: int = 0
    red: int = 0


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
    effective_overall: float | None = None
    injury: PlayerInjury | None = None
    suspension: PlayerSuspension | None = None
    season_stats: PlayerSeasonStats | None = None
    available: bool = True
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
    date: str | None = None


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
    reserve: list[PlayerSummary] = []


class SquadBlock(BaseModel):
    summary: SquadSummary
    groups: list[SquadGroup]
    lineup: Lineup


class SeasonClub(BaseModel):
    id: str
    name: str
    logo: str = ""


class SeasonOpponent(SeasonClub):
    strength: float


class SeasonNext(BaseModel):
    fixture_id: str
    date: str
    round: int
    home: bool
    opponent: SeasonOpponent


class SeasonResult(BaseModel):
    fixture_id: str
    date: str
    round: int
    home: bool
    goals_for: int
    goals_against: int
    outcome: str
    opponent: SeasonClub


class StandingRow(BaseModel):
    position: int
    club_id: str
    club_name: str
    club_logo: str = ""
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int
    previous_position: int | None = None
    delta: int = 0


class MatchdayScore(BaseModel):
    home: int
    away: int


class MatchdayResult(BaseModel):
    fixture_id: str
    home: SeasonClub
    away: SeasonClub
    score: MatchdayScore
    own: bool = False


class MatchdayBlock(BaseModel):
    round: int
    date: str
    competition: str = ""
    results: list[MatchdayResult]
    standings: list[StandingRow]


class SeasonLeague(BaseModel):
    id: str
    name: str


class SeasonClubRef(BaseModel):
    id: str
    name: str
    logo: str = ""
    position: int | None = None


class SeasonMove(BaseModel):
    club: SeasonClubRef
    league: SeasonLeague


class SeasonNextDivision(BaseModel):
    league: SeasonLeague
    above: SeasonLeague | None = None
    below: SeasonLeague | None = None
    from_above: list[SeasonMove]
    from_below: list[SeasonMove]


class SeasonReview(BaseModel):
    league: SeasonLeague
    standings: list[StandingRow]
    promoted: list[SeasonClubRef]
    relegated: list[SeasonClubRef]
    promoted_to: SeasonLeague | None = None
    relegated_to: SeasonLeague | None = None
    movement: str | None = None
    next: SeasonNextDivision | None = None


class SeasonBlock(BaseModel):
    season_start: str
    round: int
    rounds_total: int
    complete: bool
    next: SeasonNext | None = None
    last_result: SeasonResult | None = None
    form: list[SeasonResult]
    standings: list[StandingRow]
    last_matchday: MatchdayBlock | None = None
    review: SeasonReview | None = None


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
    season: SeasonBlock


class MatchPlayer(BaseModel):
    id: str
    name: str
    last_name: str | None = None
    shirt_number: int | None = None
    role: str | None = None


class MatchSlot(BaseModel):
    position: str
    role: str
    x: int
    y: int
    player: MatchPlayer


class MatchLineup(BaseModel):
    formation: str
    slots: list[MatchSlot]
    bench: list[MatchPlayer]


class MatchTeam(BaseModel):
    id: str
    name: str
    logo: str = ""
    abbr: str


class MatchSetup(BaseModel):
    fixture_id: str
    round: int
    date: str
    home: bool
    competition: str
    home_team: MatchTeam
    away_team: MatchTeam
    home_lineup: MatchLineup
    away_lineup: MatchLineup


class MatchScore(BaseModel):
    home: int
    away: int


class MatchEvent(BaseModel):
    id: str
    minute: int
    type: str
    team: str
    player: MatchPlayer
    player_out: MatchPlayer | None = None
    assist: MatchPlayer | None = None
    injury_type: str | None = None
    injury_until: str | None = None


class MatchSimulation(MatchSetup):
    events: list[MatchEvent]
    score: MatchScore
    outcome: str
    goals_for: int
    goals_against: int


class MatchSimulationResponse(BaseModel):
    career: CareerSnapshot
    match: MatchSimulation


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

    def strength_resolver(career=None, players=None):
        cache: dict[str, float] = {}

        def resolve(club_id: str) -> float:
            if club_id not in cache:
                if career is not None and players and club_id == career.club_id:
                    cache[club_id] = lineup_strength(career, players)
                else:
                    cache[club_id] = squad_strength(canon.squad(club_id))
            return cache[club_id]

        return resolve

    league_catalog = {str(league["id"]): league for league in canon.leagues()}

    def division_context(career, club):
        league_id = career.league_id or str(club["league_id"])
        league = league_catalog.get(league_id) or {
            "id": league_id,
            "name": club["league_name"],
            "country_id": club["country_id"],
            "tier": club["tier"],
            "tier_rank": club["tier_rank"],
        }
        if career.league_club_ids is None:
            career.league_id = league_id
            career.league_club_ids = [
                str(item["id"])
                for item in canon.clubs(league_id=league_id, limit=1000)
            ]
        clubs = []
        for club_id in career.league_club_ids:
            item = canon.club(str(club_id))
            if item is not None:
                clubs.append(item)
        if not any(str(item["id"]) == career.club_id for item in clubs):
            clubs.append(club)

        rank = int(league.get("tier_rank") or 0)
        same_country = [
            item
            for item in league_catalog.values()
            if item["country_id"] == league["country_id"] and int(item.get("tier_rank") or 0) != 99
        ]
        above_league = next(
            (item for item in same_country if int(item["tier_rank"]) == rank - 1), None
        )
        below_league = next(
            (item for item in same_country if int(item["tier_rank"]) == rank + 1), None
        )
        above2_league = next(
            (item for item in same_country if int(item["tier_rank"]) == rank - 2), None
        )
        below2_league = next(
            (item for item in same_country if int(item["tier_rank"]) == rank + 2), None
        )
        return {
            "league": league,
            "clubs": clubs,
            "above_league": above_league,
            "above_clubs": canon.clubs(league_id=above_league["id"], limit=1000)
            if above_league
            else [],
            "below_league": below_league,
            "below_clubs": canon.clubs(league_id=below_league["id"], limit=1000)
            if below_league
            else [],
            "above2_league": above2_league,
            "above2_clubs": canon.clubs(league_id=above2_league["id"], limit=1000)
            if above2_league
            else [],
            "below2_league": below2_league,
            "below2_clubs": canon.clubs(league_id=below2_league["id"], limit=1000)
            if below2_league
            else [],
        }

    def match_setup(career, context):
        ensure_schedule(career, context["clubs"])
        fixture = next_fixture(career)
        if fixture is None:
            raise HTTPException(status_code=422, detail="season is complete")
        if career.date < fixture["date"]:
            raise HTTPException(status_code=422, detail="advance to the match day first")

        clubs = {}
        for club_id in (fixture["home"], fixture["away"]):
            item = canon.club(club_id)
            if item is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"club {club_id} is missing from canon.db",
                )
            clubs[club_id] = item

        our_players = canon.players_by_ids(career.player_ids, with_stats=True)
        if not our_players:
            raise HTTPException(status_code=409, detail="career squad is missing from canon.db")
        ensure_player_states(career, [str(player["id"]) for player in our_players])
        recover_condition(career, career.date)
        blocked = blocked_player_ids(career)
        own_home = fixture["home"] == career.club_id
        home_players = our_players if own_home else canon.squad(fixture["home"])
        away_players = our_players if not own_home else canon.squad(fixture["away"])
        home_order = career.lineup if own_home else None
        home_bench = career.bench_order if own_home else None
        away_order = career.lineup if not own_home else None
        away_bench = career.bench_order if not own_home else None
        setup = build_match_setup(
            career,
            fixture,
            str(context["league"]["name"]),
            clubs,
            build_lineup(home_players, home_order, home_bench, blocked if own_home else None),
            build_lineup(away_players, away_order, away_bench, None if own_home else blocked),
        )
        return fixture, setup

    def prepare_own_lineup(career, players):
        ensure_player_states(career, [str(player["id"]) for player in players])
        recover_condition(career, career.date)
        blocked = blocked_player_ids(career)
        lineup = lineup_for(players, career.lineup, career.bench_order, blocked)
        career.lineup = [slot["player"]["id"] for slot in lineup["slots"]]
        career.bench_order = [player["id"] for player in lineup["bench"]]
        return lineup

    def play_own_match(career, context):
        players = canon.players_by_ids(career.player_ids, with_stats=True)
        if not players:
            raise HTTPException(status_code=409, detail="career squad is missing from canon.db")
        prepare_own_lineup(career, players)
        fixture, setup = match_setup(career, context)
        play_next_match(career, context["clubs"], strength_resolver(career, players))
        score = career.results.get(fixture["id"])
        if score is None:
            raise HTTPException(status_code=409, detail="match produced no result")
        match = build_match_simulation(career, fixture, setup, score)
        apply_match_outcome(career, fixture, setup, match)
        return fixture, setup, match

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
        context = division_context(career, club)
        league = context["league"]
        club_view = {
            **club,
            "league_id": league["id"],
            "league_name": league["name"],
            "tier": league["tier"],
            "tier_rank": league["tier_rank"],
        }
        strength_for = strength_resolver(career, players)
        result = build_snapshot(
            career,
            club_view,
            players,
            league_clubs=context["clubs"],
            strength_for=strength_for,
        )
        transition = season_transition(
            career,
            context["league"],
            context["clubs"],
            context["above_league"],
            context["above_clubs"],
            context["below_league"],
            context["below_clubs"],
            strength_for,
            above2_league=context["above2_league"],
            above2_clubs=context["above2_clubs"],
            below2_league=context["below2_league"],
            below2_clubs=context["below2_clubs"],
        )
        if transition is not None:
            result["season"]["review"] = transition["review"]
        return result

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
        league_clubs = canon.clubs(league_id=club["league_id"], limit=1000)
        career.league_id = str(club["league_id"])
        career.league_club_ids = [str(item["id"]) for item in league_clubs]
        ensure_schedule(career, league_clubs)
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
                league = league_catalog.get(career.league_id or str(club["league_id"]))
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
                        "league_name": league["name"] if league else club["league_name"],
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

    @app.get("/api/careers/{career_id}/match", response_model=MatchSetup)
    def match_preview(career_id: str):
        loaded = load_career(career_id)
        club = canon.club(loaded.club_id)
        if club is None:
            raise HTTPException(status_code=409, detail="career club is missing from canon.db")
        context = division_context(loaded, club)
        _, setup = match_setup(loaded, context)
        return setup

    @app.post("/api/careers/{career_id}/simulate", response_model=MatchSimulationResponse)
    def simulate_career(career_id: str):
        loaded = load_career(career_id)
        club = canon.club(loaded.club_id)
        if club is None:
            raise HTTPException(status_code=409, detail="career club is missing from canon.db")
        context = division_context(loaded, club)
        try:
            _, _, match = play_own_match(loaded, context)
        except SeasonError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        loaded.touch()
        saves.save(loaded)
        return {"career": snapshot(loaded), "match": match}

    @app.post("/api/careers/{career_id}/save", response_model=CareerSnapshot)
    def save_career(career_id: str):
        career = load_career(career_id)
        career.touch()
        saves.save(career)
        return snapshot(career)

    @app.post("/api/careers/{career_id}/actions", response_model=CareerSnapshot)
    def apply_action(career_id: str, payload: CareerActionRequest):
        career = load_career(career_id)
        if payload.type == "swap":
            if not payload.player_a or not payload.player_b:
                raise HTTPException(status_code=422, detail="swap requires player_a and player_b")
            players = canon.players_by_ids(career.player_ids)
            try:
                swap_players(career, players, payload.player_a, payload.player_b)
            except ActionError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        elif payload.type == "advance":
            if not payload.date:
                raise HTTPException(status_code=422, detail="advance requires date")
            club = canon.club(career.club_id)
            if club is None:
                raise HTTPException(status_code=409, detail="career club is missing from canon.db")
            context = division_context(career, club)
            try:
                advance_to(career, payload.date, context["clubs"])
            except SeasonError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
            recover_condition(career, career.date)
        elif payload.type == "next_season":
            club = canon.club(career.club_id)
            if club is None:
                raise HTTPException(status_code=409, detail="career club is missing from canon.db")
            context = division_context(career, club)
            strength_for = strength_resolver()
            transition = season_transition(
                career,
                context["league"],
                context["clubs"],
                context["above_league"],
                context["above_clubs"],
                context["below_league"],
                context["below_clubs"],
                strength_for,
                above2_league=context["above2_league"],
                above2_clubs=context["above2_clubs"],
                below2_league=context["below2_league"],
                below2_clubs=context["below2_clubs"],
            )
            try:
                if transition is None:
                    next_season(career, context["clubs"])
                else:
                    next_season(
                        career,
                        context["clubs"],
                        league_id=transition["league_id"],
                        next_league_clubs=transition["league_club_ids"],
                        transition=transition["review"],
                    )
            except SeasonError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        elif payload.type == "play":
            club = canon.club(career.club_id)
            if club is None:
                raise HTTPException(status_code=409, detail="career club is missing from canon.db")
            context = division_context(career, club)
            try:
                play_own_match(career, context)
            except SeasonError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        else:
            raise HTTPException(status_code=422, detail=f"unknown action type: {payload.type}")
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
