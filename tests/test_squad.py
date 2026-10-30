from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.career.actions import ActionError, release_player
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
    ensure_player_finances,
    finance_view,
    morale_percent,
    resolve_negotiations,
    rollover_player_values,
    start_negotiation,
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


def squad_players(snapshot: dict) -> list[dict]:
    return [player for group in snapshot["squad"]["groups"] for player in group["players"]]


def find_player(snapshot: dict, player_id: str) -> dict:
    for player in squad_players(snapshot):
        if player["id"] == player_id:
            return player
    raise AssertionError(f"player {player_id} is missing from the snapshot")


def act(client: TestClient, career_id: str, **payload) -> dict:
    response = client.post(f"/api/careers/{career_id}/actions", json=payload)
    assert response.status_code == 200, response.text
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
    raw.pop("player_values", None)
    raw.pop("player_ages", None)
    raw.pop("balance", None)
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
    assert all(player["market_value"] > 0 for player in players)
    assert snapshot["squad"]["finance"]["balance"] > 0


def test_release_clause_stays_inside_the_multiplier_range():
    players = [
        {
            "id": f"p{index}",
            "name": f"P{index}",
            "overall": 70,
            "age": 27,
            "market_value": 1_234_567 + index,
        }
        for index in range(50)
    ]
    career = Career(
        id="c" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[player["id"] for player in players],
    )

    ensure_player_contracts(career, players)

    for player in players:
        contract = career.player_contracts[player["id"]]
        value = player["market_value"]
        assert int(value * 1.2) <= contract["release_clause"] <= int(value * 2.0)


def test_finance_view_sums_values_and_weekly_wages():
    career, _, _ = make_career()
    players = make_players("h")

    ensure_player_finances(career, players)
    view = finance_view(career, players)

    assert view["balance"] > 0
    assert view["total_market_value"] == sum(player["market_value"] for player in players)
    assert view["weekly_wage_bill"] == sum(
        career.player_contracts[player["id"]]["weekly_wage"] for player in players
    )


def test_values_stay_put_until_the_season_rolls_over():
    career, _, _ = make_career()
    players = make_players("h")

    ensure_player_finances(career, players)
    before = {player["id"]: player["market_value"] for player in players}

    ensure_player_finances(career, players)

    assert {player["id"]: player["market_value"] for player in players} == before
    assert career.balance is not None


def test_season_rollover_revalues_from_age_overall_and_minutes():
    player = {
        "id": "veteran",
        "name": "Veteran",
        "overall": 75,
        "age": 34,
        "market_value": 1_000_000,
    }
    career = Career(
        id="d" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[player["id"]],
    )
    ensure_player_contracts(career, [player])
    ensure_player_finances(career, [player])
    career.player_state[player["id"]] = {
        "stats": {"minutes": 1800},
        "expected_minutes": 1800,
    }

    rollover_player_values(career, [player])

    assert career.player_ages[player["id"]] == 35
    assert player["age"] == 35
    assert player["market_value"] == 710_000
    assert career.player_values[player["id"]] == 710_000


def test_api_snapshot_exposes_finance_summary(client: TestClient):
    snapshot = create_career(client)
    finance = snapshot["squad"]["finance"]
    players = [
        player
        for group in snapshot["squad"]["groups"]
        for player in group["players"]
    ]

    assert finance["balance"] > 0
    assert finance["total_market_value"] == sum(
        player["market_value"] for player in players
    )
    assert finance["weekly_wage_bill"] == sum(
        player["contract"]["weekly_wage"] for player in players
    )
    assert finance["total_market_value"] == snapshot["squad"]["summary"]["total_market_value"]
    assert all(player["age"] is not None for player in players)
    assert all(player["market_value"] > 0 for player in players)


def test_transfer_statuses_are_mutually_exclusive_and_saved(client: TestClient):
    created = create_career(client)
    player = squad_players(created)[0]

    updated = act(
        client,
        created["id"],
        type="transfer_status",
        player_id=player["id"],
        status="transfer",
    )
    assert find_player(updated, player["id"])["transfer_status"] == "transfer"

    updated = act(
        client,
        created["id"],
        type="transfer_status",
        player_id=player["id"],
        status="loan",
    )
    assert find_player(updated, player["id"])["transfer_status"] == "loan"

    reloaded = client.get(f"/api/careers/{created['id']}").json()
    assert find_player(reloaded, player["id"])["transfer_status"] == "loan"

    updated = act(
        client,
        created["id"],
        type="transfer_status",
        player_id=player["id"],
        status="none",
    )
    assert find_player(updated, player["id"])["transfer_status"] is None


def test_transfer_status_rejects_unknown_values(client: TestClient):
    created = create_career(client)
    player = squad_players(created)[0]

    response = client.post(
        f"/api/careers/{created['id']}/actions",
        json={
            "type": "transfer_status",
            "player_id": player["id"],
            "status": "sold",
        },
    )

    assert response.status_code == 422


def test_shirt_numbers_are_unique_and_only_free_numbers_can_be_taken(client: TestClient):
    created = create_career(client)
    players = squad_players(created)
    numbers = [player["shirt_number"] for player in players]

    assert all(number is not None and 1 <= number <= 99 for number in numbers)
    assert len(set(numbers)) == len(numbers)

    free = next(number for number in range(1, 100) if number not in numbers)
    target = players[0]
    updated = act(
        client,
        created["id"],
        type="shirt_number",
        player_id=target["id"],
        number=free,
    )
    assert find_player(updated, target["id"])["shirt_number"] == free

    response = client.post(
        f"/api/careers/{created['id']}/actions",
        json={
            "type": "shirt_number",
            "player_id": players[1]["id"],
            "number": free,
        },
    )
    assert response.status_code == 422

    reloaded = client.get(f"/api/careers/{created['id']}").json()
    assert find_player(reloaded, target["id"])["shirt_number"] == free


def test_releasing_a_player_removes_him_from_every_squad_list(client: TestClient):
    created = create_career(client)
    victim = squad_players(created)[-1]

    updated = act(
        client,
        created["id"],
        type="release_player",
        player_id=victim["id"],
    )

    ids = {player["id"] for player in squad_players(updated)}
    lineup = updated["squad"]["lineup"]
    match_ids = {
        slot["player"]["id"] for slot in lineup["slots"]
    } | {player["id"] for player in lineup["bench"]} | {
        player["id"] for player in lineup["reserve"]
    }
    assert victim["id"] not in ids
    assert victim["id"] not in match_ids
    assert len(ids) == len(squad_players(created)) - 1

    reloaded = client.get(f"/api/careers/{created['id']}").json()
    assert victim["id"] not in {player["id"] for player in squad_players(reloaded)}


def test_release_keeps_a_full_matchday_squad():
    career = Career(
        id="e" * 32,
        seed=7,
        manager=Manager(name="Test", nationality_id="1", nationality="Test"),
        club_id="home",
        player_ids=[f"p{index}" for index in range(11)],
    )

    with pytest.raises(ActionError):
        release_player(career, "p0")


def test_contract_renewal_thinks_for_a_few_days_then_counters(client: TestClient):
    created = create_career(client)
    player = squad_players(created)[0]
    lowball = {
        "type": "negotiate",
        "player_id": player["id"],
        "years": 1,
        "weekly_wage": 1_000,
        "squad_role": player["squad_role"],
        "release_clause": 0,
    }

    updated = act(client, created["id"], **lowball)
    state = find_player(updated, player["id"])["negotiation"]
    assert state["status"] == "pending"
    assert state["due"] > updated["date"]
    assert state["counter"] is None
    assert state["acknowledged"] is True

    pending = client.get(f"/api/careers/{created['id']}").json()
    assert find_player(pending, player["id"])["negotiation"]["status"] == "pending"

    updated = act(client, created["id"], type="advance", date=state["due"])
    state = find_player(updated, player["id"])["negotiation"]
    assert state["status"] == "counter"
    assert state["counter_offers"] == 1
    assert state["counter"]["weekly_wage"] > lowball["weekly_wage"]
    assert state["acknowledged"] is False

    updated = act(
        client,
        created["id"],
        type="ack_negotiation",
        player_id=player["id"],
    )
    assert find_player(updated, player["id"])["negotiation"]["acknowledged"] is True


def test_contract_renewal_counter_offers_are_limited_to_two():
    career, _, _ = make_career()
    players = make_players("h")
    ensure_player_finances(career, players)
    player = players[0]
    lowball = {
        "years": 1,
        "weekly_wage": 1_000,
        "squad_role": career.player_contracts[player["id"]]["squad_role"],
        "release_clause": 0,
    }

    state = start_negotiation(career, player, player["id"], lowball)
    assert state["status"] == "pending"

    for expected in (1, 2):
        career.date = state["due"]
        resolve_negotiations(career)
        assert state["status"] == "counter"
        assert state["counter_offers"] == expected
        state = start_negotiation(career, player, player["id"], lowball)
        assert state["status"] == "pending"

    career.date = state["due"]
    resolve_negotiations(career)
    assert state["status"] == "refused"
    assert state["counter"] is None


def test_accepting_counter_signs_the_contract_immediately(client: TestClient):
    created = create_career(client)
    player = squad_players(created)[0]

    updated = act(
        client,
        created["id"],
        type="negotiate",
        player_id=player["id"],
        years=1,
        weekly_wage=1_000,
        squad_role=player["squad_role"],
        release_clause=0,
    )
    state = find_player(updated, player["id"])["negotiation"]
    assert state["status"] == "pending"

    updated = act(client, created["id"], type="advance", date=state["due"])
    counter = find_player(updated, player["id"])["negotiation"]["counter"]

    updated = act(
        client,
        created["id"],
        type="accept_counter",
        player_id=player["id"],
    )
    renewed = find_player(updated, player["id"])
    assert renewed["negotiation"] is None
    assert renewed["contract"]["years"] == counter["years"]
    assert renewed["contract"]["weekly_wage"] == counter["weekly_wage"]
    assert renewed["contract"]["release_clause"] == counter["release_clause"]
    assert renewed["squad_role"] == counter["squad_role"]

    reloaded = client.get(f"/api/careers/{created['id']}").json()
    persisted = find_player(reloaded, player["id"])
    assert persisted["contract"] == renewed["contract"]
    assert persisted["squad_role"] == renewed["squad_role"]


def test_accepting_counter_requires_money(client: TestClient, saves_dir: Path):
    created = create_career(client)
    player = squad_players(created)[0]

    updated = act(
        client,
        created["id"],
        type="negotiate",
        player_id=player["id"],
        years=1,
        weekly_wage=1_000,
        squad_role=player["squad_role"],
        release_clause=0,
    )
    due = find_player(updated, player["id"])["negotiation"]["due"]
    updated = act(client, created["id"], type="advance", date=due)
    state = find_player(updated, player["id"])["negotiation"]
    assert state["status"] == "counter"
    assert state["affordable"] is True

    path = saves_dir / f"{created['id']}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["balance"] = 0
    path.write_text(json.dumps(raw), encoding="utf-8")

    response = client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "accept_counter", "player_id": player["id"]},
    )
    assert response.status_code == 422

    snapshot = client.get(f"/api/careers/{created['id']}").json()
    persisted = find_player(snapshot, player["id"])
    assert persisted["negotiation"]["status"] == "counter"
    assert persisted["negotiation"]["affordable"] is False


def test_contract_cannot_be_signed_before_agreement(client: TestClient):
    created = create_career(client)
    player = squad_players(created)[0]

    response = client.post(
        f"/api/careers/{created['id']}/actions",
        json={"type": "sign_contract", "player_id": player["id"]},
    )

    assert response.status_code == 422

