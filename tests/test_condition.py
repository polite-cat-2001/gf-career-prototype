from __future__ import annotations

from server.career.actions import swap_players
from server.career.condition import (
    apply_match_outcome,
    ensure_player_states,
    recover_condition,
)
from server.career.core import Career, Manager
from server.career.match import _replacement_for, build_lineup, build_match_setup
from server.career.season import build_schedule, matchday_state
from server.career.snapshot import build_snapshot, lineup_for, lineup_strength

ROLES = ["GK", "CB", "CB", "LB", "RB", "DM", "CM", "CM", "LM", "CF", "RM"]
BENCH_ROLES = ["GK", "CB", "LB", "DM", "CM", "LM", "CF"]


def make_players(prefix: str = "p") -> list[dict]:
    return [
        {
            "id": f"{prefix}{index}",
            "name": f"Player {prefix}{index}",
            "last_name": f"Player {prefix}{index}",
            "shirt_number": index + 1,
            "role": role,
            "overall": 70 + index,
        }
        for index, role in enumerate(ROLES + BENCH_ROLES)
    ]


def make_career() -> tuple[Career, dict, dict]:
    career = Career(
        id="a" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[player["id"] for player in make_players("h")],
        date="2026-07-08",
    )
    fixture = {
        "id": "r01-00",
        "round": 1,
        "date": "2026-07-08",
        "home": "home",
        "away": "away",
    }
    clubs = {
        "home": {"id": "home", "name": "Home", "logo": ""},
        "away": {"id": "away", "name": "Away", "logo": ""},
    }
    setup = build_match_setup(
        career,
        fixture,
        "League",
        clubs,
        build_lineup(make_players("h")),
        build_lineup(make_players("a")),
    )
    ensure_player_states(career, career.player_ids)
    return career, fixture, setup


def own_event(setup: dict, event_type: str, player_id: str, **extra) -> dict:
    side = "home" if setup["home"] else "away"
    player = next(
        slot["player"]
        for slot in setup[f"{side}_lineup"]["slots"]
        if slot["player"]["id"] == player_id
    )
    return {"minute": 10, "type": event_type, "team": side, "player": player, **extra}


def test_match_updates_minutes_goals_assists_and_fatigue():
    career, fixture, setup = make_career()
    scorer = setup["home_lineup"]["slots"][9]["player"]
    assister = setup["home_lineup"]["slots"][7]["player"]
    match = {
        "events": [
            own_event(setup, "goal", scorer["id"], assist=assister),
            own_event(setup, "yellow", setup["home_lineup"]["slots"][5]["player"]["id"]),
        ]
    }

    apply_match_outcome(career, fixture, setup, match)

    scorer_state = career.player_state[scorer["id"]]
    assister_state = career.player_state[assister["id"]]
    starter_state = career.player_state[setup["home_lineup"]["slots"][0]["player"]["id"]]
    assert scorer_state["stats"]["goals"] == 1
    assert scorer_state["stats"]["apps"] == 1
    assert scorer_state["stats"]["starts"] == 1
    assert scorer_state["stats"]["minutes"] == 90
    assert assister_state["stats"]["assists"] == 1
    assert starter_state["fatigue"] == 65


def test_consecutive_starts_leave_residual_fatigue():
    career, fixture, setup = make_career()
    player_id = setup["home_lineup"]["slots"][0]["player"]["id"]

    apply_match_outcome(career, fixture, setup, {"events": []})
    after_first = career.player_state[player_id]["fatigue"]
    recover_condition(career, "2026-07-15")
    before_second = career.player_state[player_id]["fatigue"]
    apply_match_outcome(career, fixture, setup, {"events": []})
    after_second = career.player_state[player_id]["fatigue"]

    assert after_first == 65
    assert before_second == 93
    assert after_second == 58
    assert after_second < after_first


def test_red_card_creates_suspension_and_is_served_by_next_match():
    career, fixture, setup = make_career()
    player = setup["home_lineup"]["slots"][3]["player"]
    apply_match_outcome(
        career,
        fixture,
        setup,
        {"events": [own_event(setup, "red", player["id"])]},
    )

    assert career.player_state[player["id"]]["suspension"]["matches"] == 1
    assert career.player_state[player["id"]]["stats"]["red"] == 1

    apply_match_outcome(career, fixture, setup, {"events": []})
    assert career.player_state[player["id"]]["suspension"] is None


def test_fifth_yellow_creates_one_match_suspension():
    career, fixture, setup = make_career()
    player = setup["home_lineup"]["slots"][4]["player"]
    career.player_state[player["id"]]["stats"]["yellow"] = 4

    apply_match_outcome(
        career,
        fixture,
        setup,
        {"events": [own_event(setup, "yellow", player["id"])]},
    )

    assert career.player_state[player["id"]]["suspension"] == {
        "matches": 1,
        "reason": "yellow",
    }


def test_blocked_starter_is_replaced_and_sits_out_the_matchday_squad():
    players = make_players()
    blocked = players[0]["id"]

    plan = lineup_for(players, blocked_ids={blocked})
    matchday = build_lineup(players, blocked_ids={blocked})

    plan_starters = {slot["player"]["id"] for slot in plan["slots"]}
    matchday_starters = {slot["player"]["id"] for slot in matchday["slots"]}
    matchday_bench = {player["id"] for player in matchday["bench"]}
    assert len(plan_starters) == 11
    assert len(matchday_starters) == 11
    assert blocked not in plan_starters
    assert blocked in {player["id"] for player in plan["bench"]}
    assert blocked not in matchday_starters
    assert blocked not in matchday_bench


def test_blocked_goalkeeper_is_replaced_by_the_backup_goalkeeper():
    players = make_players()
    blocked = players[0]["id"]

    lineup = lineup_for(players, blocked_ids={blocked})

    goalkeeper = lineup["slots"][0]["player"]
    assert goalkeeper["role"] == "GK"
    assert goalkeeper["id"] != blocked


def test_injury_replacement_prefers_the_same_position():
    bench = [
        {"id": "gk", "role": "GK", "overall": 60},
        {"id": "cb", "role": "CB", "overall": 80},
        {"id": "cf", "role": "CF", "overall": 90},
    ]

    assert _replacement_for(bench, "GK", set())["id"] == "gk"
    assert _replacement_for(bench, "CB", set())["id"] == "cb"
    assert _replacement_for(bench, "CF", set())["id"] == "cf"


def test_fatigue_reduces_selected_lineup_strength():
    career, _, _ = make_career()
    players = make_players("h")
    fresh = lineup_strength(career, players)
    for state in career.player_state.values():
        state["fatigue"] = 0
    tired = lineup_strength(career, players)

    assert tired < fresh


def test_injury_and_daily_recovery_are_persistent():
    career, fixture, setup = make_career()
    player = setup["home_lineup"]["slots"][6]["player"]
    apply_match_outcome(
        career,
        fixture,
        setup,
        {
            "events": [
                own_event(
                    setup,
                    "injury",
                    player["id"],
                    injury_type="Мышца",
                    injury_until="2026-07-22",
                )
            ]
        },
    )

    assert career.player_state[player["id"]]["injury"]["until"] == "2026-07-22"
    recover_condition(career, "2026-07-21")
    assert career.player_state[player["id"]]["injury"] is not None
    recover_condition(career, "2026-07-22")
    assert career.player_state[player["id"]]["injury"] is None


def test_snapshot_separates_matchday_bench_from_reserve():
    players = make_players("h")
    players.extend(
        [
            {"id": "reserve-cb", "name": "Reserve CB", "role": "CB", "overall": 60},
            {"id": "reserve-cf", "name": "Reserve CF", "role": "CF", "overall": 61},
        ]
    )
    career = Career(
        id="c" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[player["id"] for player in players],
    )
    club = {"id": "home", "name": "Home", "logo": "", "league_name": "League"}
    opponent = {"id": "away", "name": "Away", "logo": "", "league_name": "League"}

    snapshot = build_snapshot(
        career,
        club,
        players,
        league_clubs=[club, opponent],
        strength_for=lambda _club_id: 70.0,
    )

    assert len(snapshot["squad"]["lineup"]["bench"]) == 7
    assert len(snapshot["squad"]["lineup"]["reserve"]) == 2
    assert {
        player["id"] for player in snapshot["squad"]["lineup"]["reserve"]
    } == {"reserve-cb", "reserve-cf"}


def test_reserve_can_be_moved_like_a_bench_player():
    players = make_players("h")
    players.extend(
        [
            {"id": "reserve-cb", "name": "Reserve CB", "role": "CB", "overall": 60},
            {"id": "reserve-cf", "name": "Reserve CF", "role": "CF", "overall": 61},
        ]
    )
    career = Career(
        id="d" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[player["id"] for player in players],
    )
    starter = lineup_for(players)["slots"][10]["player"]["id"]

    swap_players(career, players, starter, "reserve-cf")

    assert "reserve-cf" in career.lineup


def test_matchday_reports_results_and_position_movements():
    clubs = [{"id": str(index), "name": f"Club {index}", "logo": ""} for index in range(4)]
    schedule = build_schedule([club["id"] for club in clubs])
    career = Career(
        id="b" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="0",
        player_ids=[],
        schedule=schedule,
        date="2026-07-30",
    )
    first_round = [fixture for fixture in schedule if fixture["round"] == 1]
    for fixture in first_round:
        career.results[fixture["id"]] = {"home": 2, "away": 0}

    first = matchday_state(career, {club["id"]: club for club in clubs}, "League")
    assert first is not None
    assert all(row["delta"] == 0 for row in first["standings"])

    second_round = [fixture for fixture in schedule if fixture["round"] == 2]
    for fixture in second_round:
        if (fixture["home"], fixture["away"]) == ("2", "0"):
            career.results[fixture["id"]] = {"home": 3, "away": 0}
        else:
            career.results[fixture["id"]] = {"home": 0, "away": 1}

    second = matchday_state(career, {club["id"]: club for club in clubs}, "League")
    assert second is not None
    assert second["competition"] == "League"
    assert len(second["results"]) == 2
    assert any(row["delta"] != 0 for row in second["standings"])
    assert all("previous_position" in row for row in second["standings"])
