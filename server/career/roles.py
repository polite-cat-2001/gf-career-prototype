from __future__ import annotations

from server.career.core import Career

ROLE_IDS = (
    "captain",
    "free_kick_left",
    "free_kick_right",
    "free_kick_long",
    "penalties",
    "corner_left",
    "corner_right",
)

ROLE_WEIGHTS: dict[str, dict[str, float]] = {
    "captain": {
        "mental_calmness": 0.30,
        "mental_resilience": 0.25,
        "mental_workrate": 0.20,
        "mental_vision": 0.10,
        "overall": 0.15,
    },
    "free_kick_left": {
        "technical_shot": 0.25,
        "technical_highpass": 0.25,
        "physical_shotpower": 0.20,
        "mental_vision": 0.15,
        "technical_ballcontrol": 0.15,
    },
    "free_kick_right": {
        "technical_shot": 0.25,
        "technical_highpass": 0.25,
        "physical_shotpower": 0.20,
        "mental_vision": 0.15,
        "technical_ballcontrol": 0.15,
    },
    "free_kick_long": {
        "physical_shotpower": 0.35,
        "technical_shot": 0.25,
        "technical_highpass": 0.20,
        "mental_vision": 0.10,
        "technical_ballcontrol": 0.10,
    },
    "penalties": {
        "technical_shot": 0.35,
        "mental_calmness": 0.30,
        "physical_shotpower": 0.20,
        "technical_ballcontrol": 0.15,
    },
    "corner_left": {
        "technical_highpass": 0.40,
        "mental_vision": 0.25,
        "technical_ballcontrol": 0.20,
        "technical_shortpass": 0.15,
    },
    "corner_right": {
        "technical_highpass": 0.40,
        "mental_vision": 0.25,
        "technical_ballcontrol": 0.20,
        "technical_shortpass": 0.15,
    },
}


def _role_score(player: dict, weights: dict[str, float]) -> float:
    stats = player.get("stats") or {}
    total = 0.0
    weight = 0.0
    for key, share in weights.items():
        if key == "overall":
            value = player.get("overall")
        else:
            value = stats.get(key)
        if value is None:
            continue
        total += float(value) * share
        weight += share
    return total / weight if weight else 0.0


def default_assignments(players: list[dict]) -> dict[str, str]:
    if not players:
        return {}
    result: dict[str, str] = {}
    for role in ROLE_IDS:
        weights = ROLE_WEIGHTS[role]
        best = max(
            players,
            key=lambda player: (
                _role_score(player, weights),
                float(player.get("overall") or 0),
                str(player.get("id") or ""),
            ),
        )
        result[role] = str(best["id"])
    return result


def role_assignments(career: Career, starters: list[dict]) -> dict[str, str]:
    fallback = default_assignments(starters)
    starter_ids = {str(player["id"]) for player in starters}
    result: dict[str, str] = {}
    for role in ROLE_IDS:
        stored = career.role_assignments.get(role)
        result[role] = stored if stored in starter_ids else fallback.get(role, "")
    return result


def set_role_assignment(
    career: Career, starters: list[dict], role: str, player_id: str
) -> None:
    if role not in ROLE_IDS:
        raise ValueError("unknown role")
    player_id = str(player_id)
    if player_id not in {str(player["id"]) for player in starters}:
        raise ValueError("player is not in the starting lineup")
    career.role_assignments[role] = player_id
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "lineup.role",
            "payload": {"role": role, "player_id": player_id},
        }
    )
