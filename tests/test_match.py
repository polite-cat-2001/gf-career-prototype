from __future__ import annotations

from server.career.core import Career, Manager
from server.career.match import build_lineup, build_match_setup, build_match_simulation

ROLES = ["GK", "CB", "CB", "LB", "RB", "DM", "CM", "CM", "LM", "CF", "RM"]
BENCH_ROLES = ["GK", "CB", "LB", "DM", "CM", "LM", "CF"]


def make_players(prefix: str = "p") -> list[dict]:
    roles = ROLES + BENCH_ROLES
    return [
        {
            "id": f"{prefix}{index}",
            "name": f"Player {prefix}{index}",
            "last_name": f"Player {prefix}{index}",
            "shirt_number": index + 1,
            "role": role,
            "overall": 70 + index,
        }
        for index, role in enumerate(roles)
    ]


def make_setup(seed: int = 7) -> tuple[Career, dict, dict]:
    career = Career(
        id="a" * 32,
        seed=seed,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[],
    )
    clubs = {
        "home": {"id": "home", "name": "Home FC", "logo": ""},
        "away": {"id": "away", "name": "Away FC", "logo": ""},
    }
    fixture = {
        "id": "r01-00",
        "round": 1,
        "date": "2026-07-08",
        "home": "home",
        "away": "away",
    }
    setup = build_match_setup(
        career,
        fixture,
        "League",
        clubs,
        build_lineup(make_players("h")),
        build_lineup(make_players("a")),
    )
    return career, fixture, setup


def test_lineup_has_eleven_starters_and_seven_bench_players():
    lineup = build_lineup(make_players())

    assert lineup["formation"] == "4-3-3"
    assert len(lineup["slots"]) == 11
    assert len(lineup["bench"]) == 7
    starter_ids = {slot["player"]["id"] for slot in lineup["slots"]}
    bench_ids = {player["id"] for player in lineup["bench"]}
    assert len(starter_ids) == 11
    assert not starter_ids & bench_ids


def test_events_match_the_score_and_are_sorted():
    career, fixture, setup = make_setup()
    match = build_match_simulation(career, fixture, setup, {"home": 3, "away": 2})

    assert match["score"] == {"home": 3, "away": 2}
    assert match["outcome"] == "W"
    assert match["goals_for"] == 3
    assert match["goals_against"] == 2

    goals = {"home": 0, "away": 0}
    for event in match["events"]:
        assert 1 <= event["minute"] <= 90
        if event["type"] in {"goal", "penalty"}:
            goals[event["team"]] += 1
    assert goals == {"home": 3, "away": 2}
    minutes = [event["minute"] for event in match["events"]]
    assert minutes == sorted(minutes)
    assert any(event["type"] == "sub" for event in match["events"])


def test_simulation_is_reproducible_for_the_same_seed():
    career, fixture, setup = make_setup(seed=99)
    first = build_match_simulation(career, fixture, setup, {"home": 1, "away": 1})
    second = build_match_simulation(career, fixture, setup, {"home": 1, "away": 1})
    assert first == second


def test_away_result_is_reported_from_the_career_club_perspective():
    career, fixture, setup = make_setup()
    career.club_id = "away"
    setup["home"] = False

    match = build_match_simulation(career, fixture, setup, {"home": 2, "away": 0})

    assert match["outcome"] == "L"
    assert match["goals_for"] == 0
    assert match["goals_against"] == 2
