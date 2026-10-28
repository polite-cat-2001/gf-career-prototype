from __future__ import annotations

from collections import Counter

from server.career.core import Career, Manager
from server.career.season import build_schedule, season_transition


def test_double_round_robin_covers_every_pair_twice():
    clubs = [str(index) for index in range(6)]
    fixtures = build_schedule(clubs)

    assert len(fixtures) == 30
    assert len({fixture["id"] for fixture in fixtures}) == 30
    assert {fixture["round"] for fixture in fixtures} == set(range(1, 11))

    meetings = Counter()
    for fixture in fixtures:
        meetings[(fixture["home"], fixture["away"])] += 1
    for home in clubs:
        for away in clubs:
            if home == away:
                continue
            assert meetings[(home, away)] == 1
            assert meetings[(away, home)] == 1


def test_every_club_gets_balanced_home_and_away_matches():
    for size in (5, 6, 8):
        clubs = [str(index) for index in range(size)]
        fixtures = build_schedule(clubs)
        for club in clubs:
            home = sum(1 for fixture in fixtures if fixture["home"] == club)
            away = sum(1 for fixture in fixtures if fixture["away"] == club)
            assert home == away == size - 1


def test_odd_league_gets_a_bye_and_keeps_every_club_busy():
    clubs = [str(index) for index in range(5)]
    fixtures = build_schedule(clubs)

    assert len(fixtures) == 20
    for round_no in {fixture["round"] for fixture in fixtures}:
        round_fixtures = [fixture for fixture in fixtures if fixture["round"] == round_no]
        playing = [club for fixture in round_fixtures for club in (fixture["home"], fixture["away"])]
        assert len(playing) == 4
        assert len(set(playing)) == 4


def test_relegated_club_moves_into_the_lower_division():
    ids = [str(index) for index in range(6)]
    schedule = build_schedule(ids)
    results = {}
    for fixture in schedule:
        if fixture["home"] == "0":
            results[fixture["id"]] = {"home": 0, "away": 5}
        elif fixture["away"] == "0":
            results[fixture["id"]] = {"home": 5, "away": 0}
        else:
            results[fixture["id"]] = {"home": 1, "away": 0}

    career = Career(
        id="a" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="0",
        player_ids=[],
        date="2027-05-01",
        season_start="2026-07-01",
        schedule=schedule,
        results=results,
    )
    above = [{"id": str(index), "name": f"Above {index}", "logo": ""} for index in range(10, 16)]
    below = [{"id": str(index), "name": f"Below {index}", "logo": ""} for index in range(20, 26)]
    transition = season_transition(
        career,
        {"id": "L1", "name": "First"},
        [{"id": club_id, "name": f"Club {club_id}", "logo": ""} for club_id in ids],
        {"id": "L0", "name": "Top"},
        above,
        {"id": "L2", "name": "Second"},
        below,
        lambda club_id: 90.0 if club_id.startswith("2") else 60.0,
    )

    assert transition is not None
    review = transition["review"]
    assert review["movement"] == "down"
    assert review["league"]["id"] == "L1"
    assert review["next"]["league"]["id"] == "L2"
    assert any(row["id"] == "0" for row in review["relegated"])
    assert any(row["club"]["id"] == "0" for row in review["next"]["from_above"])
    assert transition["league_id"] == "L2"
    assert "0" in transition["league_club_ids"]
