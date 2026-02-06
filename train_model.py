"""
Load Marathi–English pairs from SQLite and fine-tune a translation model.
Run: python train_model.py
Uses Helsinki-NLP/opus-mt-mr-en by default; set MODEL_NAME to use another model.
"""
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sqlite3
from datasets import Dataset
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainingArguments,
    Seq2SeqTrainer,
)

from config import (
    TABLE_NAME,
    USE_SQLITE,
    SQLITE_PATH,
    MODEL_NAME,
    MODEL_OUTPUT_DIR,
    TRAIN_EPOCHS,
    TRAIN_BATCH_SIZE,
    MAX_SOURCE_LENGTH,
    MAX_TARGET_LENGTH,
    TRAIN_SPLIT,
    LEARNING_RATE,
    WARMUP_RATIO,
    SAVE_STEPS,
    MAX_SAMPLES,
)


def load_data_from_sqlite():
    """Load marathi_text, english_text from SQLite (or MSSQL – add if needed)."""
    if not USE_SQLITE:
        raise NotImplementedError("Training from MSSQL not implemented; use USE_SQLITE=1 and run excel_to_mssql.py first.")
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
    print("Loading data from SQLite...")
    rows = load_data_from_sqlite()
    if not rows:
        raise RuntimeError("No rows in database. Run excel_to_mssql.py first.")
    print(f"Loaded {len(rows)} pairs.")

    dataset = Dataset.from_list(rows)
    split = dataset.train_test_split(test_size=1 - TRAIN_SPLIT, seed=42)
    train_ds = split["train"]
    eval_ds = split["test"]
    print(f"Train: {len(train_ds)}, Eval: {len(eval_ds)}")

    print(f"Loading model and tokenizer: {MODEL_NAME}")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token_id = tokenizer.eos_token_id
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    def preprocess(examples):
        inputs = [s.strip() for s in examples["marathi_text"]]
        targets = [s.strip() for s in examples["english_text"]]
        model_inputs = tokenizer(
            inputs,
            max_length=MAX_SOURCE_LENGTH,
            truncation=True,
            padding="max_length",
            return_tensors=None,
        )
        labels = tokenizer(
            targets,
            max_length=MAX_TARGET_LENGTH,
            truncation=True,
            padding="max_length",
            return_tensors=None,
        )
        model_inputs["labels"] = [[(x if x != tokenizer.pad_token_id else -100) for x in seq] for seq in labels["input_ids"]]
        return model_inputs

    train_ds = train_ds.map(preprocess, batched=True, remove_columns=train_ds.column_names, desc="Tokenize train")
    eval_ds = eval_ds.map(preprocess, batched=True, remove_columns=eval_ds.column_names, desc="Tokenize eval")

    data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model, padding=True)

    output_dir = base / MODEL_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    args = Seq2SeqTrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=TRAIN_EPOCHS,
        per_device_train_batch_size=TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=TRAIN_BATCH_SIZE * 2,
        learning_rate=LEARNING_RATE,
        warmup_ratio=WARMUP_RATIO,
        save_steps=SAVE_STEPS,
        save_total_limit=2,
        eval_strategy="steps",
        eval_steps=SAVE_STEPS,
        logging_steps=500,
        predict_with_generate=True,
        fp16=False,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    print("Starting training...")
    trainer.train()
    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))
    print(f"Model saved to {output_dir}")


if __name__ == "__main__":
    main()
