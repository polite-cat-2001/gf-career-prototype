from __future__ import annotations

from collections import Counter

from server.career.season import build_schedule


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
