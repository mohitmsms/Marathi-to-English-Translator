"""
Configuration for Marathi–English translation data pipeline.
Uses environment variables for MSSQL connection (no secrets in code).
"""
import os
import sys

# Excel input
EXCEL_PATH = os.getenv("EXCEL_PATH", "Marathi to English data for LLM.xlsx")
EXCEL_SHEET = os.getenv("EXCEL_SHEET", "0")

# MSSQL connection (local or cloud) – pymssql only
MSSQL_SERVER = os.getenv("MSSQL_SERVER", "localhost")
MSSQL_DATABASE = os.getenv("MSSQL_DATABASE", "marathi_english")
MSSQL_UID = os.getenv("MSSQL_UID", "")
MSSQL_PWD = os.getenv("MSSQL_PWD", "")

# Table to store translation pairs
TABLE_NAME = os.getenv("TRANSLATION_TABLE", "marathi_english_pairs")

# SQLite when no MSSQL server (default on macOS)
_default_sqlite = "1" if sys.platform == "darwin" else ""
USE_SQLITE = os.getenv("USE_SQLITE", _default_sqlite).strip().lower() in ("1", "true", "yes")
SQLITE_PATH = os.getenv("SQLITE_PATH", "marathi_english.db")

# Translation model (fine-tuning)
MODEL_NAME = os.getenv("MODEL_NAME", "Helsinki-NLP/opus-mt-mr-en")
MODEL_OUTPUT_DIR = os.getenv("MODEL_OUTPUT_DIR", "marathi_english_model")
TRAIN_EPOCHS = int(os.getenv("TRAIN_EPOCHS", "3"))
TRAIN_BATCH_SIZE = int(os.getenv("TRAIN_BATCH_SIZE", "8"))
MAX_SOURCE_LENGTH = int(os.getenv("MAX_SOURCE_LENGTH", "128"))
MAX_TARGET_LENGTH = int(os.getenv("MAX_TARGET_LENGTH", "128"))
TRAIN_SPLIT = float(os.getenv("TRAIN_SPLIT", "0.95"))
LEARNING_RATE = float(os.getenv("LEARNING_RATE", "2e-5"))
WARMUP_RATIO = float(os.getenv("WARMUP_RATIO", "0.1"))
SAVE_STEPS = int(os.getenv("SAVE_STEPS", "5000"))
MAX_SAMPLES = os.getenv("MAX_SAMPLES", "")


def get_pymssql_kwargs():
    """Kwargs for pymssql.connect."""
    return {
        "server": MSSQL_SERVER,
        "database": MSSQL_DATABASE,
        "user": MSSQL_UID or None,
        "password": MSSQL_PWD or None,
    }
