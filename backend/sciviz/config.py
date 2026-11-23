"""Runtime configuration (environment variables with sensible defaults)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT.parent / ".env")  # workspace-level .env (outside the repo), if present


@dataclass(frozen=True)
class Settings:
    repo_root: Path = REPO_ROOT
    db_path: Path = field(default_factory=lambda: Path(os.getenv("SCIVIZ_DB", REPO_ROOT / "data" / "columbia.duckdb")))
    catalog_path: Path = field(
        default_factory=lambda: Path(os.getenv("SCIVIZ_CATALOG", REPO_ROOT / "catalog" / "columbia.yaml"))
    )
    workspaces_dir: Path = field(
        default_factory=lambda: Path(os.getenv("SCIVIZ_WORKSPACES", REPO_ROOT / "workspaces"))
    )
    cdn_cache_dir: Path = field(default_factory=lambda: Path(os.getenv("SCIVIZ_CDN_CACHE", REPO_ROOT / ".cdn_cache")))
    model: str = os.getenv("SCIVIZ_MODEL", "openai:gpt-6.2-sol")
    escalation_model: str = os.getenv("SCIVIZ_ESCALATION_MODEL", "openai:gpt-6.2-astra")
    budget_usd: float = float(os.getenv("SCIVIZ_BUDGET_USD", "50"))
    budget_warn_usd: float = float(os.getenv("SCIVIZ_BUDGET_WARN_USD", "35"))
    per_question_soft_cap_usd: float = float(os.getenv("SCIVIZ_QUESTION_CAP_USD", "1.5"))
    max_gate_revisions: int = int(os.getenv("SCIVIZ_MAX_GATE_REVISIONS", "3"))
    max_view_data_mb: float = float(os.getenv("SCIVIZ_MAX_VIEW_DATA_MB", "5"))
    viewport: tuple[int, int] = (1200, 800)


settings = Settings()

# USD per 1M tokens: (input, cached input, output). Reasoning tokens are billed as output.
# gpt-6.2-sol: OpenAI pricing page (2026-11-23). gpt-6.2-astra cached price is an estimate (5% of input).
PRICES: dict[str, tuple[float, float, float]] = {
    "gpt-6.2-sol": (2.00, 0.10, 10.00),
    "gpt-6.2-astra": (8.00, 0.40, 40.00),
}


def model_short_name(model: str) -> str:
    return model.split(":", 1)[-1]
