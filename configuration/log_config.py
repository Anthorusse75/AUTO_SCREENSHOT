import logging
import os
import shutil
from datetime import datetime
from dotenv import load_dotenv

def rotate_logs(log_dir: str, log_file: str, archive_dir: str, max_archives: int = 4):
    """Archive l'ancien fichier de log et conserve les 4 dernières archives"""
    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
        os.makedirs(archive_dir, exist_ok=True)

        # Nom d'archive avec timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        archive_path = os.path.join(archive_dir, f"bluestacks_{timestamp}.log")
        shutil.move(log_file, archive_path)

        # Nettoyage des archives anciennes
        archives = sorted(
            [f for f in os.listdir(archive_dir) if f.endswith(".log")],
            key=lambda f: os.path.getmtime(os.path.join(archive_dir, f))
        )

        while len(archives) > max_archives:
            to_delete = archives.pop(0)
            os.remove(os.path.join(archive_dir, to_delete))

def setup_logger():
    load_dotenv()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    log_dir = "logs"
    archive_dir = os.path.join(log_dir, "archives")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, "bluestacks.log")

    # Archive l'ancien log avant de démarrer
    rotate_logs(log_dir, log_file, archive_dir)

    logger = logging.getLogger("bluestacks")
    logger.setLevel(log_level)

    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')  # Écrase le fichier à chaque démarrage
    file_handler.setFormatter(formatter)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger


def toggle_debug(logger: logging.Logger) -> None:
    """Basculer dynamiquement entre les niveaux INFO et DEBUG."""
    new_level = logging.DEBUG if logger.level != logging.DEBUG else logging.INFO
    logger.setLevel(new_level)
    for handler in logger.handlers:
        handler.setLevel(new_level)
    logger.info("Nouveau niveau de log : %s", logging.getLevelName(new_level))
