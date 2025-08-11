import logging
from pathlib import Path
import builtins

def setup_logging(log_dir: str = "logs", filename: str = "app.log", level: int = logging.INFO) -> logging.Logger:
    """Configure root logger to write to a file in *log_dir* and override ``print``.

    The directory is created if it does not exist.  All calls to ``print`` after
    this function runs will be redirected to the logger at INFO level so that
    existing debugging statements are preserved in the log file.
    """
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log_file = log_path / filename

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    def log_print(*args, **kwargs):
        message = " ".join(str(arg) for arg in args)
        logging.getLogger().info(message)

    builtins.print = log_print
    return logging.getLogger()
