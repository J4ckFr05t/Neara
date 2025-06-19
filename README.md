# Neara 🧠🔍

**Neara** is an interactive Streamlit-based fuzzy matching tool that helps analysts, data engineers, and researchers find *near matches* across CSV datasets. Whether you're trying to normalize messy country names, product codes, or free-text entries — Neara helps you match them against a master list, fast.

---

## 🚀 Features

- 📂 Upload any CSV file
- 🎯 Select one or more fields to perform fuzzy matching
- 🧾 Provide your own **master reference list** (inline or from file)
- 🧠 Uses **RapidFuzz** for high-performance approximate string matching
- ⚙️ Adjustable match threshold (60–100)
- ⚡ Parallel processing for faster matching on large datasets
- 📊 Per-field match statistics
- 📥 Download enriched dataset with match results and evidence

---

## 🔧 Use Cases

- Normalizing messy location, brand, or product name fields
- Matching log events against IOC lists or tags
- Mapping user-entered data to standard taxonomies
- Anything that requires *approximate string comparison*

---

## 🛠️ Requirements

- Python 3.8+
- Install dependencies:

```bash
pip install -r requirements.txt
```

**requirements.txt**
```
streamlit
pandas
rapidfuzz
```

---

## 🖥️ Running the App

```bash
streamlit run neara.py
```

---

## 📌 How It Works

1. Upload your CSV dataset.
2. Paste your master list of reference strings (one per line).
3. Select the fields from the CSV to apply fuzzy matching.
4. Set a similarity threshold.
5. Hit **Run Fuzzy Matching** — Neara will process each row in parallel.
6. View results, evidence, and download the updated dataset.

---

## 📤 Output

Neara appends two columns:

- `Matched Value`: the closest match (or `Not Found`)
- `Evidence`: the matched field, original value, matched string, and match score (only shown when a match is found)

---

## 🧠 Why RapidFuzz?

Unlike `fuzzywuzzy`, RapidFuzz:
- Is 10–20x faster
- Has no dependency on Python-Levenshtein
- Is production-ready and optimized for NLP-style tasks

---
