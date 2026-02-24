# Tigrigna Sentiment Analysis
### A Design Science Approach to Real-Time Sentiment Analysis for YouTube

This repository contains the dataset and source code for the **Tigrigna Sentiment Tool**, a browser extension developed to analyze public opinion on YouTube in real-time. This research addresses the gap in NLP tools for low-resource languages, specifically focusing on the Tigrigna language.

---

## 📊 Dataset Overview
The dataset consists of **30,353 manually annotated comments** collected via the YouTube API.

### Data Structure
The dataset is provided in `.csv` format with the following columns:

| Column | Description |
| :--- | :--- |
| **text** | The raw, original text as it appeared on YouTube. |
| **label** | The sentiment class (Positive, Negative, or Neutral). |

> **Data Quality Note:** This dataset represents a significant manual annotation effort. While every effort was made to ensure accuracy through a human-in-the-loop strategy, users should be aware of "label noise" inherent in social media text due to linguistic nuances, sarcasm, and subjectivity.

---

## 🛠 Model & Methodology
Using a **Bi-LSTM** architecture combined with **FastText** embeddings, the model was optimized for the unique morphological structure of Tigrigna.

* **Architecture:** Bi-LSTM (Bidirectional Long Short-Term Memory).
* **Embeddings:** FastText (100-Dimensional) trained on a custom Tigrigna corpus.
* **Hyperparameters:** * **44,000** Vocab Size (90% Coverage).
    * **32** Max Sequence Length.
* **Evaluation:** 70/15/15 stratified split.
* **Framework:** Design Science Research Methodology (DSRM).

### Performance Results
| Metric | Score |
| :--- | :--- |
| **Accuracy** | **82%** |
| **Macro F1-score** | **78%** |

---

## 🚀 The Browser Extension
The **Tigrigna Sentiment Tool** allows for real-time inference. 
1. **Fetch:** It grabs comments directly from the YouTube DOM.
2. **Process:** Data is sent to a Flask-based API for preprocessing.
3. **Display:** The sentiment distribution is visualized directly on the browser interface for the user.
