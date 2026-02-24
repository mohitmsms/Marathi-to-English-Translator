"""
Translate Marathi text from a CSV file and write results to a new CSV.
Input: CSV with a Marathi column. Output: same CSV with an added English column.

Usage:
  python translate_csv.py input.csv output.csv
  python translate_csv.py                    # uses env INPUT_CSV, OUTPUT_CSV
  MARATHI_COLUMN=source python translate_csv.py in.csv out.csv
"""
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import torch
import pandas as pd
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from config import (
    MODEL_OUTPUT_DIR,
    MAX_SOURCE_LENGTH,
    MAX_TARGET_LENGTH,
)

# CSV defaults (env or CLI)
INPUT_CSV_ENV = "INPUT_CSV"
OUTPUT_CSV_ENV = "OUTPUT_CSV"
MARATHI_COLUMN_ENV = "MARATHI_COLUMN"
OUTPUT_COLUMN_ENV = "OUTPUT_COLUMN"
BATCH_SIZE_ENV = "TRANSLATE_BATCH_SIZE"

MARATHI_COLUMN_ALIASES = [
    "marathi", "Marathi", "marathi_text", "source", "मराठी",
    "text", "input",
]


def find_marathi_column(df):
    """Return column name for Marathi text, or None."""
    for col in df.columns:
        c = str(col).strip()
        if c in MARATHI_COLUMN_ALIASES:
            return col
        if "marathi" in c.lower() or "source" in c.lower():
            return col
    return df.columns[0] if len(df.columns) >= 1 else None


def translate_batch(model, tokenizer, texts, device, batch_size=16):
    """Translate a list of Marathi strings; returns list of English strings."""
    if not texts:
        return []
    all_english = []
    for i in range(0, len(texts), batch_size):
        batch = [str(s).strip() if pd.notna(s) else "" for s in texts[i : i + batch_size]]
        encoded = tokenizer(
            batch,
            max_length=MAX_SOURCE_LENGTH,
            truncation=True,
            padding=True,
            return_tensors="pt",
        )
        with torch.no_grad():
            out = model.generate(
                **encoded.to(device),
                max_length=MAX_TARGET_LENGTH,
                num_beams=4,
            )
        decoded = tokenizer.batch_decode(out, skip_special_tokens=True)
        all_english.extend([t.strip() for t in decoded])
    return all_english


def main():
    parser = argparse.ArgumentParser(description="Translate Marathi CSV column to English and save CSV.")
    parser.add_argument("input_csv", nargs="?", default=None, help="Input CSV path")
    parser.add_argument("output_csv", nargs="?", default=None, help="Output CSV path")
    parser.add_argument("--marathi-column", "-m", default=None, help="Column name containing Marathi text (auto-detect if omitted)")
    parser.add_argument("--output-column", "-o", default=None, help="Column name for English output (default: english_text)")
    parser.add_argument("--batch-size", "-b", type=int, default=None, help="Batch size for inference (default: 16)")
    args = parser.parse_args()

    import os
    input_path = args.input_csv or os.getenv(INPUT_CSV_ENV)
    output_path = args.output_csv or os.getenv(OUTPUT_CSV_ENV)
    if not input_path or not output_path:
        parser.error("Provide input and output CSV (positional or INPUT_CSV and OUTPUT_CSV env vars).")

    base = Path(__file__).resolve().parent
    input_file = base / input_path if not Path(input_path).is_absolute() else Path(input_path)
    output_file = base / output_path if not Path(output_path).is_absolute() else Path(output_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_file}")

    marathi_col = args.marathi_column or os.getenv(MARATHI_COLUMN_ENV)
    output_col = args.output_column or os.getenv(OUTPUT_COLUMN_ENV) or "english_text"
    batch_size = args.batch_size or int(os.getenv(BATCH_SIZE_ENV, "16"))

    print(f"Reading CSV: {input_file}")
    df = pd.read_csv(input_file)
    if df.empty:
        raise ValueError("CSV is empty.")

    if marathi_col is None:
        marathi_col = find_marathi_column(df)
        print(f"Using Marathi column: {marathi_col}")
    elif marathi_col not in df.columns:
        raise ValueError(f"Column '{marathi_col}' not found. Columns: {list(df.columns)}")

    model_dir = base / MODEL_OUTPUT_DIR
    if not model_dir.exists():
        raise FileNotFoundError(f"Model not found: {model_dir}. Train first: python train_model.py")

    print(f"Loading model from {model_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = AutoModelForSeq2SeqLM.from_pretrained(str(model_dir))
    model.eval()
    device = next(model.parameters()).device

    texts = df[marathi_col].astype(str).tolist()
    n = len(texts)
    print(f"Translating {n} rows (batch_size={batch_size})...")
    english = translate_batch(model, tokenizer, texts, device, batch_size=batch_size)

    df[output_col] = english
    output_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file, index=False)
    print(f"Saved {n} rows to {output_file}")


if __name__ == "__main__":
    main()
