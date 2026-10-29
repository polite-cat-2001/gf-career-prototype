from __future__ import annotations

import random
import re
from datetime import date, timedelta

from server.career.condition import INJURY_DAYS, INJURY_TYPES
from server.career.core import Career
from server.career.snapshot import lineup_for

MATCHDAY_BENCH = 7
EVENT_ORDER = {
    "goal": 0,
    "penalty": 0,
    "yellow": 1,
    "red": 2,
    "injury": 3,
    "sub": 4,
}
CLUB_PREFIXES = {"FC", "AFC", "CF", "AC", "AS", "SV", "SC"}


def club_abbr(name: str) -> str:
    words = re.findall(r"[A-Za-z0-9]+", name or "")
    if not words:
        return "???"
    word = words[0]
    if word.upper() in CLUB_PREFIXES and len(words) > 1:
        word = words[1]
    return word[:3].upper()


def player_ref(player: dict) -> dict:
    return {
        "id": str(player["id"]),
        "name": str(player.get("name") or ""),
        "last_name": player.get("last_name"),
        "shirt_number": player.get("shirt_number"),
        "role": player.get("role"),
    }


def build_lineup(
    players: list[dict],
    order: list[str] | None = None,
    bench_order: list[str] | None = None,
    blocked_ids: set[str] | None = None,
) -> dict:
    raw = lineup_for(players, order, bench_order, blocked_ids)
    return {
        "formation": raw["formation"],
        "slots": [
            {
                "position": slot["position"],
                "role": slot["role"],
                "x": slot["x"],
                "y": slot["y"],
                "player": player_ref(slot["player"]),
            }
            for slot in raw["slots"]
        ],
        "bench": [
            player_ref(player)
            for player in raw["bench"]
            if player["id"] not in set(blocked_ids or ())
        ][:MATCHDAY_BENCH],
    }


def build_match_setup(
    career: Career,
    fixture: dict,
    competition: str,
    clubs: dict[str, dict],
    home_lineup: dict,
    away_lineup: dict,
) -> dict:
    home = clubs[fixture["home"]]
    away = clubs[fixture["away"]]
    return {
        "fixture_id": str(fixture["id"]),
        "round": int(fixture["round"]),
        "date": str(fixture["date"]),
        "home": fixture["home"] == career.club_id,
        "competition": competition,
        "home_team": {
            "id": str(home["id"]),
            "name": str(home["name"]),
            "logo": str(home.get("logo") or ""),
            "abbr": club_abbr(str(home["name"])),
        },
        "away_team": {
            "id": str(away["id"]),
            "name": str(away["name"]),
            "logo": str(away.get("logo") or ""),
            "abbr": club_abbr(str(away["name"])),
        },
        "home_lineup": home_lineup,
        "away_lineup": away_lineup,
    }


def _scorer_weight(player: dict) -> float:
    role = player.get("role")
    if role == "GK":
        return 0.0
    if role == "CF":
        return 6.0
    if role in {"AM", "LM", "RM"}:
        return 3.0
    if role in {"CM", "DM"}:
        return 1.4
    return 0.6


def _assist_weight(player: dict) -> float:
    role = player.get("role")
    if role == "GK":
        return 0.0
    if role in {"AM", "LM", "RM"}:
        return 5.0
    if role in {"CM", "CF"}:
        return 3.0
    if role == "DM":
        return 1.2
    return 0.5


def _pick_weighted(rng: random.Random, players: list[dict], weight_for) -> dict | None:
    weighted = [(player, weight_for(player)) for player in players]
    weighted = [(player, weight) for player, weight in weighted if weight > 0]
    if not weighted:
        return players[0] if players else None
    total = sum(weight for _, weight in weighted)
    point = rng.uniform(0, total)
    upto = 0.0
    for player, weight in weighted:
        upto += weight
        if point <= upto:
            return player
    return weighted[-1][0]


ROLE_FAMILY = {
    "GK": 0,
    "CB": 1,
    "LB": 1,
    "RB": 1,
    "DM": 2,
    "CM": 2,
    "AM": 2,
    "LM": 3,
    "RM": 3,
    "CF": 4,
}


def _replacement_for(bench: list[dict], role: str | None, used_ids: set[str]) -> dict | None:
    candidates = [player for player in bench if player["id"] not in used_ids]
    if not candidates:
        return None

    def score(player: dict) -> tuple[int, float]:
        candidate_role = player.get("role")
        if candidate_role == role:
            return (0, -float(player.get("overall") or 0))
        if role == "GK" or candidate_role == "GK":
            return (9, -float(player.get("overall") or 0))
        distance = abs(
            ROLE_FAMILY.get(str(candidate_role), 2) - ROLE_FAMILY.get(str(role), 2)
        )
        return (1 + distance, -float(player.get("overall") or 0))

    return min(candidates, key=score)


def _substitutions(
    rng: random.Random,
    team: str,
    lineup: dict,
) -> list[dict]:
    starters = [slot["player"] for slot in lineup["slots"]]
    bench = [player for player in lineup["bench"] if player.get("role") != "GK"]
    if len(bench) < 2:
        return []
    outfield = [player for player in starters if player.get("role") != "GK"]
    count = rng.randint(2, min(4, len(outfield), len(bench)))
    minutes = sorted(rng.sample(range(55, 86), count))
    outgoing = rng.sample(outfield, count)
    incoming = rng.sample(bench, count)
    return [
        {
            "minute": minute,
            "type": "sub",
            "team": team,
            "player": incoming[index],
            "player_out": outgoing[index],
        }
        for index, minute in enumerate(minutes)
    ]


def _active_players(
    lineup: dict,
    subs: list[dict],
    minute: int,
) -> list[dict]:
    players: list[dict] = []
    out_at = {
        event["player_out"]["id"]: event["minute"]
        for event in subs
        if event.get("player_out")
    }
    in_at = {
        event["player"]["id"]: event["minute"]
        for event in subs
        if event.get("player")
    }
    for slot in lineup["slots"]:
        player = slot["player"]
        if player["id"] in out_at and minute >= out_at[player["id"]]:
            continue
        players.append(player)
    for player in lineup["bench"]:
        if player["id"] in in_at and minute >= in_at[player["id"]]:
            players.append(player)
    return players


def build_match_simulation(
    career: Career,
    fixture: dict,
    setup: dict,
    score: dict,
) -> dict:
    rng = random.Random(f"{career.seed}:{fixture['id']}:timeline")
    final_home = int(score["home"])
    final_away = int(score["away"])
    events: list[dict] = []

    subs = {
        "home": _substitutions(rng, "home", setup["home_lineup"]),
        "away": _substitutions(rng, "away", setup["away_lineup"]),
    }

    injuries = rng.choices([0, 1, 2], weights=[64, 29, 7], k=1)[0]
    injured_ids: set[str] = set()
    injury_events = []
    for _ in range(injuries):
        side = rng.choice(["home", "away"])
        minute = rng.randint(12, 86)
        active = _active_players(setup[f"{side}_lineup"], subs[side], minute)
        candidates = [player for player in active if player["id"] not in injured_ids]
        if not candidates:
            continue
        player = rng.choice(candidates)
        injured_ids.add(player["id"])
        days = rng.choice(INJURY_DAYS)
        until = (date.fromisoformat(str(fixture["date"])) + timedelta(days=days)).isoformat()
        event = {
            "minute": minute,
            "type": "injury",
            "team": side,
            "player": player,
            "injury_type": rng.choice(INJURY_TYPES),
            "injury_until": until,
        }
        injury_events.append(event)

    accepted_injuries = []
    for injury in injury_events:
        side = injury["team"]
        player = injury["player"]
        minute = int(injury["minute"])
        side_subs = subs[side]
        active_ids = {
            active["id"]
            for active in _active_players(setup[f"{side}_lineup"], side_subs, minute)
        }
        if player["id"] not in active_ids:
            continue
        accepted_injuries.append(injury)
        if len(side_subs) >= 5:
            continue
        side_subs[:] = [
            event
            for event in side_subs
            if not (
                (event.get("player_out") or {}).get("id") == player["id"]
                and int(event["minute"]) > minute
            )
        ]
        incoming = {
            (event.get("player") or {}).get("id") for event in side_subs
        }
        replacement = _replacement_for(
            setup[f"{side}_lineup"]["bench"],
            player.get("role"),
            {str(player_id) for player_id in incoming if player_id},
        )
        if replacement is None:
            continue
        side_subs.append(
            {
                "minute": minute,
                "type": "sub",
                "team": side,
                "player": replacement,
                "player_out": player,
            }
        )

    for side in ("home", "away"):
        subs[side].sort(key=lambda event: int(event["minute"]))
        events.extend(subs[side])
    events.extend(accepted_injuries)

    goal_sides = ["home"] * final_home + ["away"] * final_away
    rng.shuffle(goal_sides)
    for side in goal_sides:
        minute = rng.randint(1, 90)
        active = _active_players(setup[f"{side}_lineup"], subs[side], minute)
        scorer = _pick_weighted(rng, active, _scorer_weight)
        if scorer is not None:
            event_type = "penalty" if rng.random() < 0.14 else "goal"
            assist = None
            if event_type == "goal":
                candidates = [player for player in active if player["id"] != scorer["id"]]
                assist = _pick_weighted(rng, candidates, _assist_weight)
            events.append(
                {
                    "minute": minute,
                    "type": event_type,
                    "team": side,
                    "player": scorer,
                    "assist": assist,
                }
            )

    for side in ("home", "away"):
        active = _active_players(setup[f"{side}_lineup"], subs[side], 0)
        carded: set[str] = set()
        yellows = rng.choices([0, 1, 2, 3, 4], weights=[40, 30, 17, 9, 4], k=1)[0]
        for _ in range(yellows):
            minute = rng.randint(18, 89)
            candidates = [
                player
                for player in _active_players(setup[f"{side}_lineup"], subs[side], minute)
                if player["id"] not in carded
            ]
            if not candidates:
                continue
            player = rng.choice(candidates)
            carded.add(player["id"])
            events.append(
                {"minute": minute, "type": "yellow", "team": side, "player": player}
            )
        if active and rng.random() < 0.08:
            minute = rng.randint(25, 89)
            candidates = [
                player
                for player in _active_players(setup[f"{side}_lineup"], subs[side], minute)
                if player["id"] not in carded
            ]
            if candidates:
                player = rng.choice(candidates)
                events.append(
                    {"minute": minute, "type": "red", "team": side, "player": player}
                )

    events.sort(
        key=lambda event: (
            int(event["minute"]),
            EVENT_ORDER.get(str(event["type"]), 9),
            str(event.get("player", {}).get("id", "")),
        )
    )
    for index, event in enumerate(events, start=1):
        event["id"] = f"{fixture['id']}-e{index:02d}"

    home = bool(setup["home"])
    goals_for = final_home if home else final_away
    goals_against = final_away if home else final_home
    outcome = "W" if goals_for > goals_against else "D" if goals_for == goals_against else "L"
    return {
        **setup,
        "events": events,
        "score": {"home": final_home, "away": final_away},
        "outcome": outcome,
        "goals_for": goals_for,
        "goals_against": goals_against,
    }
