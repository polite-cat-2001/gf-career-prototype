from __future__ import annotations

import hashlib
import random
from datetime import date, timedelta
from typing import Callable

from server.career.core import Career

SQUAD_MIN = 18
SQUAD_MAX = 30
MAX_BUYS = 3
MAX_SELLS = 3
BUDGET_SHARE = 0.10
MIN_MARKET_VALUE = 50_000
DEFAULT_BATCH_CLUBS = 120

WINDOW_BATCHES = ("opening", "middle", "last_week", "last_day")

ROLE_TARGETS = {
    "GK": 2,
    "CB": 3,
    "LB": 1,
    "RB": 1,
    "DM": 1,
    "CM": 2,
    "LM": 1,
    "RM": 1,
    "AM": 1,
    "CF": 2,
}

SquadSource = dict[str, list[dict]] | Callable[[list[str]], dict[str, list[dict]]]


def window_bounds(day: date) -> tuple[date, date] | None:
    if day.month == 1:
        return date(day.year, 1, 1), date(day.year, 1, 31)
    if day.month in (7, 8):
        return date(day.year, 7, 1), date(day.year, 8, 31)
    return None


def batch_schedule(
    window_start: str | date, window_end: str | date
) -> list[dict]:
    start = (
        window_start
        if isinstance(window_start, date)
        else date.fromisoformat(str(window_start)[:10])
    )
    end = (
        window_end
        if isinstance(window_end, date)
        else date.fromisoformat(str(window_end)[:10])
    )
    if end < start:
        return []
    middle = start + timedelta(days=(end - start).days // 2)
    last_week = max(start, end - timedelta(days=6))
    dates = [start, middle, last_week, end]
    period_starts = [start, middle, last_week, end]
    period_ends = [
        middle - timedelta(days=1),
        last_week - timedelta(days=1),
        end - timedelta(days=1),
        end,
    ]
    batches = []
    for key, trigger, period_start, period_end in zip(
        WINDOW_BATCHES, dates, period_starts, period_ends
    ):
        batches.append(
            {
                "key": f"{start.isoformat()}:{key}",
                "name": key,
                "date": trigger.isoformat(),
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "window_start": start.isoformat(),
                "window_end": end.isoformat(),
            }
        )
    return batches


def batches_between(
    previous_date: str | date | None, target_date: str | date
) -> list[dict]:
    target = (
        target_date
        if isinstance(target_date, date)
        else date.fromisoformat(str(target_date)[:10])
    )
    if previous_date is None:
        bounds = window_bounds(target)
        previous = bounds[0] - timedelta(days=1) if bounds else target
    else:
        previous = (
            previous_date
            if isinstance(previous_date, date)
            else date.fromisoformat(str(previous_date)[:10])
        )
    if target <= previous:
        return []

    batches: list[dict] = []
    for year in range(previous.year, target.year + 1):
        for month in (1, 7):
            bounds = window_bounds(date(year, month, 1))
            if bounds is None:
                continue
            start, end = bounds
            if end < previous or start > target:
                continue
            for batch in batch_schedule(start, end):
                trigger = date.fromisoformat(batch["date"])
                if previous < trigger <= target:
                    batches.append(batch)
    batches.sort(key=lambda batch: batch["date"])
    return batches


def _rng(career: Career, *parts: object) -> random.Random:
    return random.Random(":".join(str(part) for part in (career.seed, *parts)))


def _money(value: float) -> int:
    return max(0, int(round(value / 10_000) * 10_000))


def _market_value(player: dict) -> int:
    return max(int(player.get("market_value") or 0), MIN_MARKET_VALUE)


def _overall(player: dict) -> float:
    return float(player.get("overall") or 0)


def _role(player: dict) -> str:
    return str(player.get("role") or "")


def club_value(players: list[dict]) -> int:
    return sum(int(player.get("market_value") or 0) for player in players)


def club_budget(players: list[dict]) -> int:
    return int(club_value(players) * BUDGET_SHARE)


def role_counts(players: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for player in players:
        role = _role(player)
        counts[role] = counts.get(role, 0) + 1
    return counts


def _need(counts: dict[str, int], role: str) -> int:
    return max(0, ROLE_TARGETS.get(role, 1) - counts.get(role, 0))


def _load_squads(
    source: SquadSource,
    club_ids: list[str],
    career: Career | None = None,
    lookup: Callable[[list[str]], list[dict]] | None = None,
) -> dict[str, list[dict]]:
    if callable(source):
        loaded = source(club_ids) or {}
    else:
        loaded = source or {}
    squads = {}
    for club_id in club_ids:
        players = [dict(player) for player in loaded.get(str(club_id), [])]
        if career is not None:
            players = effective_players(career, club_id, players, lookup)
        squads[str(club_id)] = players
    return squads


def _window_counts(
    career: Career, window_start: str, window_end: str
) -> tuple[dict[str, int], dict[str, int]]:
    bought: dict[str, int] = {}
    sold: dict[str, int] = {}
    for transfer in career.world_transfers:
        day = str(transfer.get("date") or "")[:10]
        if not (window_start <= day <= window_end):
            continue
        buyer = str(transfer.get("to_club_id") or "")
        seller = str(transfer.get("from_club_id") or "")
        if buyer:
            bought[buyer] = bought.get(buyer, 0) + 1
        if seller:
            sold[seller] = sold.get(seller, 0) + 1
    return bought, sold


def _window_spend(
    career: Career, window_start: str, window_end: str
) -> dict[str, int]:
    spent: dict[str, int] = {}
    for transfer in career.world_transfers:
        day = str(transfer.get("date") or "")[:10]
        if not (window_start <= day <= window_end):
            continue
        buyer = str(transfer.get("to_club_id") or "")
        if not buyer:
            continue
        spent[buyer] = spent.get(buyer, 0) + int(transfer.get("fee") or 0)
    return spent


def _delta(career: Career, club_id: str) -> dict[str, list[str]]:
    club_id = str(club_id)
    delta = career.club_deltas.get(club_id)
    if delta is None:
        delta = {"in": [], "out": []}
        career.club_deltas[club_id] = delta
    delta.setdefault("in", [])
    delta.setdefault("out", [])
    return delta


def _attach(career: Career, club_id: str, player_id: str) -> None:
    delta = _delta(career, club_id)
    if player_id in delta["out"]:
        delta["out"].remove(player_id)
    if player_id not in delta["in"]:
        delta["in"].append(player_id)


def _detach(career: Career, club_id: str, player_id: str) -> None:
    delta = _delta(career, club_id)
    if player_id in delta["in"]:
        delta["in"].remove(player_id)
    if player_id not in delta["out"]:
        delta["out"].append(player_id)


def effective_players(
    career: Career,
    club_id: str,
    base_players: list[dict],
    lookup: Callable[[list[str]], list[dict]] | None = None,
) -> list[dict]:
    club_id = str(club_id)
    delta = career.club_deltas.get(club_id) or {}
    outgoing = {str(player_id) for player_id in delta.get("out") or []}
    players = {
        str(player["id"]): player
        for player in base_players
        if str(player["id"]) not in outgoing
    }
    added_ids = [
        str(player_id)
        for player_id in delta.get("in") or []
        if str(player_id) not in outgoing and str(player_id) not in players
    ]
    if added_ids and lookup is not None:
        for player in lookup(added_ids):
            players[str(player["id"])] = player
    return list(players.values())


def _select_sellers(
    players: list[dict], count: int, rng: random.Random
) -> list[dict]:
    if count <= 0:
        return []
    counts = role_counts(players)
    surplus = [
        player
        for player in players
        if counts.get(_role(player), 0) > ROLE_TARGETS.get(_role(player), 1)
    ]
    pool = surplus or sorted(players, key=lambda player: (_overall(player), str(player["id"])))
    chosen: list[dict] = []
    pool = list(pool)
    for _ in range(count):
        if not pool:
            break
        player = rng.choice(pool)
        pool.remove(player)
        chosen.append(player)
    return chosen


def _pick_buyer_target(
    candidates: list[dict],
    players: list[dict],
    budget: int,
    rng: random.Random,
    club_id: str | None = None,
) -> dict | None:
    affordable = [
        candidate
        for candidate in candidates
        if candidate["value"] <= budget
        and str(candidate["from_club_id"]) != str(club_id)
    ]
    if not affordable:
        return None
    counts = role_counts(players)
    wanted = [
        candidate
        for candidate in affordable
        if _need(counts, _role(candidate["player"])) > 0
    ]
    pool = wanted or affordable
    weights = []
    for candidate in pool:
        need = _need(counts, _role(candidate["player"]))
        weights.append(1.0 + need * 3.0)
    return rng.choices(pool, weights=weights, k=1)[0]


def _pick_free_agent(
    free_agents: list[dict], players: list[dict], rng: random.Random
) -> dict | None:
    if not free_agents:
        return None
    counts = role_counts(players)
    wanted = [
        player for player in free_agents if _need(counts, _role(player)) > 0
    ]
    pool = wanted or free_agents
    return rng.choice(pool)


def _deal_dates(batch: dict, count: int, rng: random.Random) -> list[str]:
    if count <= 0:
        return []
    start = date.fromisoformat(batch["period_start"])
    end = date.fromisoformat(batch["period_end"])
    span = max(0, (end - start).days)
    if count <= span + 1:
        offsets = sorted(rng.sample(range(span + 1), count))
    else:
        offsets = sorted(rng.randrange(span + 1) for _ in range(count))
    return [(start + timedelta(days=offset)).isoformat() for offset in offsets]


def _record(
    career: Career,
    player: dict,
    from_club_id: str | None,
    to_club_id: str,
    fee: int,
    day: str,
    rng: random.Random,
) -> dict:
    kind = "free_agent" if from_club_id is None else "transfer"
    transfer = {
        "id": hashlib.sha1(
            f"{career.seed}:{day}:{from_club_id}:{to_club_id}:{player['id']}:"
            f"{len(career.world_transfers)}:{rng.random()}".encode("utf-8")
        ).hexdigest()[:16],
        "player_id": str(player["id"]),
        "player_name": str(player.get("name") or ""),
        "overall": round(_overall(player), 1),
        "from_club_id": None if from_club_id is None else str(from_club_id),
        "to_club_id": str(to_club_id),
        "fee": int(fee),
        "kind": kind,
        "date": day,
    }
    career.world_transfers.append(transfer)
    return transfer


def run_world_batch(
    career: Career,
    batch: dict,
    clubs: list[dict],
    squads: SquadSource,
    free_agents: list[dict] | None = None,
    *,
    player_lookup: Callable[[list[str]], list[dict]] | None = None,
    batch_clubs: int = DEFAULT_BATCH_CLUBS,
) -> list[dict]:
    own_club_id = str(career.club_id)
    ai_clubs = [
        club for club in clubs if str(club.get("id") or "") != own_club_id
    ]
    if not ai_clubs:
        return []

    rng = _rng(career, "world-market", batch["key"])
    if len(ai_clubs) > batch_clubs:
        ordered = sorted(ai_clubs, key=lambda club: str(club.get("id") or ""))
        sample = rng.sample(ordered, batch_clubs)
    else:
        sample = list(ai_clubs)
    club_ids = [str(club["id"]) for club in sample]
    local_squads = _load_squads(squads, club_ids, career, player_lookup)

    bought, sold = _window_counts(
        career, batch["window_start"], batch["window_end"]
    )
    spent = _window_spend(career, batch["window_start"], batch["window_end"])
    acquired: dict[str, set[str]] = {}
    for transfer in career.world_transfers:
        day = str(transfer.get("date") or "")[:10]
        if not (batch["window_start"] <= day <= batch["window_end"]):
            continue
        buyer = str(transfer.get("to_club_id") or "")
        if buyer:
            acquired.setdefault(buyer, set()).add(str(transfer.get("player_id") or ""))
    free_pool = list(free_agents or [])

    sale_pool: list[dict] = []
    for club in sample:
        club_id = str(club["id"])
        players = local_squads.setdefault(club_id, [])
        available = MAX_SELLS - sold.get(club_id, 0)
        room = len(players) - SQUAD_MIN
        max_sells = max(0, min(available, room))
        if max_sells <= 0:
            continue
        excess = max(0, len(players) - SQUAD_MAX)
        planned = max(rng.randint(0, max_sells), min(excess, max_sells))
        for player in _select_sellers(players, planned, rng):
            players.remove(player)
            sale_pool.append(
                {
                    "player": player,
                    "from_club_id": club_id,
                    "value": _market_value(player),
                }
            )

    deals: list[dict] = []
    for club in sample:
        club_id = str(club["id"])
        players = local_squads.setdefault(club_id, [])
        available = MAX_BUYS - bought.get(club_id, 0)
        room = SQUAD_MAX - len(players)
        max_buys = max(0, min(available, room))
        if max_buys <= 0:
            continue
        shortage = max(0, SQUAD_MIN - len(players))
        planned = max(rng.randint(0, max_buys), min(shortage, max_buys))
        for _ in range(planned):
            if len(players) >= SQUAD_MAX:
                break
            bought_ids = acquired.get(club_id, set())
            budget_players = [
                player for player in players if str(player["id"]) not in bought_ids
            ]
            budget_left = club_budget(budget_players) - spent.get(club_id, 0)
            target = (
                _pick_buyer_target(
                    sale_pool, players, budget_left, rng, club_id
                )
                if budget_left > 0
                else None
            )
            if target is not None:
                player = target["player"]
                value = int(target["value"])
                factor = 1.0 + rng.random() * 0.2
                fee = _money(max(value, MIN_MARKET_VALUE) * factor)
                if fee > budget_left:
                    sale_pool.remove(target)
                    continue
                sale_pool.remove(target)
                source_id = str(target["from_club_id"])
                _detach(career, source_id, str(player["id"]))
                _attach(career, club_id, str(player["id"]))
                local_squads.setdefault(source_id, [])
                players.append(player)
                acquired.setdefault(club_id, set()).add(str(player["id"]))
                spent[club_id] = spent.get(club_id, 0) + fee
                bought[club_id] = bought.get(club_id, 0) + 1
                sold[source_id] = sold.get(source_id, 0) + 1
                deals.append(
                    {
                        "player": player,
                        "from_club_id": source_id,
                        "to_club_id": club_id,
                        "fee": fee,
                    }
                )
                continue

            free_agent = _pick_free_agent(free_pool, players, rng)
            if free_agent is None:
                break
            _attach(career, club_id, str(free_agent["id"]))
            players.append(free_agent)
            free_pool.remove(free_agent)
            acquired.setdefault(club_id, set()).add(str(free_agent["id"]))
            bought[club_id] = bought.get(club_id, 0) + 1
            deals.append(
                {
                    "player": free_agent,
                    "from_club_id": None,
                    "to_club_id": club_id,
                    "fee": 0,
                }
            )

    dates = _deal_dates(batch, len(deals), rng)
    recorded: list[dict] = []
    for deal, day in zip(deals, dates):
        recorded.append(
            _record(
                career,
                deal["player"],
                deal["from_club_id"],
                deal["to_club_id"],
                int(deal["fee"]),
                day,
                rng,
            )
        )
    return recorded


def advance_world_market(
    career: Career,
    clubs: list[dict],
    squads: SquadSource,
    free_agents: list[dict] | None = None,
    *,
    previous_date: str | None = None,
    target_date: str | None = None,
    player_lookup: Callable[[list[str]], list[dict]] | None = None,
    batch_clubs: int = DEFAULT_BATCH_CLUBS,
) -> list[dict]:
    target = target_date or career.date
    previous = previous_date
    if previous is None:
        previous = career.world_market_date
    if previous is None:
        bounds = window_bounds(date.fromisoformat(str(target)[:10]))
        previous = (
            (bounds[0] - timedelta(days=1)).isoformat() if bounds else target
        )
    batches = batches_between(previous, target)
    recorded: list[dict] = []
    for batch in batches:
        recorded.extend(
            run_world_batch(
                career,
                batch,
                clubs,
                squads,
                free_agents,
                player_lookup=player_lookup,
                batch_clubs=batch_clubs,
            )
        )
    career.world_market_date = str(target)[:10]
    return recorded
