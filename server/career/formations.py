from __future__ import annotations

from functools import lru_cache

DEFAULT_FORMATION = "4-3-3"

FORMATION_ORDER = [
    "4-3-3",
    "4-5-1",
    "4-4-2",
    "4-4-2-diamond",
    "4-2-3-1",
    "3-4-3",
    "3-5-2",
    "2-3-5",
    "4-2-4",
    "3-6-1",
    "2-4-3-1",
    "4-1-4-1",
    "4-3-2-1",
    "3-2-4-1",
    "4-2-2-2",
    "4-4-1-1",
    "3-1-3-3",
    "3-1-4-2",
    "5-4-1",
    "4-1-3-2",
]

FORMATION_LABELS = {
    "4-3-3": "4-3-3",
    "4-5-1": "4-5-1",
    "4-4-2": "4-4-2",
    "4-4-2-diamond": "4-4-2 с ромбом",
    "4-2-3-1": "4-2-3-1",
    "3-4-3": "3-4-3",
    "3-5-2": "3-5-2",
    "2-3-5": "2-3-5",
    "4-2-4": "4-2-4",
    "3-6-1": "3-6-1",
    "2-4-3-1": "2-4-3-1",
    "4-1-4-1": "4-1-4-1",
    "4-3-2-1": "4-3-2-1",
    "3-2-4-1": "3-2-4-1",
    "4-2-2-2": "4-2-2-2",
    "4-4-1-1": "4-4-1-1",
    "3-1-3-3": "3-1-3-3",
    "3-1-4-2": "3-1-4-2",
    "5-4-1": "5-4-1",
    "4-1-3-2": "4-1-3-2",
}

LINE_BY_ROLE = {
    "GK": "GK",
    "CB": "DEF",
    "LB": "DEF",
    "RB": "DEF",
    "DM": "MID",
    "CM": "MID",
    "LM": "MID",
    "RM": "MID",
    "AM": "MID",
    "CF": "ATT",
}

LINE_BY_POSITION = {
    "GK": "GK",
    "LB": "DEF",
    "CB": "DEF",
    "RB": "DEF",
    "DM": "MID",
    "CM": "MID",
    "LM": "MID",
    "RM": "MID",
    "AM": "MID",
    "LW": "ATT",
    "RW": "ATT",
    "ST": "ATT",
    "CF": "ATT",
}


def _slot(position: str, role: str, x: int, y: int, roles: list[str]) -> dict:
    return {"position": position, "role": role, "x": x, "y": y, "roles": roles}


GK = _slot("GK", "GK", 50, 92, ["GK"])

FORMATIONS: dict[str, list[dict]] = {
    "4-3-3": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("DM", "DM", 50, 58, ["DM", "CM", "CB"]),
        _slot("CM", "CM", 30, 47, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 70, 47, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("LW", "LM", 20, 24, ["LM", "RM", "AM", "CF", "CM"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
        _slot("RW", "RM", 80, 24, ["RM", "LM", "AM", "CF", "CM"]),
    ],
    "4-5-1": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("LM", "LM", 12, 50, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 31, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 50, 46, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 69, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 88, 50, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
    ],
    "4-4-2": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("LM", "LM", 15, 50, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 38, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 62, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 85, 50, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("ST", "CF", 37, 20, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 63, 20, ["CF", "AM", "LM", "RM"]),
    ],
    "4-4-2-diamond": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("DM", "DM", 50, 60, ["DM", "CM", "CB"]),
        _slot("CM", "CM", 30, 50, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 70, 50, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("AM", "AM", 50, 38, ["AM", "CM", "LM", "RM", "CF"]),
        _slot("ST", "CF", 37, 18, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 63, 18, ["CF", "AM", "LM", "RM"]),
    ],
    "4-2-3-1": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("DM", "DM", 38, 54, ["DM", "CM", "CB"]),
        _slot("DM", "DM", 62, 54, ["DM", "CM", "CB"]),
        _slot("AM", "LM", 18, 40, ["LM", "AM", "RM", "CM", "CF"]),
        _slot("AM", "AM", 50, 38, ["AM", "CM", "LM", "RM", "CF"]),
        _slot("AM", "RM", 82, 40, ["RM", "AM", "LM", "CM", "CF"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
    ],
    "3-4-3": [
        GK,
        _slot("CB", "CB", 25, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 50, 70, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 75, 77, ["CB", "LB", "RB"]),
        _slot("LM", "LM", 15, 50, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 38, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 62, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 85, 50, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("LW", "LM", 20, 22, ["LM", "RM", "AM", "CF", "CM"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
        _slot("RW", "RM", 80, 22, ["RM", "LM", "AM", "CF", "CM"]),
    ],
    "3-5-2": [
        GK,
        _slot("CB", "CB", 25, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 50, 70, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 75, 77, ["CB", "LB", "RB"]),
        _slot("LM", "LM", 12, 50, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 31, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 50, 46, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 69, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 88, 50, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("ST", "CF", 37, 20, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 63, 20, ["CF", "AM", "LM", "RM"]),
    ],
    "2-3-5": [
        GK,
        _slot("CB", "CB", 35, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 65, 77, ["CB", "LB", "RB"]),
        _slot("CM", "CM", 30, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 50, 46, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 70, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("LW", "LM", 10, 22, ["LM", "RM", "AM", "CF", "CM"]),
        _slot("ST", "CF", 30, 18, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 70, 18, ["CF", "AM", "LM", "RM"]),
        _slot("RW", "RM", 90, 22, ["RM", "LM", "AM", "CF", "CM"]),
    ],
    "4-2-4": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("CM", "CM", 38, 50, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 62, 50, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("LW", "LM", 12, 22, ["LM", "RM", "AM", "CF", "CM"]),
        _slot("ST", "CF", 37, 18, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 63, 18, ["CF", "AM", "LM", "RM"]),
        _slot("RW", "RM", 88, 22, ["RM", "LM", "AM", "CF", "CM"]),
    ],
    "3-6-1": [
        GK,
        _slot("CB", "CB", 25, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 50, 70, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 75, 77, ["CB", "LB", "RB"]),
        _slot("LM", "LM", 10, 50, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 26, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 42, 46, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 58, 46, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 74, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 90, 50, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
    ],
    "2-4-3-1": [
        GK,
        _slot("CB", "CB", 38, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 62, 77, ["CB", "LB", "RB"]),
        _slot("LM", "LM", 15, 52, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 38, 50, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 62, 50, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 85, 52, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("AM", "LM", 20, 32, ["LM", "AM", "RM", "CM", "CF"]),
        _slot("AM", "AM", 50, 32, ["AM", "CM", "LM", "RM", "CF"]),
        _slot("AM", "RM", 80, 32, ["RM", "AM", "LM", "CM", "CF"]),
        _slot("ST", "CF", 50, 12, ["CF", "AM", "LM", "RM"]),
    ],
    "4-1-4-1": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("DM", "DM", 50, 60, ["DM", "CM", "CB"]),
        _slot("LM", "LM", 15, 48, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 38, 46, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 62, 46, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 85, 48, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
    ],
    "4-3-2-1": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("CM", "CM", 30, 50, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 50, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 70, 50, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("AM", "LM", 20, 36, ["LM", "AM", "RM", "CM", "CF"]),
        _slot("AM", "RM", 80, 36, ["RM", "AM", "LM", "CM", "CF"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
    ],
    "3-2-4-1": [
        GK,
        _slot("CB", "CB", 25, 78, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 50, 70, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 75, 78, ["CB", "LB", "RB"]),
        _slot("DM", "DM", 30, 58, ["DM", "CM", "CB"]),
        _slot("DM", "DM", 70, 58, ["DM", "CM", "CB"]),
        _slot("LM", "LM", 12, 36, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 37, 36, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 63, 36, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 88, 36, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
    ],
    "4-2-2-2": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("DM", "DM", 38, 54, ["DM", "CM", "CB"]),
        _slot("DM", "DM", 62, 54, ["DM", "CM", "CB"]),
        _slot("AM", "LM", 25, 38, ["LM", "AM", "RM", "CM", "CF"]),
        _slot("AM", "RM", 75, 38, ["RM", "AM", "LM", "CM", "CF"]),
        _slot("ST", "CF", 37, 18, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 63, 18, ["CF", "AM", "LM", "RM"]),
    ],
    "4-4-1-1": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("LM", "LM", 15, 50, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 38, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 62, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 85, 50, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("AM", "AM", 50, 36, ["AM", "CM", "LM", "RM", "CF"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
    ],
    "3-1-3-3": [
        GK,
        _slot("CB", "CB", 25, 72, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 50, 72, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 75, 72, ["CB", "LB", "RB"]),
        _slot("DM", "DM", 50, 52, ["DM", "CM", "CB"]),
        _slot("CM", "CM", 30, 32, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 50, 32, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 70, 32, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("LW", "LM", 20, 22, ["LM", "RM", "AM", "CF", "CM"]),
        _slot("ST", "CF", 50, 12, ["CF", "AM", "LM", "RM"]),
        _slot("RW", "RM", 80, 22, ["RM", "LM", "AM", "CF", "CM"]),
    ],
    "3-1-4-2": [
        GK,
        _slot("CB", "CB", 25, 74, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 50, 72, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 75, 74, ["CB", "LB", "RB"]),
        _slot("DM", "DM", 50, 52, ["DM", "CM", "CB"]),
        _slot("LM", "LM", 15, 32, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 38, 32, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 62, 32, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 85, 32, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("ST", "CF", 37, 12, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 63, 12, ["CF", "AM", "LM", "RM"]),
    ],
    "5-4-1": [
        GK,
        _slot("LB", "LB", 10, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 30, 74, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 50, 72, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 70, 74, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 90, 74, ["RB", "RM", "CB", "LB"]),
        _slot("LM", "LM", 15, 50, ["LM", "AM", "CM", "RM", "CF"]),
        _slot("CM", "CM", 38, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 62, 48, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("RM", "RM", 85, 50, ["RM", "AM", "CM", "LM", "CF"]),
        _slot("ST", "CF", 50, 16, ["CF", "AM", "LM", "RM"]),
    ],
    "4-1-3-2": [
        GK,
        _slot("LB", "LB", 15, 74, ["LB", "LM", "CB", "RB"]),
        _slot("CB", "CB", 37, 77, ["CB", "LB", "RB"]),
        _slot("CB", "CB", 63, 77, ["CB", "LB", "RB"]),
        _slot("RB", "RB", 85, 74, ["RB", "RM", "CB", "LB"]),
        _slot("DM", "DM", 50, 52, ["DM", "CM", "CB"]),
        _slot("CM", "CM", 30, 32, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 50, 32, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("CM", "CM", 70, 32, ["CM", "DM", "AM", "LM", "RM"]),
        _slot("ST", "CF", 37, 12, ["CF", "AM", "LM", "RM"]),
        _slot("ST", "CF", 63, 12, ["CF", "AM", "LM", "RM"]),
    ],
}


def normalize_formation(formation: str | None) -> str:
    value = str(formation or "").strip()
    return value if value in FORMATIONS else DEFAULT_FORMATION


def formation_slots(formation: str | None) -> list[dict]:
    return FORMATIONS[normalize_formation(formation)]


def formation_label(formation: str | None) -> str:
    return FORMATION_LABELS[normalize_formation(formation)]


def formation_catalog() -> list[dict]:
    return [
        {
            "id": formation,
            "label": FORMATION_LABELS[formation],
            "slots": [
                {
                    "position": slot["position"],
                    "role": slot["role"],
                    "x": slot["x"],
                    "y": slot["y"],
                    "roles": list(slot["roles"]),
                }
                for slot in FORMATIONS[formation]
            ],
        }
        for formation in FORMATION_ORDER
    ]


def _fit_score(player: dict, slot: dict) -> float:
    role = str(player.get("role") or "")
    roles = slot["roles"]
    if role in roles:
        score = 100 - roles.index(role) * 6
    else:
        player_line = LINE_BY_ROLE.get(role)
        slot_line = LINE_BY_POSITION.get(str(slot.get("position") or ""))
        score = 30 if player_line and player_line == slot_line else 0
    return score + float(player.get("overall") or 0) * 0.01


def _assign_players(players: list[dict], slots: list[dict]) -> list[str]:
    count = len(slots)
    if len(players) < count:
        return [player["id"] for player in players]
    scores = [[_fit_score(player, slot) for slot in slots] for player in players[:count]]

    @lru_cache(maxsize=None)
    def solve(slot_index: int, mask: int) -> tuple[float, tuple[int, ...]]:
        if slot_index == count:
            return 0.0, ()
        best_score = -1.0
        best_order: tuple[int, ...] = ()
        for index in range(count):
            bit = 1 << index
            if mask & bit:
                continue
            rest_score, rest_order = solve(slot_index + 1, mask | bit)
            total = scores[index][slot_index] + rest_score
            if total > best_score:
                best_score = total
                best_order = (index,) + rest_order
        return best_score, best_order

    _, order = solve(0, 0)
    return [players[index]["id"] for index in order]


def arrange_lineup(current_slots: list[dict], formation: str) -> list[str]:
    if not current_slots:
        return []
    keeper = next(
        (slot for slot in current_slots if slot.get("position") == "GK"),
        current_slots[0],
    )
    keeper_id = keeper["player"]["id"]
    outfield = [
        slot["player"]
        for slot in current_slots
        if slot["player"]["id"] != keeper_id
    ][:10]
    outfield_slots = [
        slot for slot in formation_slots(formation) if slot["position"] != "GK"
    ]
    return [keeper_id, *_assign_players(outfield, outfield_slots)]
