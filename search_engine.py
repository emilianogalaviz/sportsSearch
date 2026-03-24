"""
Sports Search Engine
Text processing, inverted index, BM25 scoring, and autocomplete.
Enhancement C: Autocomplete with trie-based term suggestions.
"""

import json
import math
import re
import time
from collections import defaultdict


# --------------------------------------------------------------------------- #
#  Stop words
# --------------------------------------------------------------------------- #
STOP_WORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "was", "are", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "shall", "can", "not", "no", "nor",
    "as", "if", "then", "than", "so", "yet", "both", "either", "each",
    "this", "that", "these", "those", "it", "its", "their", "they", "them",
    "he", "she", "his", "her", "we", "our", "you", "your", "who", "which",
    "what", "when", "where", "how", "all", "any", "one", "two", "also",
    "after", "before", "during", "over", "under", "more", "most", "such",
}

# --------------------------------------------------------------------------- #
#  Simple Porter-like suffix stemmer (no external libs required)
# --------------------------------------------------------------------------- #

_SUFFIXES = [
    ("ational", "ate"), ("tional", "tion"), ("enci", "ence"),
    ("anci", "ance"), ("izer", "ize"), ("ising", "ize"), ("izing", "ize"),
    ("ising", "ize"), ("ational", "ate"), ("ational", "ate"),
    ("alism", "al"), ("aliti", "al"), ("alli", "al"), ("fulness", "ful"),
    ("ousness", "ous"), ("ousli", "ous"), ("iveness", "ive"), ("iviti", "ive"),
    ("biliti", "ble"), ("nesses", ""), ("ments", ""), ("ment", ""),
    ("ings", ""), ("ing", ""), ("edly", ""), ("edly", ""), ("edly", ""),
    ("ness", ""), ("ated", ""), ("ates", ""), ("ers", ""), ("est", ""),
    ("ies", "y"), ("ied", "y"), ("ive", ""), ("ize", ""), ("ise", ""),
    ("ous", ""), ("ful", ""), ("ism", ""), ("ion", ""), ("al", ""),
    ("er", ""), ("ly", ""), ("ed", ""), ("es", ""), ("s", ""),
]


def stem(word: str) -> str:
    """Very lightweight rule-based stemmer."""
    if len(word) <= 3:
        return word
    for suffix, replacement in _SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: len(word) - len(suffix)] + replacement
    return word


# --------------------------------------------------------------------------- #
#  Text processing
# --------------------------------------------------------------------------- #

def tokenize(text: str) -> list[str]:
    """Lowercase, remove punctuation, tokenize, remove stop words, stem."""
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text)
    return [stem(t) for t in tokens if t not in STOP_WORDS and len(t) > 1]


# --------------------------------------------------------------------------- #
#  Trie for autocomplete (Enhancement C)
# --------------------------------------------------------------------------- #

class TrieNode:
    __slots__ = ("children", "is_end", "frequency")

    def __init__(self):
        self.children: dict[str, "TrieNode"] = {}
        self.is_end: bool = False
        self.frequency: int = 0


class Trie:
    """Prefix trie built from the raw (unstemmed) vocabulary."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, frequency: int = 1):
        node = self.root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
        node.is_end = True
        node.frequency += frequency

    def _collect(self, node: TrieNode, prefix: str, results: list):
        if node.is_end:
            results.append((prefix, node.frequency))
        for ch, child in node.children.items():
            self._collect(child, prefix + ch, results)

    def suggest(self, prefix: str, max_results: int = 8) -> list[str]:
        """Return up to max_results suggestions sorted by frequency."""
        node = self.root
        for ch in prefix.lower():
            if ch not in node.children:
                return []
            node = node.children[ch]
        results: list[tuple[str, int]] = []
        self._collect(node, prefix.lower(), results)
        results.sort(key=lambda x: -x[1])
        return [w for w, _ in results[:max_results]]


# --------------------------------------------------------------------------- #
#  Inverted Index
# --------------------------------------------------------------------------- #

class InvertedIndex:
    def __init__(self):
        # {term: {doc_id: frequency}}
        self.index: dict[str, dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self.doc_lengths: dict[int, int] = {}          # total tokens per doc
        self.doc_metadata: dict[int, dict] = {}         # title, source, text, category
        self.total_docs: int = 0
        self.avg_doc_length: float = 0.0

    def build(self, corpus: list[dict]):
        self.total_docs = len(corpus)
        total_tokens = 0

        for doc in corpus:
            doc_id = doc["id"]
            full_text = f"{doc['title']} {doc['text']}"
            tokens = tokenize(full_text)

            self.doc_metadata[doc_id] = {
                "title": doc["title"],
                "source": doc["source"],
                "text": doc["text"],
                "category": doc.get("category", "general"),
            }
            self.doc_lengths[doc_id] = len(tokens)
            total_tokens += len(tokens)

            for token in tokens:
                self.index[token][doc_id] += 1

        self.avg_doc_length = total_tokens / self.total_docs if self.total_docs else 1.0

    @property
    def vocabulary_size(self) -> int:
        return len(self.index)


# --------------------------------------------------------------------------- #
#  BM25 Scoring
# --------------------------------------------------------------------------- #

class BM25:
    def __init__(self, index: InvertedIndex, k1: float = 1.5, b: float = 0.75):
        self.index = index
        self.k1 = k1
        self.b = b

    def idf(self, term: str) -> float:
        """Inverse Document Frequency."""
        df = len(self.index.index.get(term, {}))
        if df == 0:
            return 0.0
        n = self.index.total_docs
        return math.log((n - df + 0.5) / (df + 0.5) + 1)

    def score(self, query_terms: list[str], doc_id: int) -> float:
        """BM25 score for a document given query terms."""
        score = 0.0
        doc_len = self.index.doc_lengths.get(doc_id, 0)
        avdl = self.index.avg_doc_length

        for term in query_terms:
            posting = self.index.index.get(term, {})
            tf = posting.get(doc_id, 0)
            if tf == 0:
                continue
            idf = self.idf(term)
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / avdl)
            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        """Return ranked results for a query."""
        start = time.time()
        query_terms = tokenize(query)

        if not query_terms:
            return []

        # Candidate docs: union of posting lists
        candidate_ids: set[int] = set()
        for term in query_terms:
            candidate_ids |= set(self.index.index.get(term, {}).keys())

        # Score candidates
        scored = []
        for doc_id in candidate_ids:
            s = self.score(query_terms, doc_id)
            if s > 0:
                scored.append((doc_id, s))

        scored.sort(key=lambda x: -x[1])
        elapsed = time.time() - start

        results = []
        for doc_id, s in scored[:top_k]:
            meta = self.index.doc_metadata[doc_id]
            results.append({
                "id": doc_id,
                "title": meta["title"],
                "source": meta["source"],
                "text": meta["text"],
                "category": meta["category"],
                "score": round(s, 4),
                "search_time": round(elapsed * 1000, 2),  # ms
            })

        return results


# --------------------------------------------------------------------------- #
#  Search Engine (facade)
# --------------------------------------------------------------------------- #

class SportsSearchEngine:
    def __init__(self, corpus_path: str = "corpus.json"):
        with open(corpus_path, encoding="utf-8") as f:
            corpus = json.load(f)

        self.index = InvertedIndex()
        self.index.build(corpus)

        self.bm25 = BM25(self.index)

        # Build trie from raw words (not stemmed) for autocomplete
        self.trie = Trie()
        self._build_trie(corpus)

    def _build_trie(self, corpus: list[dict]):
        word_freq: dict[str, int] = defaultdict(int)
        for doc in corpus:
            raw_text = f"{doc['title']} {doc['text']}".lower()
            words = re.findall(r"[a-z]+", raw_text)
            for w in words:
                if w not in STOP_WORDS and len(w) > 2:
                    word_freq[w] += 1

        for word, freq in word_freq.items():
            self.trie.insert(word, freq)

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        return self.bm25.search(query, top_k)

    def autocomplete(self, prefix: str, max_results: int = 8) -> list[str]:
        if not prefix or len(prefix) < 2:
            return []
        return self.trie.suggest(prefix.strip(), max_results)

    @property
    def stats(self) -> dict:
        return {
            "total_docs": self.index.total_docs,
            "vocabulary_size": self.index.vocabulary_size,
            "avg_doc_length": round(self.index.avg_doc_length, 1),
        }


# --------------------------------------------------------------------------- #
#  Quick CLI test
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    engine = SportsSearchEngine("corpus.json")
    print(f"Stats: {engine.stats}")
    print("\nSearch: 'Messi World Cup'")
    for r in engine.search("Messi World Cup", top_k=3):
        print(f"  [{r['score']}] {r['title']}")
    print("\nAutocomplete: 'cham'")
    print(" ", engine.autocomplete("cham"))
