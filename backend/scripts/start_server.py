"""Start Uvicorn with deployment settings validated before worker creation."""

from __future__ import annotations

import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings, validate_runtime_settings


def main() -> None:
    validate_runtime_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        workers=settings.WEB_CONCURRENCY,
    )


if __name__ == "__main__":
    main()
