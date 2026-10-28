from __future__ import annotations

import math
import random
from datetime import date, timedelta
from typing import Callable

from server.career.core import START_DATE, Career


class SeasonError(ValueError):
    pass


SCHEDULE_VERSION = 2


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


def next_season(career: Career, league_clubs: list[dict]) -> None:
    ensure_schedule(career, league_clubs)
    if next_fixture(career) is not None:
        raise SeasonError("season is not complete")

    clubs = {str(club["id"]): club for club in league_clubs}
    clubs.setdefault(career.club_id, {"id": career.club_id, "name": career.club_id, "logo": ""})
    table = _standings(career, clubs)
    champion = table[0] if table else None
    own = next((row for row in table if row["club_id"] == career.club_id), None)
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "season.completed",
            "payload": {
                "season_start": career.season_start,
                "champion": champion["club_name"] if champion else None,
                "position": own["position"] if own else None,
                "points": own["points"] if own else None,
            },
        }
    )

    career.season_start = _shift_year(career.season_start)
    career.date = career.season_start
    club_ids = [str(club["id"]) for club in league_clubs]
    club_ids.append(career.club_id)
    career.schedule = build_schedule(club_ids, career.season_start)
    career.results = {}
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "season.started",
            "payload": {"season_start": career.season_start},
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
