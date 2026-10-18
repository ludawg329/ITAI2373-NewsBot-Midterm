# ITAI2373-NewsBot-Midterm: Market NewsBot Intelligence System

**Author:** Wayne Lu (individual project, no team members)  
**Date:** October 17, 2026  
**Course:** ITAI 2373, Natural Language Processing, Houston Community College  
**Instructor:** Professor Sridhar Ganti  
**GitHub Repository:** https://github.com/ludawg329/ITAI2373-NewsBot-Midterm

### 🎥 Video demo
**[▶ Watch the narrated demo (MT_Video_Wayne_Lu_ITAI2373.mp4, 5:13)](demo/MT_Video_Wayne_Lu_ITAI2373.mp4)**. It is hosted in this repo, and GitHub plays it in the browser.

### 📄 Deliverables
- Notebook: [`MarketNewsBot.ipynb`](MarketNewsBot.ipynb) (Modules 1-8, executed with outputs; reflection and report are also at the end)
- Reflection (2 pages): [`REFLECTION.md`](REFLECTION.md) · [`NewsBot_Reflection_WayneLu.pdf`](NewsBot_Reflection_WayneLu.pdf)
- Report: [`REPORT.md`](REPORT.md) · [`MT_Report_Group_Individual_Wayne_Lu_ITAI2373.pdf`](MT_Report_Group_Individual_Wayne_Lu_ITAI2373.pdf)
- Live demo script: [`demo/live_demo.py`](demo/live_demo.py)

> ⚠️ Informational only, not investment, tax, or legal advice.

## Overview
An NLP system for market and financial news, built for individual investors and small-business owners. It covers all of Modules 1-8:
preprocessing → TF-IDF (tuned) → POS patterns → dependency parsing/SVO → sentiment (VADER + trained Bullish/Bearish/Neutral model, emotion lexicon)
→ multi-class classification (NB, Complement NB, LogReg, Linear SVM, tuned SVM+chi²) → NER (spaCy + custom TICKER/PERCENT rules)
→ integrated `NewsBotIntelligenceSystem` with watchlist matching, same-day alerts, ethics badges and a weekly Monday digest.

> 📌 Dataset approval for the Reuters full-article dataset was requested from the instructor through Canvas on 2026-10-14. An earlier headline-only version (about 87.5% accuracy) is kept in the commit history.

## Data (real, public)
- **Topic data: Reuters-21578 full newswire articles** (ModApte, 1987, English). Kaggle mirror: [thedevastator/uncovering-financial-insights-with-the-reuters-2](https://www.kaggle.com/datasets/thedevastator/uncovering-financial-insights-with-the-reuters-2) (CC0). The notebook loads the same corpus from the NLTK data mirror, so no Kaggle login is needed.
- Filtering: single-label documents only, in 6 topics (earn, acq, crude, money-fx, interest, trade). Stubs under 20 words are dropped and HTML entities are decoded. **53 exact-duplicate articles are removed before sampling or splitting.** The sample is capped at 333 per class, giving **1,703 articles** with no missing values: Earnings 333, Acquisitions 333, Crude Oil 317, Trade 286, Money/FX 249, Interest Rates 185.
- Evaluation: 80/20 stratified split (1,362 train, 341 test) with 5-fold CV on the training set only. A near-duplicate check (cosine ≥ 0.9 to any training article) flags 12 test articles (3.5%), and "clean test acc" excludes them.
- **Sentiment labels: Financial PhraseBank** (Malo et al. 2014; [takala/financial_phrasebank](https://huggingface.co/datasets/takala/financial_phrasebank), CC BY-NC-SA 3.0), using the 66%-agreement subset of 4,211 sentences mapped to Bearish/Bullish/Neutral.
- Live headlines: Federal Reserve and SEC press-release RSS feeds (headline, excerpt of 200 characters or less, and link). Test items marked `[SYNTHETIC]` exist only to exercise the alert and ethics rules.
- Backup full-article dataset: [jeet2016/us-financial-news-articles](https://www.kaggle.com/datasets/jeet2016/us-financial-news-articles).

## Results (Reuters full articles)
| Model | 5-fold CV acc (train) | Test acc | Test macro-F1 | Clean test acc |
|---|---|---|---|---|
| **mpnet-base embeddings + LogReg (auto-selected)** | **0.959 ± 0.008** | **0.950** | **0.942** | 0.957 |
| Linear SVM (word+char TF-IDF) | 0.955 | 0.944 | 0.933 | 0.951 |
| Tuned Linear SVM (word+char) | 0.954 | 0.944 | 0.933 | 0.951 |
| Stacking (LR + SVM + CNB → LR) | 0.951 | 0.947 | 0.937 | 0.954 |
| Linear SVM (word) | 0.948 | 0.944 | 0.933 | 0.951 |
| Logistic Regression (word) | 0.947 | 0.941 | 0.931 | 0.948 |
| Complement NB (word) | 0.924 | 0.924 | 0.912 | 0.930 |
| Naive Bayes (word) | 0.913 | 0.921 | 0.911 | 0.927 |

The model is selected automatically by mean CV accuracy, with test macro-F1 breaking ties. The mpnet embeddings are cached in `data/reuters_mpnet_embeddings.npz`, and the notebook downloads that file from this repo when it is missing locally. Set `USE_EMBEDDINGS = False` to skip mpnet on a slow CPU; the best TF-IDF model, Linear SVM (word+char), is about 0.4 points behind.
Earlier numbers (0.963) were measured before duplicate removal and were slightly optimistic.

**Sentiment** (Bullish/Bearish/Neutral, TF-IDF + LogReg trained on Financial PhraseBank): **0.78 accuracy** on held-out PhraseBank sentences (843), compared with **0.56 for VADER**. This model is trained on single sentences, so its labels on whole Reuters articles are an estimate and cannot be checked against labels.

**Known limitation:** the topic model learned from 1987 newswire. On modern short headlines it can mislabel, for example routing a Tesla earnings headline to Acquisitions, so the digest relies on watchlist and alert rules as well as the category.

## Segments and guardrails
Example watchlist segments: Trading (TSLA, HOOD, indices, semis, AI), Data Center Builds (rule-based category), Space (compliance check on every item), Starlink direct-to-cell, Telecom, Macro (Fed, inflation, rates, tax), and Business (small business, SBA; kept separate from trading news).
An example restricted list (for readers whose employer restricts certain stock holdings) sets an ethics status. BLOCK: BA, LMT, NOC, VSAT, SpaceX/SPCX. FLAG: IRDM, RDW, RKLB, ETN, UFO, ARKX, ITA. LOW: ASTS, LUNR, PL. BLOCK and FLAG items are never framed as trade ideas.
Account numbers are redacted. Only official RSS feeds are used, with a declared User-Agent. Nothing behind a paywall is scraped.

## Files
- `MarketNewsBot.ipynb`: the main notebook, executed with outputs.
- `data/reuters_newsbot_dataset.csv`: the prepared Reuters sample (1,703 articles). `data/reuters_mpnet_embeddings.npz`: cached sentence embeddings. `data/market_newsbot_dataset.csv` is the earlier headline sample.
- `src/build_notebook.py`: the script that generated the notebook from the course template. `src/build_notebook_reuters.py` builds this Reuters version (needs `template.ipynb` path as in build_notebook.py).
- `demo/`: the narrated video and `live_demo.py`, which rebuilds the selected model from the cached embeddings and runs new Fed/SEC press releases through it (`python demo/live_demo.py`).
- `REFLECTION.md`, `REPORT.md` and their PDF copies.

## My contributions
This was an individual project, so I (Wayne Lu) did all of it: the business case and watchlist, data selection, cleaning and duplicate removal, TF-IDF, POS, and syntax analysis, sentiment, the classifier comparison, NER, the integrated NewsBot (alerts, ethics filter, Monday digest), the repository, the video, the report, and the reflection. I used an AI assistant to help write and debug code, as the course allows.

## How to run
Open `MarketNewsBot.ipynb` in Google Colab or Jupyter and run all cells (uncomment the `pip install` line in the first code cell on Colab). Reuters loads from the NLTK data mirror and Financial PhraseBank from Hugging Face, so no Kaggle login is needed. The cached embeddings in `data/` keep the run short on a CPU.
