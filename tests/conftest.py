from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_canon_db import build_canon_db


@pytest.fixture(scope="session")
def canon_db(tmp_path_factory) -> Path:
    out_path = tmp_path_factory.mktemp("canon") / "canon.db"
    build_canon_db(REPO_ROOT / "data" / "json", None, out_path)
    return out_path


@pytest.fixture(scope="session")
def client(canon_db: Path):
    from fastapi.testclient import TestClient

    from server.app import create_app

    return TestClient(create_app(canon_db))
