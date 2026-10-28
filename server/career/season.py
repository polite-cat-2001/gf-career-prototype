from __future__ import annotations

import math
import random
from datetime import date, timedelta
from typing import Callable

from server.career.core import START_DATE, Career


class SeasonError(ValueError):
    pass


SCHEDULE_VERSION = 2
PROMOTION_PLACES = 3
RELEGATION_PLACES = 3


def squad_strength(players: list[dict]) -> float:
    overalls = sorted((float(player.get("overall") or 0) for player in players), reverse=True)[:11]
    if not overalls:
        return 55.0
    return sum(overalls) / len(overalls)


def build_schedule(club_ids: list[str], start_date: str = START_DATE) -> list[dict]:
    teams: list[str | None] = sorted(set(club_ids))
    if len(teams) < 2:
        return []
    if len(teams) % 2:
        teams.append(None)

    start = date.fromisoformat(start_date)
    rounds: list[list[tuple[str, str]]] = []
    rotation = list(teams)
    for round_index in range(len(rotation) - 1):
        pairs: list[tuple[str, str]] = []
        for index in range(len(rotation) // 2):
            home = rotation[index]
            away = rotation[-1 - index]
            if home is None or away is None:
                continue
            if (round_index + index) % 2:
                home, away = away, home
            pairs.append((home, away))
        rounds.append(pairs)
        rotation = [rotation[0], rotation[-1], *rotation[1:-1]]

    fixtures: list[dict] = []
    for half in (0, 1):
        for round_index, pairs in enumerate(rounds):
            round_no = half * len(rounds) + round_index + 1
            match_date = (start + timedelta(days=7 * round_no)).isoformat()
            for match_index, (home, away) in enumerate(pairs):
                if half:
                    home, away = away, home
                fixtures.append(
                    {
                        "id": f"r{round_no:02d}-{match_index:02d}",
                        "round": round_no,
                        "date": match_date,
                        "home": home,
                        "away": away,
                    }
                )
    return fixtures


def ensure_schedule(career: Career, league_clubs: list[dict]) -> None:
    club_ids = [str(club["id"]) for club in league_clubs]
    club_ids.append(career.club_id)
    if career.schedule is None:
        career.schedule = build_schedule(club_ids, career.season_start)
        career.schedule_version = SCHEDULE_VERSION
        return
    if career.schedule_version >= SCHEDULE_VERSION:
        return

    corrected = {fixture["id"]: fixture for fixture in build_schedule(club_ids, career.season_start)}
    for fixture in career.schedule:
        if fixture["id"] in career.results:
            continue
        fresh = corrected.get(fixture["id"])
        if fresh is not None:
            fixture["home"] = fresh["home"]
            fixture["away"] = fresh["away"]
    career.schedule_version = SCHEDULE_VERSION


def next_fixture(career: Career) -> dict | None:
    for fixture in career.schedule or []:
        if fixture["id"] in career.results:
            continue
        if career.club_id in (fixture["home"], fixture["away"]):
            return fixture
    return None


def _unique_ids(club_ids: list[str]) -> list[str]:
    return list(dict.fromkeys(str(club_id) for club_id in club_ids))


def _club_ref(club: dict) -> dict:
    return {
        "id": str(club.get("id") or club.get("club_id") or ""),
        "name": str(club.get("name") or club.get("club_name") or ""),
        "logo": str(club.get("logo") or club.get("club_logo") or ""),
    }


def _row_ref(row: dict) -> dict:
    return {
        "id": str(row["club_id"]),
        "name": str(row["club_name"]),
        "logo": str(row["club_logo"]),
        "position": int(row["position"]),
    }


def _league_ref(league: dict | None) -> dict | None:
    if league is None:
        return None
    return {"id": str(league["id"]), "name": str(league["name"])}


def _ranked_clubs(clubs: list[dict], strength_for: Callable[[str], float]) -> list[dict]:
    return sorted(
        clubs,
        key=lambda club: (-strength_for(str(club["id"])), str(club.get("name") or "")),
    )


def season_transition(
    career: Career,
    league: dict,
    league_clubs: list[dict],
    above_league: dict | None,
    above_clubs: list[dict],
    below_league: dict | None,
    below_clubs: list[dict],
    strength_for: Callable[[str], float],
    *,
    above2_league: dict | None = None,
    above2_clubs: list[dict] | None = None,
    below2_league: dict | None = None,
    below2_clubs: list[dict] | None = None,
) -> dict | None:
    if next_fixture(career) is not None:
        return None

    clubs = {str(club["id"]): club for club in league_clubs}
    table = _standings(career, clubs)
    current_ids = [str(club["id"]) for club in league_clubs]
    promoted = [_row_ref(row) for row in table[:PROMOTION_PLACES]] if above_league else []
    relegated = [_row_ref(row) for row in table[-RELEGATION_PLACES:]] if below_league else []

    above = _ranked_clubs(above_clubs, strength_for)
    below = _ranked_clubs(below_clubs, strength_for)
    above2 = _ranked_clubs(above2_clubs or [], strength_for)
    below2 = _ranked_clubs(below2_clubs or [], strength_for)
    from_above = [_club_ref(club) for club in above[-RELEGATION_PLACES:]] if above_league else []
    from_below = [_club_ref(club) for club in below[:PROMOTION_PLACES]] if below_league else []

    promoted_ids = {row["id"] for row in promoted}
    relegated_ids = {row["id"] for row in relegated}
    from_above_ids = {club["id"] for club in from_above}
    from_below_ids = {club["id"] for club in from_below}

    if career.club_id in promoted_ids:
        movement = "up"
        next_league = above_league
        next_above_league = above2_league
        next_above = [_club_ref(club) for club in above2[-RELEGATION_PLACES:]] if above2_league else []
        next_below_league = league
        next_below = promoted
        next_ids = [
            str(club["id"]) for club in above_clubs if str(club["id"]) not in from_above_ids
        ] + [row["id"] for row in promoted]
    elif career.club_id in relegated_ids:
        movement = "down"
        next_league = below_league
        next_above_league = league
        next_above = relegated
        next_below_league = below2_league
        next_below = [_club_ref(club) for club in below2[:PROMOTION_PLACES]] if below2_league else []
        next_ids = [
            str(club["id"]) for club in below_clubs if str(club["id"]) not in from_below_ids
        ] + [row["id"] for row in relegated]
    else:
        movement = None
        next_league = league
        next_above_league = above_league
        next_above = from_above
        next_below_league = below_league
        next_below = from_below
        next_ids = [
            club_id
            for club_id in current_ids
            if club_id not in promoted_ids and club_id not in relegated_ids
        ]
        next_ids.extend(club["id"] for club in from_above)
        next_ids.extend(club["id"] for club in from_below)

    next_ids = _unique_ids(next_ids)
    if career.club_id not in next_ids:
        next_ids.append(career.club_id)

    next_above_ref = _league_ref(next_above_league)
    next_below_ref = _league_ref(next_below_league)
    review = {
        "league": _league_ref(league),
        "standings": table,
        "promoted": promoted,
        "relegated": relegated,
        "promoted_to": _league_ref(above_league) if promoted else None,
        "relegated_to": _league_ref(below_league) if relegated else None,
        "movement": movement,
        "next": {
            "league": _league_ref(next_league),
            "above": next_above_ref,
            "below": next_below_ref,
            "from_above": [
                {"club": club, "league": next_above_ref}
                for club in next_above
            ],
            "from_below": [
                {"club": club, "league": next_below_ref}
                for club in next_below
            ],
        },
    }
    return {
        "review": review,
        "league_id": str(next_league["id"]),
        "league_club_ids": next_ids,
    }


def _poisson(rng: random.Random, mean: float) -> int:
    limit = math.exp(-mean)
    goals = 0
    product = 1.0
    while goals < 12:
        product *= rng.random()
        if product <= limit:
            return goals
        goals += 1
    return goals


def _expected_goals(strength: float, opponent: float, home: bool) -> float:
    ratio = max(0.45, strength) / max(0.45, opponent)
    return max(0.25, min(4.4, 1.28 * ratio**2.2 + (0.22 if home else 0)))


def _simulate(career: Career, fixture: dict, strengths: dict[str, float]) -> dict:
    home_strength = strengths.get(fixture["home"], 55.0)
    away_strength = strengths.get(fixture["away"], 55.0)
    rng = random.Random(f"{career.seed}:{fixture['id']}")
    home_goals = _poisson(rng, _expected_goals(home_strength, away_strength, True))
    away_goals = _poisson(rng, _expected_goals(away_strength, home_strength, False))
    return {"home": home_goals, "away": away_goals}


def advance_to(career: Career, target: str, league_clubs: list[dict]) -> None:
    ensure_schedule(career, league_clubs)
    fixture = next_fixture(career)
    if fixture is None:
        raise SeasonError("season is complete")
    try:
        target_date = date.fromisoformat(target)
        current = date.fromisoformat(career.date)
    except ValueError as error:
        raise SeasonError("date must be ISO YYYY-MM-DD") from error
    stop_date = date.fromisoformat(fixture["date"])
    if target_date < current:
        raise SeasonError("cannot move time backwards")
    if target_date > stop_date:
        raise SeasonError("cannot pass the next match day")
    career.date = target_date.isoformat()


def _shift_year(value: str, years: int = 1) -> str:
    parsed = date.fromisoformat(value)
    try:
        shifted = parsed.replace(year=parsed.year + years)
    except ValueError:
        shifted = parsed.replace(year=parsed.year + years, day=28)
    return shifted.isoformat()


def next_season(
    career: Career,
    league_clubs: list[dict],
    *,
    league_id: str | None = None,
    next_league_clubs: list[str] | None = None,
    transition: dict | None = None,
) -> None:
    ensure_schedule(career, league_clubs)
    if next_fixture(career) is not None:
        raise SeasonError("season is not complete")

    clubs = {str(club["id"]): club for club in league_clubs}
    clubs.setdefault(career.club_id, {"id": career.club_id, "name": career.club_id, "logo": ""})
    table = _standings(career, clubs)
    champion = table[0] if table else None
    own = next((row for row in table if row["club_id"] == career.club_id), None)
    review = transition or {}
    next_block = review.get("next") or {}
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "season.completed",
            "payload": {
                "season_start": career.season_start,
                "champion": champion["club_name"] if champion else None,
                "position": own["position"] if own else None,
                "points": own["points"] if own else None,
                "movement": review.get("movement"),
                "league": next_block.get("league") or review.get("league"),
            },
        }
    )

    career.season_start = _shift_year(career.season_start)
    career.date = career.season_start
    if next_league_clubs is not None:
        career.league_id = league_id or career.league_id
        career.league_club_ids = _unique_ids(next_league_clubs)
        club_ids = list(career.league_club_ids)
    else:
        club_ids = [str(club["id"]) for club in league_clubs]
        club_ids.append(career.club_id)
        career.league_id = league_id or career.league_id
        career.league_club_ids = _unique_ids(club_ids)
    career.schedule = build_schedule(club_ids, career.season_start)
    career.schedule_version = SCHEDULE_VERSION
    career.results = {}
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "season.started",
            "payload": {
                "season_start": career.season_start,
                "league_id": career.league_id,
            },
        }
    )


def play_next_match(
    career: Career,
    league_clubs: list[dict],
    strength_for: Callable[[str], float],
) -> dict:
    ensure_schedule(career, league_clubs)
    fixture = next_fixture(career)
    if fixture is None:
        raise SeasonError("season is complete")
    if career.date < fixture["date"]:
        raise SeasonError("advance to the match day first")

    round_no = fixture["round"]
    round_fixtures = [
        match
        for match in career.schedule or []
        if match["round"] == round_no and match["id"] not in career.results
    ]
    strengths = {
        club_id: strength_for(club_id)
        for match in round_fixtures
        for club_id in (match["home"], match["away"])
    }
    for match in round_fixtures:
        career.results[match["id"]] = _simulate(career, match, strengths)

    career.date = (date.fromisoformat(fixture["date"]) + timedelta(days=1)).isoformat()
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "match.played",
            "payload": {
                "fixture_id": fixture["id"],
                "round": round_no,
                **career.results[fixture["id"]],
            },
        }
    )
    return fixture


def _match_summary(career: Career, fixture: dict, clubs: dict[str, dict]) -> dict:
    score = career.results.get(fixture["id"])
    if score is None:
        return {}
    home = fixture["home"] == career.club_id
    opponent_id = fixture["away"] if home else fixture["home"]
    opponent = clubs.get(opponent_id, {})
    goals_for = score["home"] if home else score["away"]
    goals_against = score["away"] if home else score["home"]
    outcome = "W" if goals_for > goals_against else "D" if goals_for == goals_against else "L"
    return {
        "fixture_id": fixture["id"],
        "date": fixture["date"],
        "round": fixture["round"],
        "home": home,
        "goals_for": goals_for,
        "goals_against": goals_against,
        "outcome": outcome,
        "opponent": {
            "id": opponent.get("id", opponent_id),
            "name": opponent.get("name", opponent_id),
            "logo": opponent.get("logo", ""),
        },
    }


def _last_result(career: Career, clubs: dict[str, dict]) -> dict | None:
    played = [
        fixture
        for fixture in career.schedule or []
        if fixture["id"] in career.results and career.club_id in (fixture["home"], fixture["away"])
    ]
    if not played:
        return None
    latest = max(played, key=lambda fixture: (fixture["round"], fixture["date"]))
    return _match_summary(career, latest, clubs) or None


def _recent_form(career: Career, clubs: dict[str, dict], limit: int = 5) -> list[dict]:
    played = [
        fixture
        for fixture in career.schedule or []
        if fixture["id"] in career.results and career.club_id in (fixture["home"], fixture["away"])
    ]
    played.sort(key=lambda fixture: (fixture["round"], fixture["date"]))
    return [_match_summary(career, fixture, clubs) for fixture in played[-limit:]]


def _standings(career: Career, clubs: dict[str, dict]) -> list[dict]:
    table = {
        club_id: {
            "club_id": club_id,
            "club_name": club.get("name", club_id),
            "club_logo": club.get("logo", ""),
            "played": 0,
            "won": 0,
            "drawn": 0,
            "lost": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
        }
        for club_id, club in clubs.items()
    }
    for fixture in career.schedule or []:
        score = career.results.get(fixture["id"])
        if score is None:
            continue
        home = table.get(fixture["home"])
        away = table.get(fixture["away"])
        if home is None or away is None:
            continue
        home_goals = int(score["home"])
        away_goals = int(score["away"])
        home["played"] += 1
        away["played"] += 1
        home["goals_for"] += home_goals
        home["goals_against"] += away_goals
        away["goals_for"] += away_goals
        away["goals_against"] += home_goals
        if home_goals > away_goals:
            home["won"] += 1
            away["lost"] += 1
            home["points"] += 3
        elif home_goals < away_goals:
            away["won"] += 1
            home["lost"] += 1
            away["points"] += 3
        else:
            home["drawn"] += 1
            away["drawn"] += 1
            home["points"] += 1
            away["points"] += 1

    for row in table.values():
        row["goal_difference"] = row["goals_for"] - row["goals_against"]

    ordered = sorted(
        table.values(),
        key=lambda row: (
            -row["points"],
            -row["goal_difference"],
            -row["goals_for"],
            row["club_name"],
        ),
    )
    for position, row in enumerate(ordered, start=1):
        row["position"] = position
    return ordered


def season_state(
    career: Career,
    league_clubs: list[dict],
    strength_for: Callable[[str], float],
) -> dict:
    ensure_schedule(career, league_clubs)
    clubs = {str(club["id"]): club for club in league_clubs}
    clubs.setdefault(
        career.club_id,
        {"id": career.club_id, "name": career.club_id, "logo": ""},
    )
    fixture = next_fixture(career)
    next_match = None
    if fixture is not None:
        opponent_id = (
            fixture["away"] if fixture["home"] == career.club_id else fixture["home"]
        )
        opponent = clubs.get(opponent_id, {})
        next_match = {
            "fixture_id": fixture["id"],
            "date": fixture["date"],
            "round": fixture["round"],
            "home": fixture["home"] == career.club_id,
            "opponent": {
                "id": opponent.get("id", opponent_id),
                "name": opponent.get("name", opponent_id),
                "logo": opponent.get("logo", ""),
                "strength": round(strength_for(opponent_id)),
            },
        }

    rounds = [int(fixture["round"]) for fixture in career.schedule or []]
    rounds_total = max(rounds) if rounds else 0
    return {
        "season_start": career.season_start,
        "round": fixture["round"] if fixture else rounds_total,
        "rounds_total": rounds_total,
        "complete": fixture is None and rounds_total > 0,
        "next": next_match,
        "last_result": _last_result(career, clubs),
        "form": _recent_form(career, clubs),
        "standings": _standings(career, clubs),
    }
