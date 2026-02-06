# Marathi → English Translator

Pipeline: load Excel translation data into a database (SQLite or MSSQL via pymssql), then fine-tune a translation model.

## Prerequisites

- Python 3.8+
- Excel file: `Marathi to English data for LLM.xlsx` in the project folder
- For MSSQL: SQL Server + **pymssql** (`pip install pymssql`)
- For local run: **SQLite** (built-in); set `USE_SQLITE=1`

## Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set values if using MSSQL.

---

## Step 1: Load data (Excel → database)

**SQLite (no server):**
```bash
USE_SQLITE=1 python excel_to_mssql.py
```

**MSSQL:** Create database `marathi_english`, set `MSSQL_SERVER`, `MSSQL_DATABASE`, `MSSQL_UID`, `MSSQL_PWD` in `.env`, then:
```bash
python excel_to_mssql.py
```

- Reads the Excel file, detects Marathi/English columns, creates table `marathi_english_pairs`, inserts rows.
- For MSSQL table creation you can run `scripts/create_table.sql` after creating the database.

---

## Step 2: Fine-tune model

Training reads from **SQLite only** (run step 1 with `USE_SQLITE=1` first, or copy data into SQLite).

```bash
python train_model.py
```

- Loads pairs from `marathi_english.db`, fine-tunes **Helsinki-NLP/opus-mt-mr-en**, saves to `marathi_english_model/`.
- Quick test with fewer samples: `MAX_SAMPLES=5000 python train_model.py`

---

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| USE_SQLITE | 0 | Set to 1 for SQLite (no MSSQL) |
| SQLITE_PATH | marathi_english.db | SQLite file path |
| EXCEL_PATH | Marathi to English data for LLM.xlsx | Input Excel file |
| EXCEL_SHEET | 0 | Sheet index or name |
| TRANSLATION_TABLE | marathi_english_pairs | Table name |
| MSSQL_SERVER | localhost | SQL Server instance |
| MSSQL_DATABASE | marathi_english | Database name |
| MSSQL_UID / MSSQL_PWD | (empty) | SQL auth |
| MODEL_NAME | Helsinki-NLP/opus-mt-mr-en | Pretrained model |
| MODEL_OUTPUT_DIR | marathi_english_model | Output directory |
| TRAIN_EPOCHS | 3 | Training epochs |
| TRAIN_BATCH_SIZE | 8 | Batch size |
| MAX_SOURCE_LENGTH / MAX_TARGET_LENGTH | 128 | Max sequence lengths |
| TRAIN_SPLIT | 0.95 | Train fraction |
| LEARNING_RATE | 2e-5 | Learning rate |
| SAVE_STEPS | 5000 | Checkpoint interval |
| MAX_SAMPLES | (empty) | Limit rows for training |

## After training

Load the fine-tuned model:
```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
model = AutoModelForSeq2SeqLM.from_pretrained("marathi_english_model")
tokenizer = AutoTokenizer.from_pretrained("marathi_english_model")
```
