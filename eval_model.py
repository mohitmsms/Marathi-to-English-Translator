"""
Evaluate the fine-tuned Marathi→English model on the held-out eval set.
Uses the same train/test split as training (seed=42) and reports BLEU.
Run: python eval_model.py
"""
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sqlite3
import torch
from datasets import Dataset
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from config import (
    TABLE_NAME,
    USE_SQLITE,
    SQLITE_PATH,
    MODEL_OUTPUT_DIR,
    MAX_SOURCE_LENGTH,
    MAX_TARGET_LENGTH,
    TRAIN_SPLIT,
    MAX_SAMPLES,
)


def load_data_from_sqlite():
    """Load marathi_text, english_text from SQLite (same as train_model)."""
    if not USE_SQLITE:
        raise NotImplementedError("Eval from MSSQL not implemented; use USE_SQLITE=1.")
    db_path = Path(__file__).resolve().parent / SQLITE_PATH
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}. Run excel_to_mssql.py first.")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    limit = f" LIMIT {int(MAX_SAMPLES)}" if MAX_SAMPLES.strip() else ""
    rows = conn.execute(
        f"SELECT marathi_text, english_text FROM [{TABLE_NAME}] WHERE marathi_text IS NOT NULL AND english_text IS NOT NULL{limit}"
    ).fetchall()
    conn.close()
    return [{"marathi_text": r["marathi_text"], "english_text": r["english_text"]} for r in rows]


def main():
    base = Path(__file__).resolve().parent
    model_dir = base / MODEL_OUTPUT_DIR
    if not model_dir.exists():
        raise FileNotFoundError(f"Model not found: {model_dir}. Train first with: python train_model.py")

    print("Loading eval data from SQLite (same split as training)...")
    rows = load_data_from_sqlite()
    if not rows:
        raise RuntimeError("No rows in database. Run excel_to_mssql.py first.")

    dataset = Dataset.from_list(rows)
    split = dataset.train_test_split(test_size=1 - TRAIN_SPLIT, seed=42)
    eval_ds = split["test"]
    print(f"Eval set size: {len(eval_ds)}")

    print(f"Loading model and tokenizer from {model_dir}...")
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = AutoModelForSeq2SeqLM.from_pretrained(str(model_dir))
    model.eval()

    references = [s.strip() for s in eval_ds["english_text"]]
    marathi_inputs = [s.strip() for s in eval_ds["marathi_text"]]

    batch_size = 16
    hypotheses = []
    num_batches = (len(marathi_inputs) + batch_size - 1) // batch_size
    for i in range(0, len(marathi_inputs), batch_size):
        batch_idx = i // batch_size + 1
        if num_batches >= 5:
            print(f"  Evaluating batch {batch_idx}/{num_batches}...", flush=True)
        batch = marathi_inputs[i : i + batch_size]
        encoded = tokenizer(
            batch,
            max_length=MAX_SOURCE_LENGTH,
            truncation=True,
            padding=True,
            return_tensors="pt",
        )
        with torch.no_grad():
            out = model.generate(
                **encoded.to(model.device),
                max_length=MAX_TARGET_LENGTH,
                num_beams=4,
            )
        decoded = tokenizer.batch_decode(out, skip_special_tokens=True)
        hypotheses.extend([t.strip() for t in decoded])

    try:
        import sacrebleu
        bleu = sacrebleu.corpus_bleu(hypotheses, [references])
        print(f"\nBLEU: {bleu.score:.2f}")
        print(f"  (BP={bleu.bp:.4f}, ratio={bleu.sys_len / bleu.ref_len:.4f})")
    except ImportError:
        print("Install sacrebleu for BLEU: pip install sacrebleu")
        print("Showing first 5 predictions vs references instead:")
        for k in range(min(5, len(hypotheses))):
            print(f"  Marathi:  {marathi_inputs[k][:60]}...")
            print(f"  Ref:     {references[k][:60]}...")
            print(f"  Pred:    {hypotheses[k][:60]}...")
            print()
        return

    # Sample a few examples
    print("\n--- Sample translations (first 5) ---")
    for k in range(min(5, len(hypotheses))):
        print(f"Marathi:  {marathi_inputs[k]}")
        print(f"Ref:      {references[k]}")
        print(f"Pred:     {hypotheses[k]}")
        print()


if __name__ == "__main__":
    main()
