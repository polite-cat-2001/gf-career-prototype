from __future__ import annotations

import random
from datetime import date, timedelta

from server.career.core import Career

MAX_SCOUTS = 6
INITIAL_SCOUTS = 2
CANDIDATES_SHOWN = 5
POOL_SIZE = 12
FOUND_CAP = 20
ROLE_GROUPS = {"", "GK", "DEF", "MID", "FWD"}
AGE_MIN = 16
AGE_MAX = 35
CONTRACT_MIN = 0
CONTRACT_MAX = 5

REGION_SPECS = [
    {
        "id": "british-isles",
        "name": "Британские острова",
        "x": 45,
        "y": 25,
        "countries": [
            "England",
            "Scotland",
            "Wales",
            "Northern Ireland",
            "Ireland",
        ],
    },
    {
        "id": "north-europe",
        "name": "Северная Европа",
        "x": 53,
        "y": 18,
        "countries": [
            "Norway",
            "Sweden",
            "Denmark",
            "Finland",
            "Iceland",
            "Faroe Islands",
        ],
    },
    {
        "id": "west-europe",
        "name": "Западная Европа",
        "x": 48,
        "y": 34,
        "countries": [
            "France",
            "Germany",
            "Netherlands",
            "Belgium",
            "Austria",
            "Switzerland",
            "Luxembourg",
        ],
    },
    {
        "id": "south-europe",
        "name": "Южная Европа",
        "x": 53,
        "y": 42,
        "countries": [
            "Spain",
            "Italy",
            "Portugal",
            "Türkiye",
            "Greece",
            "Croatia",
            "Serbia",
            "Albania",
            "North Macedonia",
            "Montenegro",
            "Kosovo",
            "Slovenia",
            "Malta",
            "Cyprus",
            "San Marino",
            "Andorra",
            "Gibraltar",
        ],
    },
    {
        "id": "east-europe",
        "name": "Восточная Европа",
        "x": 62,
        "y": 29,
        "countries": [
            "Russia",
            "Ukraine",
            "Belarus",
            "Poland",
            "Czech Republic",
            "Slovakia",
            "Hungary",
            "Romania",
            "Bulgaria",
            "Moldova",
            "Estonia",
            "Latvia",
            "Lithuania",
            "Armenia",
            "Azerbaijan",
            "Georgia",
            "Kazakhstan",
        ],
    },
    {
        "id": "north-america",
        "name": "Северная Америка",
        "x": 19,
        "y": 33,
        "countries": [
            "United States",
            "Canada",
            "Costa Rica",
            "Panama",
            "Nicaragua",
            "Puerto Rico",
            "Jamaica",
        ],
    },
    {
        "id": "latin-america",
        "name": "Латинская Америка",
        "x": 27,
        "y": 66,
        "countries": [
            "Brazil",
            "Argentina",
            "Uruguay",
            "Chile",
            "Colombia",
            "Peru",
            "Ecuador",
            "Paraguay",
            "Bolivia",
            "Venezuela",
            "Mexico",
        ],
    },
    {
        "id": "africa",
        "name": "Африка",
        "x": 52,
        "y": 62,
        "countries": [
            "Egypt",
            "Algeria",
            "Morocco",
            "Tunisia",
            "Senegal",
            "Nigeria",
            "Ghana",
            "South Africa",
            "Ethiopia",
            "Libya",
            "Uganda",
        ],
    },
    {
        "id": "asia-pacific",
        "name": "Азия и Океания",
        "x": 78,
        "y": 47,
        "countries": [
            "Japan",
            "China",
            "Chinese Taipei",
            "Hongkong",
            "India",
            "Indonesia",
            "Iran",
            "Iraq",
            "Israel",
            "Jordan",
            "Lebanon",
            "Malaysia",
            "Myanmar",
            "Oman",
            "Philippines",
            "Qatar",
            "Saudi Arabia",
            "Singapore",
            "Thailand",
            "United Arab Emirates",
            "Uzbekistan",
            "Vietnam",
            "Australia",
            "New Zealand",
            "Cambodia",
        ],
    },
]

SCOUT_POOL = [
    ("Brian Smith", "Canada"),
    ("Daniel Perez", "Spain"),
    ("Donald Wood", "United States"),
    ("Frank Cooper", "Canada"),
    ("Yago Acuña", "Mexico"),
    ("Juan Guerra", "Spain"),
    ("Telmo Jurado", "Spain"),
    ("Antonio Rizzo", "Italy"),
    ("Andre Domingues", "Portugal"),
    ("Celik Asker", "Türkiye"),
    ("Marek Nowak", "Poland"),
    ("Lukas Berg", "Sweden"),
    ("Nils Hansen", "Norway"),
    ("Marco Bianchi", "Italy"),
    ("Hugo Laurent", "France"),
    ("Kai Fischer", "Germany"),
    ("Owen Price", "England"),
    ("Callum Reid", "Scotland"),
    ("Diego Salas", "Argentina"),
    ("Rafael Costa", "Brazil"),
]


def _rng(career: Career, key: str) -> random.Random:
    return random.Random(f"{career.seed}:{key}")


def _add_days(iso_date: str, days: int) -> str:
    return (date.fromisoformat(iso_date) + timedelta(days=days)).isoformat()


def days_between(start: str, end: str) -> int:
    return max(0, (date.fromisoformat(end) - date.fromisoformat(start)).days)


def _journal(career: Career, kind: str, payload: dict) -> None:
    career.journal.append(
        {
            "seq": len(career.journal) + 1,
            "type": kind,
            "payload": payload,
        }
    )


def scout_pool(career: Career) -> list[dict]:
    rng = _rng(career, "scout-pool")
    pool = []
    for index in range(POOL_SIZE):
        name, nationality = SCOUT_POOL[index % len(SCOUT_POOL)]
        experience = 1 + rng.randint(0, 4)
        judgement = 1 + rng.randint(0, 4)
        price = max(
            10_000,
            int(
                round(
                    (
                        (experience * experience + judgement * judgement) * 30_000
                        + rng.randint(0, 24) * 5_000
                    )
                    / 1_000
                )
                * 1_000
            ),
        )
        pool.append(
            {
                "id": f"scout-{index + 1}",
                "name": name,
                "nationality": nationality,
                "experience": experience,
                "judgement": judgement,
                "price": price,
            }
        )
    return pool


def ensure_scouts(career: Career) -> None:
    if career.scouts:
        return
    pool = scout_pool(career)
    career.scouts = [
        {**scout, "hired_at": career.date} for scout in pool[:INITIAL_SCOUTS]
    ]


def scout_candidates(career: Career) -> list[dict]:
    ensure_scouts(career)
    hired = {str(scout["id"]) for scout in career.scouts}
    return [scout for scout in scout_pool(career) if str(scout["id"]) not in hired][
        :CANDIDATES_SHOWN
    ]


def _scout(career: Career, scout_id: str) -> dict:
    for scout in career.scouts:
        if str(scout["id"]) == str(scout_id):
            return scout
    raise ValueError("scout not found")


def hire_scout(career: Career, scout_id: str) -> dict:
    ensure_scouts(career)
    if len(career.scouts) >= MAX_SCOUTS:
        raise ValueError("all scout slots are occupied")
    candidate = next(
        (item for item in scout_pool(career) if str(item["id"]) == str(scout_id)),
        None,
    )
    if candidate is None:
        raise ValueError("scout is not available")
    if any(str(scout["id"]) == str(candidate["id"]) for scout in career.scouts):
        raise ValueError("scout is already hired")
    price = int(candidate["price"])
    if career.balance is not None and int(career.balance) < price:
        raise ValueError("not enough money to hire this scout")
    if career.balance is not None:
        career.balance = int(career.balance) - price
    scout = {**candidate, "hired_at": career.date}
    career.scouts.append(scout)
    _journal(
        career,
        "scouting.hired",
        {"scout_id": candidate["id"], "price": price},
    )
    return scout


def report_days(experience: int) -> int:
    return max(1, min(5, 6 - int(experience)))


def assign_player_report(career: Career, scout_id: str, player_id: str) -> dict:
    ensure_scouts(career)
    scout = _scout(career, scout_id)
    if str(scout_id) in career.scout_assignments:
        raise ValueError("this scout is already studying a player")
    if any(
        str(report.get("player_id")) == str(player_id)
        for report in career.scout_assignments.values()
    ):
        raise ValueError("this player is already being studied")
    if str(player_id) in career.scout_reports or str(player_id) in career.scout_found:
        raise ValueError("this player has already been studied")
    total = report_days(int(scout.get("experience") or 1))
    report = {
        "player_id": str(player_id),
        "scout_id": str(scout_id),
        "started_at": career.date,
        "due_at": _add_days(career.date, total),
        "days_total": total,
        "acknowledged": False,
    }
    career.scout_assignments[str(scout_id)] = report
    _journal(
        career,
        "scouting.report_started",
        {"scout_id": str(scout_id), "player_id": str(player_id), "days": total},
    )
    return report


def default_criteria() -> dict:
    return {
        "role": "",
        "age_min": None,
        "age_max": None,
        "contract_min": None,
        "contract_max": None,
    }


def normalize_criteria(raw: dict | None) -> dict:
    criteria = default_criteria()
    raw = raw or {}
    role = str(raw.get("role") or "").upper()
    criteria["role"] = role if role in ROLE_GROUPS else ""
    for key, low, high in (
        ("age", AGE_MIN, AGE_MAX),
        ("contract", CONTRACT_MIN, CONTRACT_MAX),
    ):
        minimum = raw.get(f"{key}_min")
        maximum = raw.get(f"{key}_max")
        try:
            minimum = int(minimum) if minimum is not None else None
        except (TypeError, ValueError):
            minimum = None
        try:
            maximum = int(maximum) if maximum is not None else None
        except (TypeError, ValueError):
            maximum = None
        if minimum is not None:
            minimum = max(low, min(high, minimum))
        if maximum is not None:
            maximum = max(low, min(high, maximum))
        if minimum is not None and maximum is not None and minimum > maximum:
            minimum, maximum = maximum, minimum
        criteria[f"{key}_min"] = minimum
        criteria[f"{key}_max"] = maximum
    return criteria


def start_network(
    career: Career,
    scout_id: str,
    region_id: str,
    country_id: str,
    region_name: str,
    country_name: str,
    criteria: dict | None = None,
) -> dict:
    ensure_scouts(career)
    _scout(career, scout_id)
    task = {
        "kind": "network",
        "region_id": str(region_id),
        "region_name": str(region_name),
        "country_id": str(country_id),
        "country_name": str(country_name),
        "criteria": normalize_criteria(criteria),
        "started_at": career.date,
        "last_tick": career.date,
        "found": [],
    }
    career.scout_tasks[str(scout_id)] = task
    if not any(
        str(network.get("country_id")) == str(country_id)
        for network in career.scout_networks
    ):
        career.scout_networks.append(
            {
                "region_id": str(region_id),
                "region_name": str(region_name),
                "country_id": str(country_id),
                "country_name": str(country_name),
                "created_at": career.date,
                "scout_id": str(scout_id),
            }
        )
    _journal(
        career,
        "scouting.network_started",
        {
            "scout_id": str(scout_id),
            "region_id": str(region_id),
            "country_id": str(country_id),
        },
    )
    return task


def update_task(career: Career, scout_id: str, criteria: dict | None) -> dict:
    task = career.scout_tasks.get(str(scout_id))
    if task is None or task.get("kind") != "network":
        raise ValueError("this scout has no network task")
    task["criteria"] = normalize_criteria(criteria)
    _journal(
        career,
        "scouting.task_updated",
        {"scout_id": str(scout_id), "criteria": dict(task["criteria"])},
    )
    return task


def task_days(career: Career, task: dict) -> int:
    return days_between(str(task.get("started_at") or career.date), career.date)


def report_progress(career: Career, report: dict) -> dict:
    total = max(1, int(report.get("days_total") or 1))
    started = str(report.get("started_at") or career.date)
    worked = min(total, days_between(started, career.date))
    return {"days_total": total, "days_left": max(0, total - worked), "days_worked": worked}


def scouted_ids(career: Career) -> set[str]:
    return set(career.scout_reports) | set(career.scout_found)


def remove_scouted(career: Career, player_id: str) -> None:
    player_id = str(player_id)
    if any(
        str(report.get("player_id")) == player_id
        for report in career.scout_assignments.values()
    ):
        raise ValueError("report is still in progress")
    removed = False
    if career.scout_reports.pop(player_id, None) is not None:
        removed = True
    if career.scout_found.pop(player_id, None) is not None:
        removed = True
    if not removed:
        raise ValueError("player is not in any report")
    for task in career.scout_tasks.values():
        task["found"] = [
            item for item in task.get("found") or [] if str(item) != player_id
        ]
    _journal(career, "scouting.removed", {"player_id": player_id})


def acknowledge_reports(career: Career) -> None:
    for entry in career.scout_reports.values():
        entry["acknowledged"] = True
    for entry in career.scout_found.values():
        entry["acknowledged"] = True


def scouting_counts(career: Career) -> dict:
    entries = list(career.scout_reports.values()) + list(career.scout_found.values())
    new = sum(1 for entry in entries if not entry.get("acknowledged"))
    return {"new": new, "updates": max(0, len(entries) - new), "total": len(entries)}


def _role_group(role: str | None) -> str:
    if role == "GK":
        return "GK"
    if role in {"CB", "LB", "RB", "LWB", "RWB", "SW"}:
        return "DEF"
    if role in {"DM", "CM", "LM", "RM", "AM"}:
        return "MID"
    if role in {"CF", "ST", "LW", "RW"}:
        return "FWD"
    return ""


def _matches(player: dict, criteria: dict, contract_months: int | None) -> bool:
    role = criteria.get("role") or ""
    if role and _role_group(player.get("role")) != role:
        return False
    age = player.get("age")
    age_min = criteria.get("age_min")
    age_max = criteria.get("age_max")
    if age is not None and age_min is not None and int(age) < int(age_min):
        return False
    if age is not None and age_max is not None and int(age) > int(age_max):
        return False
    if contract_months is not None:
        minimum = criteria.get("contract_min")
        maximum = criteria.get("contract_max")
        if minimum is not None and contract_months < int(minimum) * 12:
            return False
        if maximum is not None and contract_months > int(maximum) * 12:
            return False
    return True


def advance_scouting(career: Career, find_candidates) -> list[dict]:
    """Move scouting forward to ``career.date``.

    ``find_candidates(country_id, criteria)`` returns canon players for a
    country; contract filtering and de-duplication happen here.
    """
    events: list[dict] = []
    for scout_id, report in list(career.scout_assignments.items()):
        due_at = str(report.get("due_at") or career.date)
        if career.date < due_at:
            continue
        player_id = str(report["player_id"])
        career.scout_reports[player_id] = {
            "scout_id": str(scout_id),
            "completed_at": due_at,
            "acknowledged": False,
        }
        career.scout_assignments.pop(scout_id, None)
        events.append({"type": "report", "player_id": player_id})
        _journal(
            career,
            "scouting.report_ready",
            {"scout_id": str(scout_id), "player_id": player_id},
        )

    for scout_id, task in career.scout_tasks.items():
        if task.get("kind") != "network":
            continue
        last_tick = str(task.get("last_tick") or task.get("started_at") or career.date)
        if career.date <= last_tick:
            continue
        start = date.fromisoformat(last_tick) + timedelta(days=1)
        end = date.fromisoformat(career.date)
        scout = next(
            (item for item in career.scouts if str(item["id"]) == str(scout_id)),
            None,
        )
        rate = 1 + (int(scout.get("judgement") or 1) // 2 if scout else 0)
        day = start
        candidates = None
        while day <= end:
            current = len(task.get("found") or [])
            target = min(FOUND_CAP, current + rate)
            if current < target:
                if candidates is None:
                    candidates = _task_candidates(career, task, find_candidates)
                rng = _rng(career, f"found:{scout_id}:{day.isoformat()}")
                rng.shuffle(candidates)
                for candidate in candidates:
                    if current >= target:
                        break
                    player_id = str(candidate["id"])
                    if player_id in task.get("found", []):
                        continue
                    if player_id in career.scout_found or player_id in career.scout_reports:
                        continue
                    if player_id in career.player_ids:
                        continue
                    task.setdefault("found", []).append(player_id)
                    career.scout_found[player_id] = {
                        "scout_id": str(scout_id),
                        "found_at": day.isoformat(),
                        "acknowledged": False,
                    }
                    events.append({"type": "found", "player_id": player_id})
                    _journal(
                        career,
                        "scouting.player_found",
                        {"scout_id": str(scout_id), "player_id": player_id},
                    )
                    current += 1
            day += timedelta(days=1)
        task["last_tick"] = career.date
    return events


def _task_candidates(career: Career, task: dict, find_candidates) -> list[dict]:
    criteria = normalize_criteria(task.get("criteria"))
    players = find_candidates(str(task.get("country_id")), criteria)
    result = []
    seen = set()
    for player in players:
        player_id = str(player["id"])
        if player_id in seen:
            continue
        seen.add(player_id)
        contract_months = player.get("contract_months")
        if not _matches(player, criteria, contract_months):
            continue
        result.append(player)
    return result
