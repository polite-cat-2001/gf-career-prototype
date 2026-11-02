from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from server.canon import REPO_ROOT, Canon, age_from_birth_date, default_db_path
from server.career import (
    ActionError,
    SaveFormatError,
    SaveNotFound,
    SaveStore,
    SaveVersionError,
    SeasonError,
    accept_counter_offer,
    accept_incoming_offer,
    accept_offer_counter,
    accept_transfer_counter,
    acknowledge_contract_negotiation,
    acknowledge_incoming_offer,
    can_discuss_contract,
    add_to_shortlist,
    advance_to,
    counter_incoming_offer,
    execute_pending_departures,
    generate_incoming_offers,
    incoming_offer_view,
    refuse_incoming_offer,
    resolve_incoming_offers,
    build_lineup,
    build_match_setup,
    build_match_simulation,
    build_snapshot,
    confirm_contract,
    create_career,
    create_transfer_offer,
    ensure_schedule,
    execute_pending_transfers,
    negotiate_contract,
    next_fixture,
    next_season,
    offer_view,
    play_next_match,
    release_player,
    remove_from_shortlist,
    resolve_transfer_contracts,
    resolve_transfer_offers,
    season_transition,
    set_shirt_number,
    set_transfer_status,
    sign_transfer_contract,
    squad_strength,
    start_transfer_contract,
    swap_players,
    toggle_shortlist,
    transfer_contract_defaults,
    transfer_contract_view,
)
from server.career.condition import (
    apply_match_outcome,
    blocked_player_ids,
    ensure_player_states,
    recover_condition,
)
from server.career.scouting import (
    AGE_MAX,
    AGE_MIN,
    CONTRACT_MAX,
    CONTRACT_MIN,
    MAX_SCOUTS,
    REGION_SPECS,
    acknowledge_reports,
    advance_scouting,
    assign_player_report,
    ensure_scouts,
    hire_scout,
    normalize_criteria,
    remove_scouted,
    report_progress,
    scouted_ids,
    scouting_counts,
    scout_candidates,
    start_network,
    task_days,
    update_task,
)
from server.career.snapshot import lineup_for, lineup_strength
from server.career.world_market import (
    advance_world_market as run_world_market,
    effective_players,
)
from server.career.squad import (
    TRANSFER_STATUSES,
    contract_expiry_for,
    contract_months_for,
    ensure_player_contracts,
    ensure_player_finances,
    release_clause_for,
    resolve_negotiations,
    weekly_wage_for,
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
    clean_sheets: int = 0


class PlayerCompetitionStats(PlayerSeasonStats):
    id: str
    name: str


class PlayerContract(BaseModel):
    years: int
    weekly_wage: int
    release_clause: int


class ContractTerms(BaseModel):
    years: int
    weekly_wage: int
    squad_role: str
    release_clause: int


class PlayerNegotiation(BaseModel):
    status: str
    counter_offers: int = 0
    offer: ContractTerms | None = None
    counter: ContractTerms | None = None
    due: str | None = None
    acknowledged: bool = True
    affordable: bool = True
    message: str = ""


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
    competition_stats: list[PlayerCompetitionStats] | None = None
    available: bool = True
    stats: dict[str, float] | None = None
    squad_role: str | None = None
    squad_role_label: str | None = None
    squad_role_short: str | None = None
    expected_share: float | None = None
    actual_minutes: int = 0
    expected_minutes: int = 0
    morale: int = 100
    contract: PlayerContract | None = None
    transfer_status: str | None = None
    negotiation: PlayerNegotiation | None = None


class PlayerDetail(PlayerSummary):
    stats: dict[str, float]


class ScoutCriteria(BaseModel):
    role: str = ""
    age_min: int | None = None
    age_max: int | None = None
    contract_min: int | None = None
    contract_max: int | None = None


class ScoutTaskView(BaseModel):
    kind: str
    region_id: str
    region_name: str
    country_id: str
    country_name: str
    criteria: ScoutCriteria
    started_at: str
    days_worked: int
    found_count: int


class ScoutReportView(BaseModel):
    player_id: str
    player_name: str
    player_photo: str
    started_at: str
    due_at: str
    days_total: int
    days_left: int
    days_worked: int
    progress: float


class ScoutView(BaseModel):
    id: str
    name: str
    nationality: str
    nationality_id: str | None = None
    flag: str = ""
    experience: int
    judgement: int
    price: int
    task: ScoutTaskView | None = None
    report: ScoutReportView | None = None


class ScoutCandidate(BaseModel):
    id: str
    name: str
    nationality: str
    nationality_id: str | None = None
    flag: str = ""
    experience: int
    judgement: int
    price: int
    affordable: bool = True


class ScoutNetwork(BaseModel):
    region_id: str
    region_name: str
    country_id: str
    country_name: str
    created_at: str
    scout_id: str


class ScoutRegionCountry(BaseModel):
    id: str
    name: str
    flag: str


class ScoutRegion(BaseModel):
    id: str
    name: str
    x: float
    y: float
    countries: list[ScoutRegionCountry]


class ScoutEntry(BaseModel):
    player: dict
    kind: str
    scout_id: str
    scout_name: str
    date: str
    acknowledged: bool = False


class ScoutingCounts(BaseModel):
    new: int = 0
    updates: int = 0
    total: int = 0


class ScoutingBlock(BaseModel):
    scouts: list[ScoutView]
    candidates: list[ScoutCandidate]
    reports: list[ScoutEntry]
    recommendations: list[ScoutEntry]
    networks: list[ScoutNetwork]
    regions: list[ScoutRegion]
    counts: ScoutingCounts
    max_scouts: int
    age_min: int
    age_max: int
    contract_min: int
    contract_max: int


class TransferSearchResponse(BaseModel):
    items: list[dict]
    total: int
    limit: int
    offset: int
    has_more: bool


class TransferCenterBlock(BaseModel):
    shortlist: list[dict]
    sent_offers: list[dict] = Field(default_factory=list)
    received_offers: list[dict] = Field(default_factory=list)
    listed: list[dict] = Field(default_factory=list)
    loaned: list[dict] = Field(default_factory=list)
    pending: list[dict] = Field(default_factory=list)
    contracts: dict[str, dict] = Field(default_factory=dict)
    history: list[dict] = Field(default_factory=list)


class CreateCareerRequest(BaseModel):
    club_id: str
    manager_name: str = Field(min_length=1, max_length=80)
    manager_nationality_id: str
    seed: int | None = Field(default=None, ge=0, le=4_294_967_295)


class CareerActionRequest(BaseModel):
    type: str
    player_a: str | None = None
    player_b: str | None = None
    player_id: str | None = None
    date: str | None = None
    status: str | None = None
    number: int | None = None
    years: int | None = None
    weekly_wage: int | None = None
    squad_role: str | None = None
    release_clause: int | None = None
    scout_id: str | None = None
    region_id: str | None = None
    country_id: str | None = None
    criteria: dict | None = None
    offer_id: str | None = None
    amount: int | None = None
    loan_fee: int | None = None
    wage_share: int | None = None
    buyout: bool | None = None


class ManagerInfo(BaseModel):
    name: str
    nationality_id: str
    nationality: str


class SquadSummary(BaseModel):
    squad_size: int
    average_overall: float
    average_age: float | None = None
    total_market_value: int


class SquadFinance(BaseModel):
    balance: int
    total_market_value: int
    weekly_wage_bill: int


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
    finance: SquadFinance
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
    scouting: ScoutingBlock | None = None
    transfers: TransferCenterBlock | None = None


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

    world_clubs: list[dict] | None = None
    world_free_agents: list[dict] | None = None
    world_club_index: dict[str, dict] | None = None

    def club_index() -> dict[str, dict]:
        nonlocal world_clubs, world_club_index
        if world_club_index is None:
            if world_clubs is None:
                world_clubs = canon.clubs(limit=10_000)
            world_club_index = {str(club["id"]): club for club in world_clubs}
        return world_club_index

    def effective_squad(career, club_id: str, with_stats: bool = False) -> list[dict]:
        base = canon.squad(club_id)
        return effective_players(
            career,
            club_id,
            base,
            lambda player_ids: canon.players_by_ids(player_ids, with_stats=with_stats),
        )

    def advance_world_market(career) -> list[dict]:
        nonlocal world_clubs, world_free_agents
        if world_clubs is None:
            world_clubs = canon.clubs(limit=10_000)
        if world_free_agents is None:
            world_free_agents = canon.free_agents(limit=2_000)
        return run_world_market(
            career,
            world_clubs,
            canon.squads_for_clubs,
            world_free_agents,
            player_lookup=canon.players_by_ids,
        )

    def load_career(career_id: str):
        try:
            career = saves.load(career_id)
        except SaveNotFound as error:
            raise HTTPException(status_code=404, detail="career save not found") from error
        except SaveVersionError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except SaveFormatError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        resolve_negotiations(career)
        resolve_transfer_offers(career)
        resolve_transfer_contracts(career)
        advance_incoming_offers(career)
        resolve_incoming_offers(career)
        execute_pending_transfers(career)
        execute_pending_departures(career)
        advance_world_market(career)
        return career

    def strength_resolver(career=None, players=None):
        cache: dict[str, float] = {}

        def resolve(club_id: str) -> float:
            if club_id not in cache:
                if career is not None and players and club_id == career.club_id:
                    cache[club_id] = lineup_strength(career, players)
                elif career is not None:
                    cache[club_id] = squad_strength(
                        effective_squad(career, club_id)
                    )
                else:
                    cache[club_id] = squad_strength(canon.squad(club_id))
            return cache[club_id]

        return resolve

    league_catalog = {str(league["id"]): league for league in canon.leagues()}

    countries_catalog = {str(country["id"]): country for country in canon.countries()}
    country_by_name = {
        str(country["name"]): country for country in countries_catalog.values()
    }
    regions = []
    for spec in REGION_SPECS:
        members = []
        for name in spec["countries"]:
            country = country_by_name.get(name)
            if country is None:
                continue
            members.append(
                {
                    "id": str(country["id"]),
                    "name": str(country["name"]),
                    "flag": str(country["flag"]),
                }
            )
        if members:
            regions.append(
                {
                    "id": spec["id"],
                    "name": spec["name"],
                    "x": spec["x"],
                    "y": spec["y"],
                    "countries": members,
                }
            )
    region_by_id = {region["id"]: region for region in regions}

    club_catalog: list[dict] | None = None
    club_roles: dict[str, dict[str, dict]] | None = None

    def incoming_market() -> tuple[list[dict], dict[str, dict[str, dict]]]:
        nonlocal club_catalog, club_roles
        if club_catalog is None:
            club_catalog = canon.clubs(limit=10_000)
        if club_roles is None:
            club_roles = canon.club_role_stats()
        return club_catalog, club_roles

    def advance_incoming_offers(career) -> None:
        players = canon.players_by_ids(career.player_ids)
        previous_date = career.incoming_market_date or career.date
        if players and previous_date < career.date:
            catalog, roles = incoming_market()
            generate_incoming_offers(
                career,
                previous_date,
                career.date,
                players,
                catalog,
                roles,
            )
        career.incoming_market_date = career.date
        execute_pending_departures(career)

    def latest_offer_payload(career, player_id: str) -> dict | None:
        player_id = str(player_id)
        for offer in reversed(career.transfer_offers):
            if str(offer.get("player_id")) != player_id:
                continue
            status = str(offer.get("status") or "")
            signed = bool(offer.get("signed"))
            return {
                "offer_id": str(offer.get("id") or ""),
                "kind": str(offer.get("kind") or "transfer"),
                "status": status,
                "signed": signed,
                "execute_on": offer.get("execute_on"),
                "can_negotiate": status == "accepted" and not signed,
            }
        return None

    def scouting_player(career, player_id: str) -> dict | None:
        player = canon.player(str(player_id))
        if player is None:
            return None
        club = canon.club(str(player["club_id"])) if player.get("club_id") else None
        status = career.player_transfers.get(str(player_id))
        if status is None:
            status = "free" if not player.get("club_id") else "contracted"
        return {
            "id": str(player["id"]),
            "name": player["name"],
            "first_name": player.get("first_name"),
            "last_name": player.get("last_name"),
            "age": age_from_birth_date(player.get("birth_date"), career.date),
            "height": player.get("height"),
            "citizenship": player.get("citizenship") or [],
            "position": player.get("position") or "",
            "role": player.get("role"),
            "club_id": player.get("club_id"),
            "club_name": club["name"] if club else None,
            "club_logo": club["logo"] if club else None,
            "league_id": club["league_id"] if club else None,
            "league_name": club["league_name"] if club else None,
            "country_id": club["country_id"] if club else None,
            "country_name": club["country_name"] if club else None,
            "release_clause": release_clause_for(career, player, player["id"]),
            "status": status,
            "photo": player["photo"],
            "scouted": True,
            "shortlisted": str(player_id) in career.shortlist,
            "contract_expires": contract_expiry_for(career, player, player["id"]),
            "foot": player.get("foot"),
            "overall": player.get("overall"),
            "pot": player.get("pot"),
            "stats": player.get("stats"),
            "weekly_wage": weekly_wage_for(career, player, player["id"]),
            "market_value": player.get("market_value"),
            "weak_foot": player.get("weak_foot"),
            "skill_moves": player.get("skill_moves"),
            "latest_offer": latest_offer_payload(career, player_id),
        }

    def scouting_candidates(career, country_id: str, criteria: dict) -> list[dict]:
        players, _ = canon.search_players(
            country_id=str(country_id),
            group=criteria.get("role") or None,
            age_min=criteria.get("age_min"),
            age_max=criteria.get("age_max"),
            limit=200,
            sort="overall",
            direction="desc",
            ref_date=career.date,
        )
        for player in players:
            player["contract_months"] = contract_months_for(
                career, player, player["id"]
            )
        return players

    def scouting_snapshot(career) -> dict:
        ensure_scouts(career)
        cache: dict[str, dict | None] = {}
        scouts_by_id = {str(scout["id"]): scout for scout in career.scouts}

        def player_view(player_id: str, reveal: bool = True) -> dict | None:
            key = str(player_id)
            if key not in cache:
                cache[key] = scouting_player(career, key)
            player = cache[key]
            if player is None:
                return None
            if reveal:
                return player
            hidden = {
                key: value
                for key, value in player.items()
                if key
                not in {
                    "overall",
                    "pot",
                    "stats",
                    "weekly_wage",
                    "market_value",
                    "foot",
                    "weak_foot",
                    "skill_moves",
                }
            }
            hidden["scouted"] = False
            return hidden

        def scout_view(scout: dict) -> dict:
            scout_id = str(scout["id"])
            country = country_by_name.get(str(scout.get("nationality") or ""))
            task = career.scout_tasks.get(scout_id)
            task_view = None
            if task is not None:
                task_view = {
                    "kind": str(task.get("kind") or "network"),
                    "region_id": str(task.get("region_id") or ""),
                    "region_name": str(task.get("region_name") or ""),
                    "country_id": str(task.get("country_id") or ""),
                    "country_name": str(task.get("country_name") or ""),
                    "criteria": normalize_criteria(task.get("criteria")),
                    "started_at": str(task.get("started_at") or career.date),
                    "days_worked": task_days(career, task),
                    "found_count": len(task.get("found") or []),
                }
            report = career.scout_assignments.get(scout_id)
            report_view = None
            if report is not None:
                progress = report_progress(career, report)
                player = player_view(str(report.get("player_id")), reveal=False)
                report_view = {
                    "player_id": str(report.get("player_id")),
                    "player_name": player["name"] if player else "",
                    "player_photo": player["photo"] if player else "",
                    "started_at": str(report.get("started_at") or career.date),
                    "due_at": str(report.get("due_at") or career.date),
                    "days_total": progress["days_total"],
                    "days_left": progress["days_left"],
                    "days_worked": progress["days_worked"],
                    "progress": round(
                        progress["days_worked"] / max(1, progress["days_total"]), 3
                    ),
                }
            return {
                "id": scout_id,
                "name": str(scout.get("name") or ""),
                "nationality": str(scout.get("nationality") or ""),
                "nationality_id": country["id"] if country else None,
                "flag": country["flag"] if country else "",
                "experience": int(scout.get("experience") or 1),
                "judgement": int(scout.get("judgement") or 1),
                "price": int(scout.get("price") or 0),
                "task": task_view,
                "report": report_view,
            }

        candidates = []
        for candidate in scout_candidates(career):
            country = country_by_name.get(str(candidate.get("nationality") or ""))
            price = int(candidate.get("price") or 0)
            candidates.append(
                {
                    "id": str(candidate["id"]),
                    "name": str(candidate["name"]),
                    "nationality": str(candidate["nationality"]),
                    "nationality_id": country["id"] if country else None,
                    "flag": country["flag"] if country else "",
                    "experience": int(candidate.get("experience") or 1),
                    "judgement": int(candidate.get("judgement") or 1),
                    "price": price,
                    "affordable": career.balance is None
                    or int(career.balance) >= price,
                }
            )

        def entry(player_id: str, data: dict, kind: str, stamp: str) -> dict | None:
            player = player_view(player_id)
            if player is None:
                return None
            scout = scouts_by_id.get(str(data.get("scout_id")))
            return {
                "player": player,
                "kind": kind,
                "scout_id": str(data.get("scout_id") or ""),
                "scout_name": str(scout.get("name") or "") if scout else "",
                "date": str(stamp),
                "acknowledged": bool(data.get("acknowledged")),
            }

        reports = [
            entry(player_id, data, "report", data.get("completed_at") or career.date)
            for player_id, data in career.scout_reports.items()
        ]
        recommendations = [
            entry(player_id, data, "recommendation", data.get("found_at") or career.date)
            for player_id, data in career.scout_found.items()
        ]
        reports = [item for item in reports if item is not None]
        recommendations = [item for item in recommendations if item is not None]
        reports.sort(key=lambda item: (item["date"], item["player"]["name"]), reverse=True)
        recommendations.sort(
            key=lambda item: (item["date"], item["player"]["name"]), reverse=True
        )

        return {
            "scouts": [scout_view(scout) for scout in career.scouts],
            "candidates": candidates,
            "reports": reports,
            "recommendations": recommendations,
            "networks": [dict(network) for network in career.scout_networks],
            "regions": regions,
            "counts": scouting_counts(career),
            "max_scouts": MAX_SCOUTS,
            "age_min": AGE_MIN,
            "age_max": AGE_MAX,
            "contract_min": CONTRACT_MIN,
            "contract_max": CONTRACT_MAX,
        }

    def transfer_contract_payload(career, player: dict, squad_players: list[dict]) -> dict:
        player_id = str(player["id"])
        if player_id in career.player_ids:
            return {"can_discuss": False}
        can_discuss = can_discuss_contract(career, player)
        return {
            "transfer_contract": transfer_contract_view(career, player_id),
            "contract_defaults": transfer_contract_defaults(
                career, player, squad_players
            ),
            "can_discuss": can_discuss,
            "latest_offer": latest_offer_payload(career, player_id),
        }

    def transfer_history_entries(career, scope: str = "all") -> list[dict]:
        clubs = club_index()
        player_ids = {
            str(record.get("player_id") or "")
            for record in (
                career.world_transfers
                + career.transfer_history
                + career.transfer_offers
                + career.incoming_offers
            )
            if record.get("player_id")
        }
        players = {
            str(player["id"]): player
            for player in canon.players_by_ids(sorted(player_ids))
        }
        manager_club_id = str(career.club_id)
        manager_league_id = str(career.league_id or "")

        def club_ref(club_id) -> dict:
            if not club_id:
                return {}
            return clubs.get(str(club_id)) or {}

        def entry(record: dict) -> dict:
            player_id = str(record.get("player_id") or "")
            player = players.get(player_id) or {}
            from_club = club_ref(record.get("from_club_id"))
            to_club = club_ref(record.get("to_club_id"))
            from_id = None if not record.get("from_club_id") else str(record["from_club_id"])
            to_id = None if not record.get("to_club_id") else str(record["to_club_id"])
            from_league = str(from_club.get("league_id") or "")
            to_league = str(to_club.get("league_id") or "")
            overall = record.get("overall")
            if overall is None:
                overall = player.get("overall") or 0
            with_manager = manager_club_id in (from_id, to_id)
            in_my_league = bool(manager_league_id) and manager_league_id in (
                from_league,
                to_league,
            )
            return {
                "id": str(record.get("id") or record.get("offer_id") or player_id),
                "player_id": player_id,
                "player_name": str(
                    player.get("name") or record.get("player_name") or ""
                ),
                "photo": player.get("photo"),
                "role": player.get("role"),
                "age": player.get("age"),
                "overall": round(float(overall or 0), 1),
                "from_club_id": from_id,
                "from_club_name": str(from_club.get("name") or ""),
                "from_club_logo": str(from_club.get("logo") or ""),
                "from_league_id": from_league or None,
                "from_league_name": str(from_club.get("league_name") or ""),
                "to_club_id": to_id,
                "to_club_name": str(to_club.get("name") or ""),
                "to_club_logo": str(to_club.get("logo") or ""),
                "to_league_id": to_league or None,
                "to_league_name": str(to_club.get("league_name") or ""),
                "fee": int(record.get("fee") or 0),
                "kind": str(record.get("kind") or "transfer"),
                "status": str(record.get("status") or "completed"),
                "source": str(record.get("source") or "world"),
                "date": str(record.get("date") or "")[:10],
                "with_manager": with_manager,
                "in_my_league": in_my_league,
            }

        entries = [
            entry({**transfer, "source": "world"})
            for transfer in career.world_transfers
        ]
        entries.extend(
            entry({**record, "source": "manager"})
            for record in career.transfer_history
        )
        settled_offers = {
            str(record.get("offer_id"))
            for record in career.transfer_history
            if record.get("offer_id")
        }
        for offer in career.transfer_offers:
            if str(offer.get("id")) in settled_offers:
                continue
            player = players.get(str(offer.get("player_id") or "")) or {}
            fee = (
                int(offer.get("loan_fee") or 0)
                if str(offer.get("kind")) == "loan"
                else int(offer.get("amount") or 0)
            )
            entries.append(
                entry(
                    {
                        "id": str(offer.get("id") or ""),
                        "player_id": str(offer.get("player_id") or ""),
                        "overall": offer.get("overall", player.get("overall")),
                        "from_club_id": player.get("club_id"),
                        "to_club_id": manager_club_id,
                        "fee": fee,
                        "kind": str(offer.get("kind") or "transfer"),
                        "status": str(offer.get("status") or "pending"),
                        "source": "sent",
                        "date": offer.get("created_at"),
                    }
                )
            )
        for offer in career.incoming_offers:
            if str(offer.get("id")) in settled_offers:
                continue
            player = players.get(str(offer.get("player_id") or "")) or {}
            entries.append(
                entry(
                    {
                        "id": str(offer.get("id") or ""),
                        "player_id": str(offer.get("player_id") or ""),
                        "overall": offer.get("overall", player.get("overall")),
                        "from_club_id": offer.get("club_id"),
                        "to_club_id": manager_club_id,
                        "fee": int(offer.get("amount") or 0),
                        "kind": str(offer.get("kind") or "transfer"),
                        "status": str(offer.get("status") or "pending"),
                        "source": "received",
                        "date": offer.get("created_at"),
                    }
                )
            )

        if scope == "league":
            entries = [item for item in entries if item["in_my_league"]]
        elif scope == "club":
            entries = [item for item in entries if item["with_manager"]]
        entries.sort(key=lambda item: (item["date"], item["id"]), reverse=True)
        entries.sort(key=lambda item: -float(item["overall"] or 0))
        return entries

    def transfer_center_snapshot(career) -> dict:
        scouts_by_id = {str(scout["id"]): scout for scout in career.scouts}
        squad_players = canon.players_by_ids(career.player_ids)

        revealed = scouted_ids(career)

        def entry(player_id: str, reveal: bool | None = None) -> dict | None:
            player_id = str(player_id)
            player = scouting_player(career, player_id)
            if player is None:
                return None
            if reveal is None:
                reveal = player_id in revealed
            if not reveal:
                for hidden in (
                    "overall",
                    "pot",
                    "stats",
                    "weekly_wage",
                    "market_value",
                    "foot",
                    "weak_foot",
                    "skill_moves",
                ):
                    player.pop(hidden, None)
                player["scouted"] = False
            player["shortlisted"] = player_id in career.shortlist
            player.update(transfer_contract_payload(career, player, squad_players))
            assignment = next(
                (
                    report
                    for report in career.scout_assignments.values()
                    if str(report.get("player_id")) == player_id
                ),
                None,
            )
            if assignment is not None:
                progress = report_progress(career, assignment)
                scout = scouts_by_id.get(str(assignment.get("scout_id")))
                player["scouting_state"] = "studying"
                player["scouting_days_left"] = progress["days_left"]
                player["scouting_scout_name"] = str(scout.get("name") or "") if scout else ""
            elif player_id in career.scout_reports:
                player["scouting_state"] = "reported"
            elif player_id in career.scout_found:
                player["scouting_state"] = "found"
            else:
                player["scouting_state"] = "none"
            negotiation = career.negotiations.get(player_id)
            player["negotiation_status"] = (
                str(negotiation.get("status")) if isinstance(negotiation, dict) else None
            )
            return player

        def collect(player_ids, reveal: bool | None = None) -> list[dict]:
            result = []
            for player_id in player_ids:
                player = entry(player_id, reveal)
                if player is not None:
                    result.append(player)
            return result

        sent_offers = []
        for offer in reversed(career.transfer_offers):
            player = entry(str(offer.get("player_id") or ""))
            if player is None:
                continue
            player.update(offer_view(career, offer))
            sent_offers.append(player)

        received_offers = []
        for offer in reversed(career.incoming_offers):
            player = entry(str(offer.get("player_id") or ""), True)
            if player is None:
                continue
            player.update(incoming_offer_view(career, offer))
            received_offers.append(player)

        return {
            "shortlist": collect(career.shortlist),
            "sent_offers": sent_offers,
            "received_offers": received_offers,
            "listed": collect(
                (
                    player_id
                    for player_id, status in career.player_transfers.items()
                    if status == "transfer"
                ),
                reveal=True,
            ),
            "loaned": collect(
                (
                    player_id
                    for player_id, status in career.player_transfers.items()
                    if status == "loan"
                ),
                reveal=True,
            ),
            "pending": [dict(item) for item in career.pending_transfers],
            "contracts": {
                str(player_id): transfer_contract_view(career, player_id) or {}
                for player_id in career.transfer_contracts
            },
            "history": transfer_history_entries(career),
        }

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
        home_players = (
            our_players if own_home else effective_squad(career, fixture["home"])
        )
        away_players = (
            our_players if not own_home else effective_squad(career, fixture["away"])
        )
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
        ensure_player_contracts(career, players)
        prepare_own_lineup(career, players)
        fixture, setup = match_setup(career, context)
        play_next_match(career, context["clubs"], strength_resolver(career, players))
        score = career.results.get(fixture["id"])
        if score is None:
            raise HTTPException(status_code=409, detail="match produced no result")
        match = build_match_simulation(career, fixture, setup, score)
        apply_match_outcome(
            career,
            fixture,
            setup,
            match,
            competition_id=str(context["league"]["id"]),
        )
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
        result["scouting"] = scouting_snapshot(career)
        result["transfers"] = transfer_center_snapshot(career)
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

    @app.get(
        "/api/careers/{career_id}/transfers/search",
        response_model=TransferSearchResponse,
    )
    def transfer_search(
        career_id: str,
        name: str | None = None,
        group: str | None = None,
        position: str | None = None,
        age_min: int | None = Query(None, ge=0, le=99),
        age_max: int | None = Query(None, ge=0, le=99),
        citizenship: str | None = None,
        country_id: str | None = None,
        league_id: str | None = None,
        club_id: str | None = None,
        foot: str | None = None,
        height_min: int | None = Query(None, ge=100, le=250),
        height_max: int | None = Query(None, ge=100, le=250),
        status: str | None = None,
        sort: str = "name",
        direction: str = "asc",
        limit: int = Query(40, ge=1, le=100),
        offset: int = Query(0, ge=0),
    ):
        career = load_career(career_id)
        free_only = status == "free"
        only_ids = None
        if status in TRANSFER_STATUSES:
            only_ids = [
                player_id
                for player_id, value in career.player_transfers.items()
                if value == status
            ]
        players, total = canon.search_players(
            name=(name or "").strip() or None,
            group=group or None,
            position=position or None,
            age_min=age_min,
            age_max=age_max,
            citizenship=citizenship or None,
            country_id=country_id or None,
            league_id=league_id or None,
            club_id=club_id or None,
            foot=foot or None,
            height_min=height_min,
            height_max=height_max,
            free_only=free_only,
            only_ids=only_ids,
            sort=sort,
            direction=direction,
            limit=limit,
            offset=offset,
            ref_date=career.date,
        )
        items = []
        revealed = scouted_ids(career)
        squad_players = canon.players_by_ids(career.player_ids)
        for player in players:
            target_status = career.player_transfers.get(player["id"])
            if target_status is None:
                target_status = "free" if not player["club_id"] else "contracted"
            item = {
                **player,
                "release_clause": release_clause_for(career, player, player["id"]),
                "status": target_status,
                "contract_expires": contract_expiry_for(
                    career, player, player["id"]
                ),
                "scouted": str(player["id"]) in revealed,
                "shortlisted": str(player["id"]) in career.shortlist,
            }
            if item["scouted"]:
                item["weekly_wage"] = weekly_wage_for(career, player, player["id"])
            else:
                for hidden in (
                    "overall",
                    "pot",
                    "stats",
                    "weekly_wage",
                    "market_value",
                    "foot",
                    "weak_foot",
                    "skill_moves",
                ):
                    item.pop(hidden, None)
            item.update(transfer_contract_payload(career, player, squad_players))
            items.append(item)
        return {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(items) < total,
        }

    @app.get("/api/careers/{career_id}/transfers/history")
    def transfer_history(
        career_id: str,
        filter: str = "all",
        scope: str | None = None,
    ):
        chosen = (scope or filter or "all").strip().lower()
        if chosen not in ("all", "league", "club"):
            raise HTTPException(
                status_code=422,
                detail="filter must be one of: all, league, club",
            )
        career = load_career(career_id)
        items = transfer_history_entries(career, chosen)
        return {"items": items, "total": len(items), "filter": chosen}

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
        ensure_player_contracts(career, squad)
        ensure_player_finances(career, squad)
        ensure_scouts(career)
        advance_world_market(career)
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
            advance_world_market(career)
            recover_condition(career, career.date)
            advance_scouting(
                career,
                lambda country_id, criteria: scouting_candidates(
                    career, country_id, criteria
                ),
            )
            advance_incoming_offers(career)
            resolve_transfer_offers(career)
            resolve_transfer_contracts(career)
            execute_pending_transfers(career)
        elif payload.type == "next_season":
            club = canon.club(career.club_id)
            if club is None:
                raise HTTPException(status_code=409, detail="career club is missing from canon.db")
            context = division_context(career, club)
            players = canon.players_by_ids(career.player_ids)
            strength_for = strength_resolver(career, players)
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
                    next_season(career, context["clubs"], players=players)
                else:
                    next_season(
                        career,
                        context["clubs"],
                        league_id=transition["league_id"],
                        next_league_clubs=transition["league_club_ids"],
                        transition=transition["review"],
                        players=players,
                    )
            except SeasonError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
            career.incoming_market_date = career.date
            execute_pending_transfers(career)
            execute_pending_departures(career)
            advance_world_market(career)
        elif payload.type == "play":
            club = canon.club(career.club_id)
            if club is None:
                raise HTTPException(status_code=409, detail="career club is missing from canon.db")
            context = division_context(career, club)
            try:
                play_own_match(career, context)
            except SeasonError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        elif payload.type in {
            "transfer_status",
            "shirt_number",
            "release_player",
            "negotiate",
            "accept_counter",
            "sign_contract",
            "ack_negotiation",
        }:
            if not payload.player_id:
                raise HTTPException(status_code=422, detail=f"{payload.type} requires player_id")
            players = canon.players_by_ids(career.player_ids)
            try:
                if payload.type == "transfer_status":
                    set_transfer_status(career, players, payload.player_id, payload.status)
                elif payload.type == "shirt_number":
                    set_shirt_number(career, players, payload.player_id, payload.number)
                elif payload.type == "release_player":
                    release_player(career, payload.player_id)
                elif payload.type == "negotiate":
                    negotiate_contract(
                        career,
                        players,
                        payload.player_id,
                        {
                            "years": payload.years,
                            "weekly_wage": payload.weekly_wage,
                            "squad_role": payload.squad_role,
                            "release_clause": payload.release_clause,
                        },
                    )
                elif payload.type == "accept_counter":
                    accept_counter_offer(career, players, payload.player_id)
                elif payload.type == "ack_negotiation":
                    acknowledge_contract_negotiation(career, players, payload.player_id)
                else:
                    confirm_contract(career, players, payload.player_id)
            except ActionError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        elif payload.type in {"transfer_offer", "loan_offer"}:
            if not payload.player_id:
                raise HTTPException(
                    status_code=422, detail=f"{payload.type} requires player_id"
                )
            player = canon.player(str(payload.player_id))
            if player is None:
                raise HTTPException(status_code=422, detail="player not found")
            player = {
                **player,
                "release_clause": release_clause_for(
                    career, player, player["id"]
                ),
            }
            try:
                create_transfer_offer(
                    career,
                    player,
                    kind="loan" if payload.type == "loan_offer" else "transfer",
                    amount=payload.amount,
                    loan_fee=payload.loan_fee,
                    wage_share=payload.wage_share,
                    buyout=bool(payload.buyout),
                )
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        elif payload.type == "accept_offer_counter":
            if not payload.offer_id:
                raise HTTPException(
                    status_code=422, detail="accept_offer_counter requires offer_id"
                )
            try:
                accept_offer_counter(career, payload.offer_id)
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        elif payload.type in {
            "transfer_contract",
            "transfer_accept_counter",
            "transfer_sign",
        }:
            if not payload.player_id:
                raise HTTPException(
                    status_code=422, detail=f"{payload.type} requires player_id"
                )
            player = canon.player(str(payload.player_id))
            if player is None:
                raise HTTPException(status_code=422, detail="player not found")
            squad_players = canon.players_by_ids(career.player_ids)
            try:
                if payload.type == "transfer_contract":
                    offer = None
                    if payload.offer_id:
                        offer = next(
                            (
                                item
                                for item in career.transfer_offers
                                if str(item.get("id")) == str(payload.offer_id)
                            ),
                            None,
                        )
                        if offer is None:
                            raise ValueError("offer not found")
                    start_transfer_contract(
                        career,
                        player,
                        {
                            "years": payload.years,
                            "weekly_wage": payload.weekly_wage,
                            "squad_role": payload.squad_role,
                            "release_clause": payload.release_clause,
                        },
                        offer=offer,
                        squad_players=squad_players,
                    )
                elif payload.type == "transfer_accept_counter":
                    accept_transfer_counter(career, payload.player_id)
                else:
                    sign_transfer_contract(career, player)
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        elif payload.type in {
            "incoming_accept",
            "accept_incoming_offer",
            "incoming_offer_accept",
            "incoming_refuse",
            "refuse_incoming_offer",
            "reject_incoming_offer",
            "incoming_offer_refuse",
            "incoming_counter",
            "counter_incoming_offer",
            "incoming_offer_counter",
            "incoming_ack",
            "ack_incoming_offer",
            "acknowledge_incoming_offer",
        }:
            if not payload.offer_id:
                raise HTTPException(
                    status_code=422, detail=f"{payload.type} requires offer_id"
                )
            try:
                if payload.type in {
                    "incoming_accept",
                    "accept_incoming_offer",
                    "incoming_offer_accept",
                }:
                    accept_incoming_offer(career, payload.offer_id)
                elif payload.type in {
                    "incoming_refuse",
                    "refuse_incoming_offer",
                    "reject_incoming_offer",
                    "incoming_offer_refuse",
                }:
                    refuse_incoming_offer(career, payload.offer_id)
                elif payload.type in {
                    "incoming_counter",
                    "counter_incoming_offer",
                    "incoming_offer_counter",
                }:
                    counter_incoming_offer(
                        career, payload.offer_id, int(payload.amount or 0)
                    )
                else:
                    acknowledge_incoming_offer(career, payload.offer_id)
            except ValueError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
        elif payload.type in {"shortlist_add", "shortlist_remove", "shortlist_toggle"}:
            if not payload.player_id:
                raise HTTPException(
                    status_code=422, detail=f"{payload.type} requires player_id"
                )
            if canon.player(str(payload.player_id)) is None:
                raise HTTPException(status_code=422, detail="player not found")
            if payload.type == "shortlist_add":
                add_to_shortlist(career, payload.player_id)
            elif payload.type == "shortlist_remove":
                remove_from_shortlist(career, payload.player_id)
            else:
                toggle_shortlist(career, payload.player_id)
        elif payload.type in {
            "scout_hire",
            "scout_assign",
            "scout_network",
            "scout_task",
            "scout_remove",
            "scout_ack",
        }:
            players = canon.players_by_ids(career.player_ids)
            ensure_player_finances(career, players)
            try:
                if payload.type == "scout_hire":
                    if not payload.scout_id:
                        raise ValueError("scout_hire requires scout_id")
                    hire_scout(career, payload.scout_id)
                elif payload.type == "scout_assign":
                    if not payload.scout_id or not payload.player_id:
                        raise ValueError(
                            "scout_assign requires scout_id and player_id"
                        )
                    if str(payload.player_id) in career.player_ids:
                        raise ValueError("you cannot scout your own player")
                    if canon.player(str(payload.player_id)) is None:
                        raise ValueError("player not found")
                    assign_player_report(career, payload.scout_id, payload.player_id)
                elif payload.type == "scout_network":
                    if not payload.scout_id or not payload.region_id or not payload.country_id:
                        raise ValueError(
                            "scout_network requires scout_id, region_id and country_id"
                        )
                    region = region_by_id.get(str(payload.region_id))
                    if region is None:
                        raise ValueError("region not found")
                    country = next(
                        (
                            item
                            for item in region["countries"]
                            if str(item["id"]) == str(payload.country_id)
                        ),
                        None,
                    )
                    if country is None:
                        raise ValueError("country is not in this region")
                    start_network(
                        career,
                        payload.scout_id,
                        region["id"],
                        country["id"],
                        region["name"],
                        country["name"],
                        payload.criteria,
                    )
                elif payload.type == "scout_task":
                    if not payload.scout_id:
                        raise ValueError("scout_task requires scout_id")
                    update_task(career, payload.scout_id, payload.criteria)
                elif payload.type == "scout_remove":
                    if not payload.player_id:
                        raise ValueError("scout_remove requires player_id")
                    remove_scouted(career, payload.player_id)
                else:
                    acknowledge_reports(career)
            except ValueError as error:
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
