import logging
import os
import sys

_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"
_configured = False


def get_logger(name: str) -> logging.Logger:
    global _configured
    if not _configured:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
        root = logging.getLogger()
        root.addHandler(handler)
        root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
        _configured = True
    return logging.getLogger(_resolve_entry_module_name(name))


def _resolve_entry_module_name(name: str) -> str:
    """Replace `__main__` with the entry module's dotted path when launched via `python -m`."""
    if name != "__main__":
        return name
    spec = getattr(sys.modules.get("__main__"), "__spec__", None)
    return spec.name if spec is not None else name
