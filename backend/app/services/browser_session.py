"""Manage Playwright storageState per user and platform."""
from pathlib import Path

SESSIONS_DIR = Path("/app/browser_sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def session_path(user_id: int, platform: str) -> Path:
    return SESSIONS_DIR / f"{user_id}_{platform}.json"


def has_session(user_id: int, platform: str) -> bool:
    return session_path(user_id, platform).exists()


def delete_session(user_id: int, platform: str) -> None:
    path = session_path(user_id, platform)
    if path.exists():
        path.unlink()