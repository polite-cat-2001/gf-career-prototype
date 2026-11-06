from __future__ import annotations

from server.career.formations import (
    FORMATION_ORDER,
    FORMATIONS,
    arrange_lineup,
    formation_catalog,
    formation_slots,
)


def player(player_id: str, role: str) -> dict:
    return {
        "id": player_id,
        "role": role,
        "overall": 80,
        "name": player_id,
        "last_name": player_id,
    }


def slot(position: str, player_id: str, role: str) -> dict:
    return {"position": position, "player": player(player_id, role)}


DEF_ROLES = {"LB", "CB", "RB"}
MID_ROLES = {"DM", "CM", "LM", "RM", "AM"}


def test_catalog_has_every_formation_with_eleven_slots():
    assert len(FORMATION_ORDER) == 20
    assert set(FORMATION_ORDER) == set(FORMATIONS)
    for formation in FORMATION_ORDER:
        slots = FORMATIONS[formation]
        assert len(slots) == 11
        assert slots[0]["position"] == "GK"
        assert sum(slot["position"] != "GK" for slot in slots) == 10


def test_catalog_exposes_compatible_roles():
    for option in formation_catalog():
        assert len(option["slots"]) == 11
        assert all(slot["roles"] for slot in option["slots"])


def test_formation_slots_do_not_overlap_on_reference_pitch():
    pitch_width, pitch_height = 827, 327
    card_width, card_height = 80, 65

    for formation in FORMATION_ORDER:
        slots = FORMATIONS[formation]
        for index, first in enumerate(slots):
            for second in slots[index + 1 :]:
                dx = abs(first["x"] - second["x"]) / 100 * pitch_width
                dy = abs(first["y"] - second["y"]) / 100 * pitch_height
                assert not (dx < card_width and dy < card_height), (
                    formation,
                    first["position"],
                    second["position"],
                )


def test_arrange_lineup_keeps_keeper_and_places_roles():
    current = [
        slot("GK", "gk", "GK"),
        slot("LB", "lb", "LB"),
        slot("CB", "cb1", "CB"),
        slot("CB", "cb2", "CB"),
        slot("RB", "rb", "RB"),
        slot("DM", "dm", "DM"),
        slot("CM", "cm1", "CM"),
        slot("CM", "cm2", "CM"),
        slot("LM", "lm", "LM"),
        slot("ST", "st1", "CF"),
        slot("RW", "st2", "CF"),
    ]

    order = arrange_lineup(current, "4-4-2")
    by_id = {player["id"]: player for player in (item["player"] for item in current)}

    assert order[0] == "gk"
    assert len(order) == 11
    assert len(set(order)) == 11

    templates = formation_slots("4-4-2")
    for index, player_id in enumerate(order):
        position = templates[index]["position"]
        role = by_id[player_id]["role"]
        if position == "GK":
            assert player_id == "gk"
        elif position in {"LB", "CB", "RB"}:
            assert role in DEF_ROLES
        elif position in {"DM", "CM", "LM", "RM", "AM"}:
            assert role in MID_ROLES
        else:
            assert role == "CF"


def test_arrange_lineup_switches_wide_players_to_strikers_when_needed():
    current = [
        slot("GK", "gk", "GK"),
        slot("LB", "lb", "LB"),
        slot("CB", "cb1", "CB"),
        slot("CB", "cb2", "CB"),
        slot("RB", "rb", "RB"),
        slot("DM", "dm", "DM"),
        slot("CM", "cm1", "CM"),
        slot("CM", "cm2", "CM"),
        slot("LW", "lw", "LM"),
        slot("ST", "st", "CF"),
        slot("RW", "rw", "RM"),
    ]

    order = arrange_lineup(current, "4-2-4")
    by_id = {player["id"]: player for player in (item["player"] for item in current)}
    templates = formation_slots("4-2-4")

    assert order[0] == "gk"
    for index in (8, 9):
        assert templates[index]["position"] == "ST"
    striker_roles = {by_id[order[8]]["role"], by_id[order[9]]["role"]}
    assert "CF" in striker_roles
    assert striker_roles & {"LM", "RM"}
