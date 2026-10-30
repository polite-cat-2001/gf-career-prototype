from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from server.career.condition import (
    apply_match_outcome,
    ensure_player_states,
    reset_season_state,
)
from server.career.core import Career, Manager
from server.career.match import build_lineup, build_match_setup
from server.career.squad import (
    ROLE_BY_ID,
    SQUAD_ROLES,
    ensure_player_contracts,
    morale_percent,
)

ARSENAL = "11"
ENGLAND = "189"

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
            "overall": 70 - index,
            "age": 27,
            "market_value": 1_000_000,
        }
        for index, role in enumerate(ROLES + BENCH_ROLES)
    ]


def make_career() -> tuple[Career, dict, dict]:
    players = make_players("h")
    career = Career(
        id="a" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[player["id"] for player in players],
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
        build_lineup(players),
        build_lineup(make_players("a")),
    )
    ensure_player_states(career, career.player_ids)
    ensure_player_contracts(career, players)
    return career, fixture, setup


def create_career(client: TestClient) -> dict:
    response = client.post(
        "/api/careers",
        json={
            "club_id": ARSENAL,
            "manager_name": "Ada Lovelace",
            "manager_nationality_id": ENGLAND,
            "seed": 4242,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_squad_roles_cover_the_ovr_hierarchy():
    players = [
        {"id": f"p{index}", "name": f"P{index}", "overall": 100 - index}
        for index in range(25)
    ]
    career = Career(
        id="b" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[player["id"] for player in players],
    )

    ensure_player_contracts(career, players)
    roles = [career.player_contracts[player["id"]]["squad_role"] for player in players]

    assert roles[0] == "key"
    assert roles[-1] == "prospect"
    assert set(roles) == {role["id"] for role in SQUAD_ROLES}
    assert roles.index("key") < roles.index("first") < roles.index("rotation")
    assert roles.index("rotation") < roles.index("squad") < roles.index("prospect")


def test_expected_minutes_are_the_five_role_shares():
    assert [round(role["expected"] * 100) for role in SQUAD_ROLES] == [85, 65, 45, 25, 10]
    assert all(role["label"] and role["short"] for role in SQUAD_ROLES)
    assert {role["id"] for role in SQUAD_ROLES} == {
        "key",
        "first",
        "rotation",
        "squad",
        "prospect",
    }
    assert set(ROLE_BY_ID) == {role["id"] for role in SQUAD_ROLES}


def test_morale_is_actual_minutes_over_expected():
    assert morale_percent(45, 90) == 50
    assert morale_percent(0, 90) == 0
    assert morale_percent(90, 90) == 100
    assert morale_percent(135, 90) == 100
    assert morale_percent(0, 0) == 100


def test_injured_and_suspended_players_stay_out_of_the_expected_minutes():
    career, fixture, setup = make_career()
    injured = career.player_ids[3]
    suspended = career.player_ids[4]
    healthy = career.player_ids[-1]
    career.player_state[injured]["injury"] = {"type": "Мышца", "until": "2026-07-22"}
    career.player_state[suspended]["suspension"] = {"matches": 1, "reason": "red"}

    apply_match_outcome(career, fixture, setup, {"events": []})

    assert career.player_state[injured]["expected_minutes"] == 0
    assert career.player_state[suspended]["expected_minutes"] == 0
    assert career.player_state[healthy]["expected_minutes"] > 0
    expected = career.player_state[healthy]["expected_minutes"]
    role = career.player_contracts[healthy]["squad_role"]
    assert expected == round(90 * ROLE_BY_ID[role]["expected"])


def test_reset_season_clears_morale_denominator():
    career, fixture, setup = make_career()

    apply_match_outcome(career, fixture, setup, {"events": []})
    assert any(state["expected_minutes"] > 0 for state in career.player_state.values())

    reset_season_state(career)

    assert all(state["expected_minutes"] == 0 for state in career.player_state.values())
    assert all(state["available_matches"] == 0 for state in career.player_state.values())


def test_api_snapshot_exposes_roles_morale_and_contracts(client: TestClient):
    snapshot = create_career(client)
    players = [
        player
        for group in snapshot["squad"]["groups"]
        for player in group["players"]
    ]

    assert players
    for player in players:
        assert player["squad_role"] in ROLE_BY_ID
        assert player["squad_role_label"] == ROLE_BY_ID[player["squad_role"]]["label"]
        assert 0.10 <= player["expected_share"] <= 0.85
        assert player["morale"] == 100
        contract = player["contract"]
        assert 1 <= contract["years"] <= 5
        assert contract["weekly_wage"] > 0
        assert contract["release_clause"] > 0

    ranked = sorted(players, key=lambda player: -player["overall"])
    assert ranked[0]["squad_role"] == "key"
    assert ranked[-1]["squad_role"] == "prospect"


def test_match_outcome_tracks_stats_by_competition_and_clean_sheets():
    career, fixture, setup = make_career()
    career.league_id = "eng-1"
    ensure_player_states(career, career.player_ids)
    scorer = setup["home_lineup"]["slots"][9]["player"]
    assister = setup["home_lineup"]["slots"][7]["player"]
    keeper = setup["home_lineup"]["slots"][0]["player"]
    match = {
        "events": [
            {
                "minute": 12,
                "type": "goal",
                "team": "home",
                "player": scorer,
                "assist": assister,
            }
        ],
        "score": {"home": 1, "away": 0},
    }

    apply_match_outcome(career, fixture, setup, match, competition_id="eng-1")

    scorer_state = career.player_state[scorer["id"]]
    keeper_state = career.player_state[keeper["id"]]
    assister_block = career.player_state[assister["id"]]["stats_by_competition"]["eng-1"]
    assert scorer_state["stats"]["goals"] == 1
    assert scorer_state["stats_by_competition"]["eng-1"]["goals"] == 1
    assert scorer_state["stats_by_competition"]["eng-1"]["apps"] == 1
    assert assister_block["assists"] == 1
    assert keeper_state["stats"]["clean_sheets"] == 1
    assert keeper_state["stats_by_competition"]["eng-1"]["clean_sheets"] == 1


def test_goalkeeper_gets_no_clean_sheet_when_conceding():
    career, fixture, setup = make_career()
    career.league_id = "eng-1"
    ensure_player_states(career, career.player_ids)
    keeper = setup["home_lineup"]["slots"][0]["player"]

    apply_match_outcome(
        career,
        fixture,
        setup,
        {"events": [], "score": {"home": 2, "away": 1}},
        competition_id="eng-1",
    )

    assert career.player_state[keeper["id"]]["stats"]["clean_sheets"] == 0
    assert (
        career.player_state[keeper["id"]]["stats_by_competition"]["eng-1"]["clean_sheets"]
        == 0
    )


def test_old_state_derives_competition_stats_from_the_aggregate():
    career, _, _ = make_career()
    career.league_id = "eng-1"
    ensure_player_states(career, career.player_ids)
    player_id = career.player_ids[0]
    state = career.player_state[player_id]
    state["stats"]["apps"] = 4
    state["stats"]["minutes"] = 360
    state.pop("stats_by_competition", None)

    ensure_player_states(career, [player_id])

    block = career.player_state[player_id]["stats_by_competition"]["eng-1"]
    assert block["apps"] == 4
    assert block["minutes"] == 360
    assert block["goals"] == 0


def test_reset_season_clears_per_competition_stats():
    career, fixture, setup = make_career()
    career.league_id = "eng-1"
    ensure_player_states(career, career.player_ids)
    apply_match_outcome(career, fixture, setup, {"events": []}, competition_id="eng-1")

    reset_season_state(career)

    assert all(
        state["stats_by_competition"] == {} for state in career.player_state.values()
    )


def test_api_snapshot_exposes_competition_stats(client: TestClient):
    snapshot = create_career(client)
    league_id = snapshot["club"]["league_id"]
    players = [
        player
        for group in snapshot["squad"]["groups"]
        for player in group["players"]
    ]

    assert players
    for player in players:
        assert len(player["stats"]) == 22
        assert len(player["competition_stats"]) == 1
        block = player["competition_stats"][0]
        assert block["id"] == league_id
        assert block["name"] == "Premier League"
        assert block["apps"] == 0
        assert block["clean_sheets"] == 0


def test_old_save_without_contracts_gets_defaults(client: TestClient, saves_dir: Path):
    created = create_career(client)
    path = saves_dir / f"{created['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw.pop("player_contracts", None)
    raw.pop("player_state", None)
    path.write_text(json.dumps(raw), encoding="utf-8")

    loaded = client.get(f"/api/careers/{created['id']}")
    assert loaded.status_code == 200, loaded.text
    snapshot = loaded.json()

    players = [
        player
        for group in snapshot["squad"]["groups"]
        for player in group["players"]
    ]
    assert all(player["squad_role"] in ROLE_BY_ID for player in players)
    assert all(player["contract"]["years"] >= 1 for player in players)
    assert all(player["morale"] == 100 for player in players)
