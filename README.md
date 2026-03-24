# 🏆 SportSearch — BM25 Sports Search Engine

**Student:** Emiliano Galaviz Gomez
**Domain:** Sports (Football, Formula 1, NBA)
**Enhancement:** C — Autocomplete

---

## 📋 Domain Justification

Sports was chosen because it provides a rich, diverse vocabulary across three sub-domains (football, F1, NBA) with real proper nouns (player names, team names, race circuits) that make autocomplete particularly useful and natural. Users searching for "Verstappen", "Champions League", or "three-point" benefit directly from term suggestions as they type.

---

## ✨ Implemented Enhancement — C: Autocomplete

A **Trie-based autocomplete** system built from scratch (no libraries):

- A `TrieNode` and `Trie` class store all raw vocabulary from the corpus.
- Each node tracks term frequency, so suggestions are sorted by how often a word appears across documents.
- The frontend sends a request to `/autocomplete?q=<prefix>` on every keystroke (debounced 160 ms).
- Results appear in a styled dropdown with the matched prefix highlighted.
- Full keyboard navigation: ↑ ↓ to select, Enter to confirm, Esc to dismiss.

---

## 🗂 Project Structure

```
my-search-engine/
├── README.md
├── corpus.json          # 25 real sports documents (Football, F1, NBA)
├── search_engine.py     # Tokenizer · Stemmer · Inverted Index · BM25 · Trie
├── app.py               # Flask server (routes: / /search /autocomplete /stats)
├── templates/
│   └── index.html       # Main page
├── static/
│   ├── style.css        # Dark editorial sports design
│   └── app.js           # Search · Autocomplete · Highlighting · Category filter
├── requirements.txt     # flask==3.1.0
├── Dockerfile
└── docker-compose.yml
```

---

## 🚀 Run Instructions

### Option A — Docker (recommended)

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/sports-search-engine.git
cd sports-search-engine

# 2. Build and start
docker compose up --build

# 3. Open in browser
open http://localhost:5000
```

To stop:
```bash
docker compose down
```

### Option B — Local Python

```bash
# Requires Python 3.10+
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

---

## 🔍 Demo Queries

| Query | Expected top result |
|-------|---------------------|
| `Messi World Cup Argentina` | Argentina World Cup Victory Qatar 2022 |
| `Verstappen champion Red Bull` | Max Verstappen Formula 1 World Champion 2023 |
| `LeBron scoring record Lakers` | LeBron James surpasses Kareem scoring record |
| `tiki taka Barcelona Guardiola` | FC Barcelona tiki-taka era |
| `Monaco Grand Prix Senna` | Monaco Grand Prix history |

---

## ⚙️ Engine Components

| Component | Implementation |
|-----------|----------------|
| **Tokenization** | `re.findall(r"[a-z0-9]+")` + lowercase |
| **Stop words** | Custom 60-word set |
| **Stemming** | Rule-based suffix stripping (no NLTK) |
| **Inverted Index** | `dict[term → dict[doc_id → frequency]]` |
| **BM25** | k1=1.5, b=0.75 — standard parameters |
| **Autocomplete** | Trie with frequency-sorted suggestions |

---

## 🖼 Screenshots

<img width="1412" height="755" alt="Captura de pantalla 2026-03-23 a la(s) 11 39 41 p m" src="https://github.com/user-attachments/assets/71a23da7-ab0d-412c-8710-93a6830ad50d" /><img width="1433" height="786" alt="Captura de pantalla 2026-03-23 a la(s) 11 39 52 p m" src="https://github.com/user-attachments/assets/abfed92d-efdf-453a-81cb-c730d2383087" />

---

## 📚 Corpus Sources

- UEFA.com, FIFA.com, NBA.com (official bodies)
- BBC Sport, ESPN, Sky Sports (mainstream sports media)
- Formula1.com, Autosport (F1 specialized)
- The Athletic, Sports Illustrated (in-depth analysis)

All 25 documents are real, each 80-180 words, covering events from 2015–2024.
