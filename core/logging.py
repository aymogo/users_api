import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure a simple structured console logger for the whole app."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        stream=sys.stdout,
    )
    # Quiet down noisy third-party loggers.
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)


logger = logging.getLogger("app")
