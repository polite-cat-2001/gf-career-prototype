from __future__ import annotations

from server.career.core import Career
from server.career.snapshot import lineup_for


class ActionError(ValueError):
    pass


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

    lineup = lineup_for(players, career.lineup, career.bench_order)
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
