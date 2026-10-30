from __future__ import annotations

from typing import Callable

from server.career.condition import (
    STAT_KEYS,
    blocked_player_ids,
    effective_overall,
    ensure_player_states,
    player_view,
    recover_condition,
)
from server.career.core import Career
from server.career.season import season_state
from server.career.squad import contract_view, ensure_player_contracts

ROLE_ORDER = {
    "GK": 0,
    "CB": 1,
    "LB": 2,
    "RB": 3,
    "DM": 4,
    "CM": 5,
    "LM": 6,
    "RM": 7,
    "AM": 8,
    "CF": 9,
}

FORMATION = "4-3-3"

LINEUP_SLOTS = [
    {"position": "GK", "role": "GK", "x": 50, "y": 92, "roles": ["GK"]},
    {"position": "LB", "role": "LB", "x": 15, "y": 72, "roles": ["LB", "LM", "CB"]},
    {"position": "CB", "role": "CB", "x": 37, "y": 77, "roles": ["CB"]},
    {"position": "CB", "role": "CB", "x": 63, "y": 77, "roles": ["CB"]},
    {"position": "RB", "role": "RB", "x": 85, "y": 72, "roles": ["RB", "RM", "CB"]},
    {"position": "DM", "role": "DM", "x": 30, "y": 54, "roles": ["DM", "CM"]},
    {"position": "CM", "role": "CM", "x": 50, "y": 48, "roles": ["CM", "DM", "AM"]},
    {"position": "AM", "role": "AM", "x": 70, "y": 54, "roles": ["AM", "CM", "LM", "RM"]},
    {"position": "LW", "role": "LM", "x": 20, "y": 27, "roles": ["LM", "AM", "CF"]},
    {"position": "ST", "role": "CF", "x": 50, "y": 19, "roles": ["CF"]},
    {"position": "RW", "role": "RM", "x": 80, "y": 27, "roles": ["RM", "AM", "CF"]},
]


def _pick_player(players: list[dict], preferred_roles: list[str], used: set[str]) -> dict | None:
    available = [player for player in players if player["id"] not in used]
    for role in preferred_roles:
        candidates = [player for player in available if player.get("role") == role]
        if candidates:
            return max(candidates, key=lambda player: float(player.get("overall") or 0))
    candidates = [player for player in available if player.get("role") != "GK"]
    if not candidates:
        candidates = available
    return max(candidates, key=lambda player: float(player.get("overall") or 0)) if candidates else None


def lineup_for(
    players: list[dict],
    order: list[str] | None = None,
    bench_order: list[str] | None = None,
    blocked_ids: set[str] | None = None,
) -> dict:
    blocked = set(blocked_ids or ())
    by_id = {player["id"]: player for player in players}
    available = [player for player in players if player["id"] not in blocked]
    order_ids = [str(player_id) for player_id in (order or [])]
    starters: list[dict] = []
    used: set[str] = set()
    for index, slot in enumerate(LINEUP_SLOTS):
        player = None
        if index < len(order_ids):
            candidate = by_id.get(order_ids[index])
            if (
                candidate is not None
                and candidate["id"] not in blocked
                and candidate["id"] not in used
            ):
                player = candidate
        if player is None:
            player = _pick_player(available, slot["roles"], used)
        if player is None:
            break
        starters.append(player)
        used.add(player["id"])

    slots = []
    for slot, player in zip(LINEUP_SLOTS, starters):
        slots.append(
            {
                "position": slot["position"],
                "role": slot["role"],
                "x": slot["x"],
                "y": slot["y"],
                "player": player,
            }
        )
    used = {player["id"] for player in starters}
    bench_players = [player for player in players if player["id"] not in used]
    bench: list[dict] = []
    if bench_order:
        benched = {player["id"]: player for player in bench_players}
        for player_id in bench_order:
            player = benched.pop(str(player_id), None)
            if player is not None:
                bench.append(player)
        bench.extend(
            sorted(
                benched.values(),
                key=lambda player: float(player.get("overall") or 0),
                reverse=True,
            )
        )
    else:
        bench = sorted(
            bench_players,
            key=lambda player: float(player.get("overall") or 0),
            reverse=True,
        )
    return {"formation": FORMATION, "slots": slots, "bench": bench}


def lineup_strength(career: Career, players: list[dict]) -> float:
    ensure_player_states(career, [str(player["id"]) for player in players])
    recover_condition(career, career.date)
    blocked = blocked_player_ids(career)
    raw = lineup_for(players, career.lineup, career.bench_order, blocked)
    ratings = [
        effective_overall(slot["player"], career.player_state.get(str(slot["player"]["id"])))
        for slot in raw["slots"]
    ]
    return sum(ratings) / len(ratings) if ratings else 55.0


def _sort_players(players: list[dict]) -> list[dict]:
    return sorted(
        players,
        key=lambda player: (
            ROLE_ORDER.get(player.get("role"), 99),
            -float(player.get("overall") or 0),
            player.get("name") or "",
        ),
    )


def _summary(players: list[dict]) -> dict:
    ages = [player["age"] for player in players if player.get("age") is not None]
    overalls = [float(player["overall"]) for player in players]
    total_value = sum(int(player.get("market_value") or 0) for player in players)
    return {
        "squad_size": len(players),
        "average_overall": round(sum(overalls) / len(overalls), 1) if overalls else 0,
        "average_age": round(sum(ages) / len(ages), 1) if ages else None,
        "total_market_value": total_value,
    }


def _groups(players: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for player in players:
        role = player.get("role") or "—"
        grouped.setdefault(role, []).append(player)
    ordered_roles = [role for role in ROLE_ORDER if role in grouped]
    ordered_roles.extend(role for role in grouped if role not in ROLE_ORDER)
    return [
        {"role": role, "players": [dict(player) for player in grouped[role]]}
        for role in ordered_roles
    ]


def _competition_stats(career: Career, player_id: str, names: dict[str, str]) -> list[dict]:
    state = career.player_state.get(str(player_id)) or {}
    blocks = state.get("stats_by_competition") or {}
    return [
        {
            "id": str(competition_id),
            "name": names.get(str(competition_id), str(competition_id)),
            **{key: int(block.get(key) or 0) for key in STAT_KEYS},
        }
        for competition_id, block in blocks.items()
        if isinstance(block, dict)
    ]


def build_snapshot(
    career: Career,
    club: dict,
    players: list[dict],
    league_clubs: list[dict] | None = None,
    strength_for: Callable[[str], float] | None = None,
) -> dict:
    ensure_player_states(career, [str(player["id"]) for player in players])
    ensure_player_contracts(career, players)
    recover_condition(career, career.date)
    squad = _sort_players(players)
    competition_names: dict[str, str] = {}
    league_id = str(club.get("league_id") or career.league_id or "")
    if league_id:
        competition_names[league_id] = str(club.get("league_name") or league_id)
    for player in squad:
        state = career.player_state[str(player["id"])]
        player.update(player_view(player, state))
        player.update(contract_view(career, player, state))
        player["effective_overall"] = effective_overall(player, state)
        player["competition_stats"] = _competition_stats(
            career, player["id"], competition_names
        )
    blocked = blocked_player_ids(career)
    clubs = league_clubs or []
    strength = strength_for or (lambda _club_id: 55.0)
    raw_lineup = lineup_for(squad, career.lineup, career.bench_order, blocked)
    available_bench = [
        player for player in raw_lineup["bench"] if player["id"] not in blocked
    ]
    matchday_bench = available_bench[:7]
    bench_ids = {player["id"] for player in matchday_bench}
    return {
        "version": career.version,
        "id": career.id,
        "seed": career.seed,
        "date": career.date,
        "created_at": career.created_at,
        "updated_at": career.updated_at,
        "manager": career.manager.to_save(),
        "club": club,
        "squad": {
            "summary": _summary(squad),
            "groups": _groups(squad),
            "lineup": {
                **raw_lineup,
                "bench": matchday_bench,
                "reserve": [
                    player for player in raw_lineup["bench"] if player["id"] not in bench_ids
                ],
            },
        },
        "season": season_state(
            career,
            clubs,
            strength,
            competition_name=str(club.get("league_name") or ""),
        ),
    }
