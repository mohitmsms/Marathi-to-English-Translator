# Marathi–English Data: Excel → Database (SQLite or MSSQL)

This pipeline loads sample translation data from the Excel file into a database. You can use **SQLite** (no server, works on Mac) or **MSSQL** (Windows/cloud).

## Option 1: SQLite (recommended on Mac)

No SQL Server needed. Data is stored in a local file `marathi_english.db`.

```bash
USE_SQLITE=1 python excel_to_mssql.py
```

Or add `USE_SQLITE=1` to a `.env` file in the project folder.

## Option 2: MSSQL

Use when you have SQL Server running (Windows or cloud).

## Prerequisites

- Python 3.8+
- **Excel**: `Marathi to English data for LLM.xlsx` in the project folder
- **SQLite**: Built into Python (no install). Use with `USE_SQLITE=1`.
- **MSSQL** (optional): SQL Server or SQL Server Express running (local or cloud)
- **ODBC**: On Windows, install [ODBC Driver 17 for SQL Server](https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server). On Mac, you can use `pymssql` or stick with SQLite.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create database (once, in SQL Server)**
   ```sql
   CREATE DATABASE marathi_english;
   ```
   Or run `scripts/create_table.sql` after creating the database.

3. **Configure connection**  
   Copy `.env.example` to `.env` and set:
   - `MSSQL_SERVER` – e.g. `localhost` or `localhost\SQLEXPRESS`
   - `MSSQL_DATABASE` – e.g. `marathi_english`
   - `MSSQL_UID` / `MSSQL_PWD` – if using SQL auth (leave blank for Windows auth)

## Run

From the project root:

```bash
python excel_to_mssql.py
```

- Reads `Marathi to English data for LLM.xlsx` (first sheet by default).
- Detects Marathi and English columns (by name or by position).
- Creates table `marathi_english_pairs` if it does not exist.
- Inserts all rows into SQLite (`marathi_english.db`) or MSSQL, depending on `USE_SQLITE`.

## Table schema (MSSQL)

| Column         | Type          | Description                |
|----------------|---------------|----------------------------|
| id             | INT IDENTITY  | Primary key                |
| marathi_text   | NVARCHAR(MAX) | Marathi source text        |
| english_text   | NVARCHAR(MAX) | English translation        |
| created_at     | DATETIME2     | Default GETUTCDATE()       |

## Optional: Mac/Linux without pyodbc

If you prefer `pymssql`:

1. `pip install pymssql`
2. In `config.py`, add a `get_pymssql_connection()` that uses `MSSQL_SERVER`, `MSSQL_UID`, `MSSQL_PWD`, `MSSQL_DATABASE`.
3. In `excel_to_mssql.py`, use that connection and cursor instead of pyodbc (same table and insert logic).

## Environment variables

| Variable            | Default                          | Description              |
|---------------------|----------------------------------|--------------------------|
| USE_SQLITE          | 0                                | Set to 1 for local SQLite (no MSSQL) |
| SQLITE_PATH         | marathi_english.db               | SQLite file name         |
| EXCEL_PATH          | Marathi to English data for LLM.xlsx | Input Excel file     |
| EXCEL_SHEET         | 0                                | Sheet index or name      |
| MSSQL_SERVER        | localhost                        | SQL Server instance      |
| MSSQL_DATABASE      | marathi_english                  | Database name            |
| MSSQL_DRIVER        | ODBC Driver 17 for SQL Server    | ODBC driver name         |
| MSSQL_UID / MSSQL_PWD | (empty)                       | SQL auth (optional)      |
| TRANSLATION_TABLE   | marathi_english_pairs            | Target table name        |
