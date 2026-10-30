from __future__ import annotations

import random
from datetime import date, timedelta

from server.career.core import Career
from server.career.squad import role_share

FATIGUE_PER_MATCH = 35
FATIGUE_PER_SUB = 15
FATIGUE_RECOVERY_PER_DAY = 4
YELLOW_SUSPENSION_THRESHOLD = 5

STAT_KEYS = (
    "apps",
    "starts",
    "minutes",
    "goals",
    "assists",
    "yellow",
    "red",
    "clean_sheets",
)
DEFAULT_COMPETITION = "league"
INJURY_TYPES = ("Мышца", "Связки", "Голеностоп", "Колено", "Бедро")
INJURY_DAYS = (7, 10, 14, 21, 28)


def empty_stats() -> dict[str, int]:
    return {key: 0 for key in STAT_KEYS}


def default_player_state() -> dict:
    return {
        "fatigue": 100,
        "injury": None,
        "suspension": None,
        "stats": empty_stats(),
        "stats_by_competition": {},
        "available_matches": 0,
        "expected_minutes": 0,
    }


def competition_key(career: Career, competition_id: str | None = None) -> str:
    return str(competition_id or career.league_id or DEFAULT_COMPETITION)


def competition_stats(state: dict, competition_id: str) -> dict:
    blocks = state.setdefault("stats_by_competition", {})
    block = blocks.setdefault(str(competition_id), {})
    for key in STAT_KEYS:
        block.setdefault(key, 0)
    return block


def ensure_player_states(career: Career, player_ids: list[str]) -> None:
    current = competition_key(career)
    for player_id in player_ids:
        state = career.player_state.setdefault(str(player_id), default_player_state())
        state.setdefault("fatigue", 100)
        state.setdefault("injury", None)
        state.setdefault("suspension", None)
        state.setdefault("available_matches", 0)
        state.setdefault("expected_minutes", 0)
        stats = state.setdefault("stats", empty_stats())
        for key in STAT_KEYS:
            stats.setdefault(key, 0)
        blocks = state.setdefault("stats_by_competition", {})
        if current not in blocks:
            blocks[current] = {key: int(stats.get(key) or 0) for key in STAT_KEYS}
        for block in blocks.values():
            if not isinstance(block, dict):
                continue
            for key in STAT_KEYS:
                block.setdefault(key, 0)
    if career.condition_date is None:
        career.condition_date = career.date


def recover_condition(career: Career, target_date: str) -> None:
    if not career.player_state:
        career.condition_date = target_date
        return
    if career.condition_date is None:
        career.condition_date = target_date
        return
    elapsed = (date.fromisoformat(target_date) - date.fromisoformat(career.condition_date)).days
    if elapsed <= 0:
        return
    for state in career.player_state.values():
        fatigue = int(state.get("fatigue") or 0)
        state["fatigue"] = min(100, fatigue + FATIGUE_RECOVERY_PER_DAY * elapsed)
        injury = state.get("injury")
        if injury and str(injury.get("until") or "") <= target_date:
            state["injury"] = None
    career.condition_date = target_date


def blocked_player_ids(career: Career, target_date: str | None = None) -> set[str]:
    if target_date is not None:
        recover_condition(career, target_date)
    blocked: set[str] = set()
    for player_id, state in career.player_state.items():
        if state.get("injury"):
            blocked.add(player_id)
            continue
        suspension = state.get("suspension")
        if suspension and int(suspension.get("matches") or 0) > 0:
            blocked.add(player_id)
    return blocked


def is_available(career: Career, player_id: str) -> bool:
    state = career.player_state.get(str(player_id)) or default_player_state()
    if state.get("injury"):
        return False
    suspension = state.get("suspension")
    return not suspension or int(suspension.get("matches") or 0) <= 0


def fatigue_factor(fatigue: int | float) -> float:
    return 0.75 + 0.25 * (max(0.0, min(100.0, float(fatigue))) / 100.0)


def effective_overall(player: dict, state: dict | None) -> float:
    fatigue = 100 if state is None else int(state.get("fatigue") or 0)
    return round(float(player.get("overall") or 0) * fatigue_factor(fatigue), 1)


def player_view(player: dict, state: dict) -> dict:
    stats = state.get("stats") or empty_stats()
    return {
        "fatigue": int(state.get("fatigue") or 0),
        "injury": state.get("injury"),
        "suspension": state.get("suspension"),
        "season_stats": {key: int(stats.get(key) or 0) for key in STAT_KEYS},
        "available": not state.get("injury")
        and int((state.get("suspension") or {}).get("matches") or 0) <= 0,
    }


def _injury_for(career: Career, fixture: dict, player_id: str) -> dict:
    rng = random.Random(f"{career.seed}:{fixture['id']}:injury:{player_id}")
    days = rng.choice(INJURY_DAYS)
    until = (date.fromisoformat(str(fixture["date"])) + timedelta(days=days)).isoformat()
    return {"type": rng.choice(INJURY_TYPES), "until": until}


def _add_suspension(state: dict, reason: str) -> None:
    current = state.get("suspension") or {}
    matches = max(1, int(current.get("matches") or 0))
    state["suspension"] = {"matches": matches, "reason": reason}


def _player_state(career: Career, player_id: str) -> dict:
    return career.player_state.setdefault(str(player_id), default_player_state())


def _bump(stats: dict, key: str, amount: int = 1) -> None:
    stats[key] = int(stats.get(key) or 0) + amount


def apply_match_outcome(
    career: Career,
    fixture: dict,
    setup: dict,
    match: dict,
    competition_id: str | None = None,
) -> None:
    side = "home" if setup.get("home") else "away"
    competition = competition_key(career, competition_id)
    lineup = setup[f"{side}_lineup"]
    starters = [slot["player"] for slot in lineup["slots"]]
    bench = list(lineup["bench"])
    events = [event for event in match.get("events") or [] if event.get("team") == side]

    suspended_before = {
        player_id
        for player_id, state in career.player_state.items()
        if int((state.get("suspension") or {}).get("matches") or 0) > 0
    }

    for player_id in (str(player_id) for player_id in career.player_ids):
        state = career.player_state.get(player_id)
        if state is None or state.get("injury"):
            continue
        if int((state.get("suspension") or {}).get("matches") or 0) > 0:
            continue
        state["available_matches"] = int(state.get("available_matches") or 0) + 1
        state["expected_minutes"] = int(state.get("expected_minutes") or 0) + round(
            90 * role_share(career, player_id)
        )

    minutes = {player["id"]: 90 for player in starters}
    blocks: dict[str, tuple[dict, dict]] = {}
    for player in [*starters, *bench]:
        state = _player_state(career, player["id"])
        blocks[player["id"]] = (state["stats"], competition_stats(state, competition))

    for event in events:
        minute = int(event.get("minute") or 0)
        player = event.get("player") or {}
        player_id = str(player.get("id") or "")
        if not player_id or player_id not in blocks:
            continue
        total, by_competition = blocks[player_id]
        if event["type"] == "sub":
            outgoing = event.get("player_out") or {}
            outgoing_id = str(outgoing.get("id") or "")
            if outgoing_id:
                minutes[outgoing_id] = min(minutes.get(outgoing_id, 90), minute)
            minutes[player_id] = max(0, 90 - minute)
            _bump(total, "apps")
            _bump(by_competition, "apps")
        elif event["type"] in {"goal", "penalty"}:
            _bump(total, "goals")
            _bump(by_competition, "goals")
            assist = event.get("assist") or {}
            assist_id = str(assist.get("id") or "")
            if assist_id in blocks:
                _bump(blocks[assist_id][0], "assists")
                _bump(blocks[assist_id][1], "assists")
        elif event["type"] == "yellow":
            _bump(total, "yellow")
            _bump(by_competition, "yellow")
            if total["yellow"] % YELLOW_SUSPENSION_THRESHOLD == 0:
                _add_suspension(_player_state(career, player_id), "yellow")
        elif event["type"] == "red":
            _bump(total, "red")
            _bump(by_competition, "red")
            minutes[player_id] = min(minutes.get(player_id, 90), minute)
            _add_suspension(_player_state(career, player_id), "red")
        elif event["type"] == "injury":
            state = _player_state(career, player_id)
            state["injury"] = {
                "type": event.get("injury_type") or _injury_for(career, fixture, player_id)["type"],
                "until": event.get("injury_until")
                or _injury_for(career, fixture, player_id)["until"],
            }

    for player in starters:
        total, by_competition = blocks[player["id"]]
        _bump(total, "apps")
        _bump(total, "starts")
        _bump(by_competition, "apps")
        _bump(by_competition, "starts")
    for player_id, played in minutes.items():
        if player_id not in blocks:
            continue
        total, by_competition = blocks[player_id]
        _bump(total, "minutes", max(0, played))
        _bump(by_competition, "minutes", max(0, played))

    score = match.get("score") or {}
    goals_against = score.get("away" if side == "home" else "home")
    keeper_id = next(
        (slot["player"]["id"] for slot in lineup["slots"] if slot.get("position") == "GK"),
        None,
    )
    if goals_against is not None and keeper_id in blocks and int(goals_against) == 0:
        total, by_competition = blocks[keeper_id]
        _bump(total, "clean_sheets")
        _bump(by_competition, "clean_sheets")

    for player in starters:
        state = _player_state(career, player["id"])
        state["fatigue"] = max(0, int(state.get("fatigue") or 0) - FATIGUE_PER_MATCH)
    for event in events:
        if event["type"] != "sub":
            continue
        player_id = str((event.get("player") or {}).get("id") or "")
        if player_id:
            state = _player_state(career, player_id)
            state["fatigue"] = max(0, int(state.get("fatigue") or 0) - FATIGUE_PER_SUB)

    for player_id in suspended_before:
        state = _player_state(career, player_id)
        suspension = state.get("suspension") or {}
        matches = int(suspension.get("matches") or 0) - 1
        state["suspension"] = (
            {**suspension, "matches": matches} if matches > 0 else None
        )


def reset_season_state(career: Career) -> None:
    for state in career.player_state.values():
        state["fatigue"] = 100
        state["injury"] = None
        state["suspension"] = None
        state["stats"] = empty_stats()
        state["stats_by_competition"] = {}
        state["available_matches"] = 0
        state["expected_minutes"] = 0
    career.condition_date = career.season_start
