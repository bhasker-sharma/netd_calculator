import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# logs/ folder sits at project root (one level above core/)
_LOG_DIR  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
_LOG_FILE = os.path.join(_LOG_DIR, "netd_calculator.log")

_FILE_FMT    = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s"
_CONSOLE_FMT = "%(levelname)-8s  %(name)s — %(message)s"
_DATE_FMT    = "%Y-%m-%d %H:%M:%S"


class AppLogger:
    """
    Central logging configurator for NETD Calculator.

    Usage
    -----
    Call once at startup::

        AppLogger.setup()

    Then anywhere in the codebase::

        log = AppLogger.get(__name__)
        log.info("something happened")
    """

    _initialized: bool = False

    @classmethod
    def setup(cls, level: int = logging.DEBUG) -> None:
        """Initialize root logger. Safe to call multiple times — runs only once."""
        if cls._initialized:
            return

        os.makedirs(_LOG_DIR, exist_ok=True)

        root = logging.getLogger()
        root.setLevel(level)

        # ── Rotating file handler — 5 MB per file, keep 3 backups ────────────
        file_handler = RotatingFileHandler(
            _LOG_FILE,
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(_FILE_FMT, _DATE_FMT))

        # ── Console handler — INFO and above ──────────────────────────────────
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(_CONSOLE_FMT))

        root.addHandler(file_handler)
        root.addHandler(console_handler)

        cls._initialized = True

        # ── Global unhandled-exception hook ───────────────────────────────────
        sys.excepthook = cls._handle_exception

        logging.getLogger(__name__).info("Logging initialized — file: %s", _LOG_FILE)

    @classmethod
    def get(cls, name: str) -> logging.Logger:
        """Return a named logger. Call setup() before using."""
        return logging.getLogger(name)

    @staticmethod
    def _handle_exception(exc_type, exc_value, exc_tb) -> None:
        """Write every unhandled exception to the log before the app dies."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let Ctrl-C through without clogging the log
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.getLogger("unhandled").critical(
            "Unhandled exception — application will exit",
            exc_info=(exc_type, exc_value, exc_tb),
        )
