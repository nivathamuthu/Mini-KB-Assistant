import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt='{"level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
        )
    )
    root.addHandler(handler)
    root.setLevel(level.upper())
