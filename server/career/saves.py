from __future__ import annotations

import json
import re
from pathlib import Path

from server.career.core import SAVE_VERSION, Career

SAVE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")


class SaveError(Exception):
    pass


class SaveNotFound(SaveError):
    pass


class SaveVersionError(SaveError):
    def __init__(self, version: int | None, expected: int):
        found = "is missing" if version is None else f"{version} is not supported"
        super().__init__(
            f"Save version {found}; this build requires version {expected}. "
            "Migrations are not available: start a new career or use a matching build."
        )
        self.version = version
        self.expected = expected


class SaveFormatError(SaveError):
    pass


class SaveStore:
    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, career_id: str) -> Path:
        if not SAVE_ID_PATTERN.fullmatch(career_id):
            raise SaveNotFound(career_id)
        return self.directory / f"{career_id}.json"

    def save(self, career: Career) -> None:
        path = self.path_for(career.id)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(career.to_save(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(path)

    def load(self, career_id: str) -> Career:
        path = self.path_for(career_id)
        if not path.is_file():
            raise SaveNotFound(career_id)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SaveFormatError(f"Save {career_id} is unreadable: {error}") from error
        version = raw.get("version")
        try:
            parsed_version = None if version is None else int(version)
        except (TypeError, ValueError):
            parsed_version = None
        if parsed_version != SAVE_VERSION:
            raise SaveVersionError(parsed_version, SAVE_VERSION)
        try:
            return Career.from_save(raw)
        except (KeyError, TypeError, ValueError) as error:
            raise SaveFormatError(f"Save {career_id} is malformed: {error}") from error

    def scan(self) -> list[dict]:
        entries = []
        for path in self.directory.glob("*.json"):
            entry = {"id": path.stem, "career": None, "raw": None, "error": None}
            try:
                entry["career"] = self.load(path.stem)
            except SaveError as error:
                entry["error"] = error
                try:
                    entry["raw"] = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    entry["raw"] = None
            entries.append(entry)
        return entries

    def list(self) -> list[Career]:
        careers = [entry["career"] for entry in self.scan() if entry["career"] is not None]
        careers.sort(key=lambda career: (career.updated_at, career.id), reverse=True)
        return careers

    def latest(self) -> Career | None:
        careers = self.list()
        return careers[0] if careers else None
