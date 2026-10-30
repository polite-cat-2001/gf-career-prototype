from __future__ import annotations

from server.career.condition import (
    blocked_player_ids,
    ensure_player_states,
    is_available,
    recover_condition,
)
from server.career.core import Career
from server.career.snapshot import lineup_for
from server.career.squad import (
    MIN_SQUAD_SIZE,
    TRANSFER_STATUSES,
    accept_counter,
    acknowledge_negotiation,
    ensure_shirt_numbers,
    sign_contract,
    start_negotiation,
)


class ActionError(ValueError):
    pass


def _journal(career: Career, kind: str, payload: dict) -> None:
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": kind,
            "payload": payload,
        }
    )


def _squad_player(players: list[dict], player_id: str) -> dict:
    for player in players:
        if str(player["id"]) == str(player_id):
            return player
    raise ActionError("player is not in this squad")


def swap_players(career: Career, players: list[dict], player_a: str, player_b: str) -> None:
    """Exchange two squad players.

    Starters swap slots; a starter and a bench player exchange places (the
    starter takes the bench player's position in the bench order); two bench
    players swap their positions in the bench order.
    """
    if player_a == player_b:
        raise ActionError("choose two different players")

    squad_ids = {player["id"] for player in players}
    if player_a not in squad_ids or player_b not in squad_ids:
        raise ActionError("player is not in this squad")
    ensure_player_states(career, [str(player["id"]) for player in players])
    recover_condition(career, career.date)
    if not is_available(career, player_a) or not is_available(career, player_b):
        raise ActionError("player is unavailable")

    blocked = blocked_player_ids(career)
    lineup = lineup_for(
        players,
        career.lineup,
        career.bench_order,
        blocked,
    )
    starters = [slot["player"]["id"] for slot in lineup["slots"]]
    bench = [player["id"] for player in lineup["bench"]]

    slot_a = starters.index(player_a) if player_a in starters else None
    slot_b = starters.index(player_b) if player_b in starters else None
    bench_a = bench.index(player_a) if player_a in bench else None
    bench_b = bench.index(player_b) if player_b in bench else None

    if slot_a is not None and slot_b is not None:
        starters[slot_a], starters[slot_b] = starters[slot_b], starters[slot_a]
        career.lineup = starters
    elif slot_a is not None or slot_b is not None:
        starter_id, bench_id = (player_a, player_b) if slot_a is not None else (player_b, player_a)
        slot = slot_a if slot_a is not None else slot_b
        bench_index = bench.index(bench_id)
        starters[slot] = bench_id
        bench[bench_index] = starter_id
        career.lineup = starters
        career.bench_order = bench
    else:
        bench[bench_a], bench[bench_b] = bench[bench_b], bench[bench_a]
        career.bench_order = bench

    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": "lineup.swap",
            "payload": {"player_a": player_a, "player_b": player_b},
        }
    )


def set_transfer_status(
    career: Career, players: list[dict], player_id: str, status: str | None
) -> None:
    player = _squad_player(players, player_id)
    player_id = str(player["id"])
    normalized = (status or "").strip().lower()
    if normalized in {"", "none", "clear"}:
        career.player_transfers.pop(player_id, None)
        normalized = "none"
    elif normalized in TRANSFER_STATUSES:
        career.player_transfers[player_id] = normalized
    else:
        raise ActionError("unknown transfer status")
    _journal(
        career,
        "player.transfer_status",
        {"player_id": player_id, "status": normalized},
    )


def set_shirt_number(
    career: Career, players: list[dict], player_id: str, number: int | None
) -> None:
    player = _squad_player(players, player_id)
    player_id = str(player["id"])
    if number is None:
        raise ActionError("shirt number is required")
    number = int(number)
    if not 1 <= number <= 99:
        raise ActionError("shirt number must be between 1 and 99")
    ensure_shirt_numbers(career, players)
    taken = {
        int(current)
        for other_id, current in career.shirt_numbers.items()
        if other_id != player_id
    }
    if number in taken:
        raise ActionError("shirt number is already taken")
    career.shirt_numbers[player_id] = number
    _journal(career, "player.shirt_number", {"player_id": player_id, "number": number})


def release_player(career: Career, player_id: str) -> None:
    player_id = str(player_id)
    if player_id not in career.player_ids:
        raise ActionError("player is not in this squad")
    if len(career.player_ids) <= MIN_SQUAD_SIZE:
        raise ActionError("the squad cannot drop below 11 players")
    career.player_ids.remove(player_id)
    if career.lineup:
        career.lineup = [item for item in career.lineup if item != player_id]
    if career.bench_order:
        career.bench_order = [item for item in career.bench_order if item != player_id]
    career.player_state.pop(player_id, None)
    career.player_contracts.pop(player_id, None)
    career.player_values.pop(player_id, None)
    career.player_ages.pop(player_id, None)
    career.shirt_numbers.pop(player_id, None)
    career.player_transfers.pop(player_id, None)
    career.negotiations.pop(player_id, None)
    _journal(career, "player.released", {"player_id": player_id})


def negotiate_contract(
    career: Career, players: list[dict], player_id: str, terms: dict
) -> None:
    player = _squad_player(players, player_id)
    player_id = str(player["id"])
    try:
        start_negotiation(career, player, player_id, terms)
    except ValueError as error:
        raise ActionError(str(error)) from error
    _journal(career, "contract.negotiation", {"player_id": player_id, "terms": terms})


def acknowledge_contract_negotiation(
    career: Career, players: list[dict], player_id: str
) -> None:
    player = _squad_player(players, player_id)
    player_id = str(player["id"])
    try:
        acknowledge_negotiation(career, player_id)
    except ValueError as error:
        raise ActionError(str(error)) from error
    _journal(career, "contract.negotiation.acknowledged", {"player_id": player_id})


def accept_counter_offer(career: Career, players: list[dict], player_id: str) -> None:
    player = _squad_player(players, player_id)
    player_id = str(player["id"])
    try:
        contract = accept_counter(career, player_id)
    except ValueError as error:
        raise ActionError(str(error)) from error
    _journal(
        career,
        "contract.signed",
        {"player_id": player_id, "contract": dict(contract)},
    )


def confirm_contract(career: Career, players: list[dict], player_id: str) -> None:
    player = _squad_player(players, player_id)
    player_id = str(player["id"])
    try:
        contract = sign_contract(career, player_id)
    except ValueError as error:
        raise ActionError(str(error)) from error
    _journal(
        career,
        "contract.signed",
        {"player_id": player_id, "contract": dict(contract)},
    )
