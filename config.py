"""
Configuration for Marathi–English translation data pipeline.
Uses environment variables for MSSQL connection (no secrets in code).
"""
import os
import sys

# Excel input
EXCEL_PATH = os.getenv("EXCEL_PATH", "Marathi to English data for LLM.xlsx")
# Optional: sheet name (0 = first sheet)
EXCEL_SHEET = os.getenv("EXCEL_SHEET", "0")

# MSSQL connection (local or cloud)
# Examples:
#   Windows: "DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=marathi_english;Trusted_Connection=yes;"
#   With login: "...;UID=sa;PWD=YourPassword;"
#   Named instance: "SERVER=localhost\\SQLEXPRESS;..."
MSSQL_SERVER = os.getenv("MSSQL_SERVER", "localhost")
MSSQL_DATABASE = os.getenv("MSSQL_DATABASE", "marathi_english")
MSSQL_DRIVER = os.getenv("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server")
MSSQL_UID = os.getenv("MSSQL_UID", "")  # leave empty for Windows auth
MSSQL_PWD = os.getenv("MSSQL_PWD", "")

# Table to store translation pairs
TABLE_NAME = os.getenv("TRANSLATION_TABLE", "marathi_english_pairs")

# Use SQLite instead of MSSQL (no server needed; works on Mac/Linux)
# Default to SQLite on macOS (no SQL Server); set USE_SQLITE=0 to try MSSQL
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
TRAIN_SPLIT = float(os.getenv("TRAIN_SPLIT", "0.95"))  # 95% train, 5% eval
LEARNING_RATE = float(os.getenv("LEARNING_RATE", "2e-5"))
WARMUP_RATIO = float(os.getenv("WARMUP_RATIO", "0.1"))
SAVE_STEPS = int(os.getenv("SAVE_STEPS", "5000"))
MAX_SAMPLES = os.getenv("MAX_SAMPLES", "")  # empty = use all; set e.g. 10000 for quick test


def get_connection_string():
    """Build pyodbc connection string."""
    parts = [
        f"DRIVER={{{MSSQL_DRIVER}}}",
        f"SERVER={MSSQL_SERVER}",
        f"DATABASE={MSSQL_DATABASE}",
    ]
    if MSSQL_UID and MSSQL_PWD:
        parts.append(f"UID={MSSQL_UID}")
        parts.append(f"PWD={MSSQL_PWD}")
    else:
        parts.append("Trusted_Connection=yes")
    return ";".join(parts)


def get_pymssql_kwargs():
    """Kwargs for pymssql.connect (Mac/Linux alternative)."""
    return {
        "server": MSSQL_SERVER,
        "database": MSSQL_DATABASE,
        "user": MSSQL_UID or None,
        "password": MSSQL_PWD or None,
    }
