# Marathi → English: Load data into model and fine-tune

This step loads translation pairs from the SQLite database and fine-tunes a pretrained model (e.g. **Helsinki-NLP/opus-mt-mr-en**).

## Prerequisites

1. **Data in SQLite**  
   Run first:
   ```bash
   python excel_to_mssql.py
   ```
   This creates `marathi_english.db` with the `marathi_english_pairs` table.

2. **Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   (Includes `torch`, `transformers`, `datasets` – first run may take a few minutes.)

## Quick run (all data)

```bash
python train_model.py
```

- Reads all pairs from `marathi_english.db`
- Uses 95% for training, 5% for evaluation
- Fine-tunes **Helsinki-NLP/opus-mt-mr-en**
- Saves the fine-tuned model to **`marathi_english_model/`**

## Quick test (small subset)

To try with fewer samples (faster):

```bash
MAX_SAMPLES=5000 python train_model.py
```

## Environment variables

| Variable           | Default                         | Description                    |
|--------------------|----------------------------------|--------------------------------|
| MODEL_NAME         | Helsinki-NLP/opus-mt-mr-en      | Pretrained model to fine-tune  |
| MODEL_OUTPUT_DIR   | marathi_english_model           | Where to save the checkpoint   |
| TRAIN_EPOCHS       | 3                               | Number of training epochs      |
| TRAIN_BATCH_SIZE   | 8                               | Per-device batch size          |
| MAX_SOURCE_LENGTH  | 128                             | Max Marathi input length       |
| MAX_TARGET_LENGTH  | 128                             | Max English output length      |
| TRAIN_SPLIT        | 0.95                            | Fraction of data for training  |
| LEARNING_RATE      | 2e-5                            | Learning rate                  |
| SAVE_STEPS         | 5000                            | Save checkpoint every N steps  |
| MAX_SAMPLES        | (empty)                         | Limit rows (e.g. 10000)        |

## After training

- Model and tokenizer are in **`marathi_english_model/`**
- Use this folder in your API or inference script (e.g. load with `AutoModelForSeq2SeqLM.from_pretrained("marathi_english_model")` and `AutoTokenizer.from_pretrained("marathi_english_model")`).
