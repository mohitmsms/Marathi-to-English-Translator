"""
Load Marathi–English sample data from Excel into SQLite or MSSQL (pymssql).
Run: python excel_to_mssql.py  (or USE_SQLITE=1 for local SQLite)
"""
import sqlite3
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import pandas as pd

try:
    import pymssql
    HAS_PYMSSQL = True
except ImportError:
    HAS_PYMSSQL = False

from config import (
    EXCEL_PATH,
    EXCEL_SHEET,
    TABLE_NAME,
    USE_SQLITE,
    SQLITE_PATH,
    INSERT_BATCH_SIZE,
    get_pymssql_kwargs,
)

if not USE_SQLITE and not HAS_PYMSSQL:
    print("Install pymssql for MSSQL (pip install pymssql), or set USE_SQLITE=1 for local SQLite.")
    sys.exit(1)


# Map common Excel column names to canonical names (Marathi, English)
COLUMN_ALIASES = {
    "marathi": ["marathi", "Marathi", "marathi_text", "source", "मराठी"],
    "english": ["english", "English", "english_text", "target", "translation"],
}


def find_column(df, kind):
    """Find column name for marathi or english from aliases."""
    for col in df.columns:
        c = str(col).strip()
        if c in COLUMN_ALIASES[kind]:
            return col
        if kind == "marathi" and ("marathi" in c.lower() or "source" in c.lower() or "मराठी" in c):
            return col
        if kind == "english" and ("english" in c.lower() or "target" in c.lower() or "translation" in c.lower()):
            return col
    # fallback: first column = marathi, second = english
    if kind == "marathi" and len(df.columns) >= 1:
        return df.columns[0]
    if kind == "english" and len(df.columns) >= 2:
        return df.columns[1]
    return None


def load_excel(excel_path, sheet=0):
    """Load Excel into DataFrame; normalize to marathi_text, english_text."""
    path = Path(excel_path)
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)
    df = pd.read_excel(path, sheet_name=sheet, engine="openpyxl")
    df = df.dropna(how="all")
    if df.empty:
        raise ValueError("Excel sheet is empty or has no data rows")
    marathi_col = find_column(df, "marathi")
    english_col = find_column(df, "english")
    if marathi_col is None:
        raise ValueError("Could not find Marathi column. Columns: " + ", ".join(str(c) for c in df.columns))
    if english_col is None:
        raise ValueError("Could not find English column. Columns: " + ", ".join(str(c) for c in df.columns))
    out = pd.DataFrame()
    out["marathi_text"] = df[marathi_col].astype(str).str.strip()
    out["english_text"] = df[english_col].astype(str).str.strip()
    out = out[(out["marathi_text"] != "") & (out["marathi_text"] != "nan")]
    return out


def create_table_mssql(cursor, table_name):
    """Create MSSQL table if it does not exist."""
    sql = f"""
    IF NOT EXISTS (
        SELECT * FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_NAME = N'{table_name}'
    )
    CREATE TABLE [{table_name}] (
        id INT IDENTITY(1,1) PRIMARY KEY,
        marathi_text NVARCHAR(MAX) NOT NULL,
        english_text NVARCHAR(MAX) NOT NULL,
        created_at DATETIME2 DEFAULT GETUTCDATE()
    );
    """
    cursor.execute(sql)
    cursor.connection.commit()


def create_table_sqlite(cursor, table_name):
    """Create SQLite table if it does not exist."""
    sql = f"""
    CREATE TABLE IF NOT EXISTS [{table_name}] (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        marathi_text TEXT NOT NULL,
        english_text TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    );
    """
    cursor.execute(sql)
    cursor.connection.commit()


def insert_batch(cursor, table_name, df, param_style="%s"):
    """Insert DataFrame in batches (executemany per chunk). param_style: '?' for SQLite, '%s' for pymssql."""
    ph = param_style
    sql = f"INSERT INTO [{table_name}] (marathi_text, english_text) VALUES ({ph}, {ph})"
    total = len(df)
    batch_size = INSERT_BATCH_SIZE if INSERT_BATCH_SIZE > 0 else total
    inserted = 0
    for start in range(0, total, batch_size):
        chunk = df.iloc[start : start + batch_size]
        rows = [
            (str(m).replace("'", "''")[:4000], str(e).replace("'", "''")[:4000])
            for m, e in zip(chunk["marathi_text"], chunk["english_text"])
        ]
        cursor.executemany(sql, rows)
        cursor.connection.commit()
        inserted += len(rows)
        if batch_size < total:
            print(f"  Inserted {inserted}/{total} rows...")


def get_connection_sqlite():
    """Return (conn, cursor, param_style) for SQLite. param_style is '?'."""
    path = Path(__file__).resolve().parent / SQLITE_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn, conn.cursor(), "?"


def get_connection_mssql():
    """Return (conn, cursor, param_style) using pymssql only."""
    if not HAS_PYMSSQL:
        raise RuntimeError("pymssql not installed. Install it: pip install pymssql")
    conn = pymssql.connect(**get_pymssql_kwargs())
    return conn, conn.cursor(), "%s"


def run():
    base = Path(__file__).resolve().parent
    excel_path = base / EXCEL_PATH
    sheet = EXCEL_SHEET

    print("Loading Excel:", excel_path)
    df = load_excel(excel_path, sheet)
    print(f"Loaded {len(df)} rows. Columns: marathi_text, english_text")

    if USE_SQLITE:
        print("Using SQLite (local file, no server required)...")
        conn, cursor, param_style = get_connection_sqlite()
        print(f"Creating table '{TABLE_NAME}' if not exists...")
        create_table_sqlite(cursor, TABLE_NAME)
    else:
        print("Connecting to MSSQL...")
        try:
            conn, cursor, param_style = get_connection_mssql()
        except Exception as e:
            print("MSSQL connection failed:", e)
            print("\nOn Mac, SQL Server is not available. Use SQLite instead:")
            print("  USE_SQLITE=1 python excel_to_mssql.py")
            sys.exit(1)
        print(f"Creating table '{TABLE_NAME}' if not exists...")
        create_table_mssql(cursor, TABLE_NAME)

    print(f"Inserting {len(df)} rows into [{TABLE_NAME}]...")
    insert_batch(cursor, TABLE_NAME, df, param_style)

    cursor.execute(f"SELECT COUNT(*) FROM [{TABLE_NAME}]")
    total = cursor.fetchone()[0]
    print(f"Done. Total rows in [{TABLE_NAME}]: {total}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    run()
