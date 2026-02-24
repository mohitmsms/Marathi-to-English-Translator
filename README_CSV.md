# Marathi → English: Translate CSV to CSV

This guide explains how to give a **CSV file** as input and get a **CSV file** as output with Marathi text translated to English using your fine-tuned model.

---

## Prerequisites

1. **Trained model**  
   You must have already run training and have the model saved:
   ```bash
   python train_model.py
   ```
   This creates the folder **`marathi_english_model/`** in the project directory. The CSV translation uses this folder.

2. **Dependencies**  
   Install project dependencies if you haven’t:
   ```bash
   pip install -r requirements.txt
   ```

---

## Input CSV format

- Your input file must be a **CSV** (comma-separated values).
- It must contain **at least one column** with **Marathi text** to translate.
- Other columns are allowed and will be **kept as-is** in the output.

**Example input CSV (`input.csv`):**

| id  | marathi_text                          | notes   |
|-----|----------------------------------------|--------|
| 1   | नमस्कार, तुम्ही कसे आहात?             | row 1  |
| 2   | आज हवामान चांगले आहे.                 | row 2  |

- The script will look for a column that contains Marathi. It checks for column names like: **marathi**, **Marathi**, **marathi_text**, **source**, **text**, **input**, or the first column if none of these exist.

---

## How to run

### Basic usage

From the project folder, run:

```bash
python translate_csv.py input.csv output.csv
```

- **`input.csv`** – path to your input CSV file.
- **`output.csv`** – path where you want the result CSV to be saved.

The script will:

1. Read the input CSV.
2. Find the Marathi column (automatically or by the option you pass).
3. Load the model from **`marathi_english_model/`**.
4. Translate each row’s Marathi text to English.
5. Write a new CSV with **all original columns plus one new column** named **`english_text`** containing the translation.

---

## Output CSV format

The output file is a CSV with:

- **All columns from the input CSV**, unchanged.
- **One extra column** (by default **`english_text`**) with the English translation for each row.

**Example output CSV (`output.csv`):**

| id  | marathi_text                          | notes   | english_text                    |
|-----|----------------------------------------|--------|----------------------------------|
| 1   | नमस्कार, तुम्ही कसे आहात?             | row 1  | Hello, how are you?              |
| 2   | आज हवामान चांगले आहे.                 | row 2  | The weather is good today.       |

---

## Options

You can customize the column names and batch size.

### Specify the Marathi column

If your Marathi text is in a column with a different name (e.g. **Marathi** or **source**):

```bash
python translate_csv.py input.csv output.csv --marathi-column "Marathi"
```

### Specify the output column name

To use a different name for the English column (e.g. **English** instead of **english_text**):

```bash
python translate_csv.py input.csv output.csv --output-column "English"
```

### Change batch size (speed vs memory)

Larger batches are faster but use more memory. Default is 16.

```bash
python translate_csv.py input.csv output.csv --batch-size 32
```

### Combined example

```bash
python translate_csv.py data.csv translated.csv --marathi-column "Marathi" --output-column "English" --batch-size 32
```

---

## Using environment variables

You can set paths and options in a **`.env`** file (or export them in the shell) and run the script without arguments:

**In `.env`:**

```
INPUT_CSV=input.csv
OUTPUT_CSV=output.csv
MARATHI_COLUMN=marathi_text
OUTPUT_COLUMN=english_text
TRANSLATE_BATCH_SIZE=16
```

Then run:

```bash
python translate_csv.py
```

The script reads these from `.env` if `python-dotenv` is installed.

---

## Quick reference

| What you want              | Command / setting |
|----------------------------|--------------------|
| Basic: input → output      | `python translate_csv.py input.csv output.csv` |
| Marathi in column "Marathi"| `--marathi-column "Marathi"` or `MARATHI_COLUMN=Marathi` |
| English column named "English" | `--output-column "English"` or `OUTPUT_COLUMN=English` |
| Faster (more RAM)          | `--batch-size 32` or `TRANSLATE_BATCH_SIZE=32` |
| Use different model folder | `MODEL_OUTPUT_DIR=other_model python translate_csv.py input.csv output.csv` |

---

## Troubleshooting

- **"Model not found"**  
  Ensure **`marathi_english_model/`** exists in the project folder. Train first with `python train_model.py`.

- **"Column not found"**  
  Check that the column name you passed (e.g. `--marathi-column`) exactly matches a header in your CSV. Column names are case-sensitive.

- **Input CSV not found**  
  Use the full path to the file, or run the script from the folder that contains the CSV.

- **Slow translation**  
  Use a smaller CSV to test, or increase `--batch-size` if you have enough RAM. On GPU, translation is faster.
