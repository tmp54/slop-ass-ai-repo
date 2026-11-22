"""Versioned prompt files. Bump the version suffix in the filename (and the constants below) on any change."""

from functools import lru_cache
from pathlib import Path

DRAFT_BRIEF_VERSION = "draft_brief_v1"
COMPARE_RESTATEMENT_VERSION = "compare_restatement_v1"

_DIR = Path(__file__).parent


@lru_cache
def load_prompt(name: str) -> str:
    return (_DIR / f"{name}.md").read_text(encoding="utf-8").strip()
