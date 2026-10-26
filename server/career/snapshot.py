from __future__ import annotations

from server.career.core import Career

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


def _auto_starters(players: list[dict]) -> list[dict]:
    used: set[str] = set()
    starters = []
    for slot in LINEUP_SLOTS:
        player = _pick_player(players, slot["roles"], used)
        if player is None:
            break
        used.add(player["id"])
        starters.append(player)
    return starters


def lineup_for(
    players: list[dict],
    order: list[str] | None = None,
    bench_order: list[str] | None = None,
) -> dict:
    by_id = {player["id"]: player for player in players}
    starters: list[dict] = []
    if order:
        for player_id in order:
            player = by_id.get(str(player_id))
            if player is not None and player not in starters:
                starters.append(player)
    if len(starters) != len(LINEUP_SLOTS):
        starters = _auto_starters(players)

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
        {
            "role": role,
            "players": [
                {key: value for key, value in player.items() if key != "stats"}
                for player in grouped[role]
            ],
        }
        for role in ordered_roles
    ]


def build_snapshot(career: Career, club: dict, players: list[dict]) -> dict:
    squad = _sort_players(players)
    for player in squad:
        player.setdefault("fatigue", 100)
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
            "lineup": lineup_for(squad, career.lineup, career.bench_order),
        },
    }
