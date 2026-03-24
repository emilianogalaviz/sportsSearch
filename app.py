"""
app.py — Flask web server for the Sports Search Engine.
Routes:
  GET  /              → main search page
  GET  /search?q=...  → JSON search results
  GET  /autocomplete?q=... → JSON autocomplete suggestions
  GET  /stats         → JSON index statistics
"""

from flask import Flask, render_template, request, jsonify
from search_engine import SportsSearchEngine

app = Flask(__name__)
engine = SportsSearchEngine("corpus.json")


@app.route("/")
def index():
    return render_template("index.html", stats=engine.stats)


@app.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"results": [], "query": "", "search_time": 0})

    results = engine.search(query, top_k=10)
    search_time = results[0]["search_time"] if results else 0

    return jsonify({
        "query": query,
        "results": results,
        "count": len(results),
        "search_time": search_time,
    })


@app.route("/autocomplete")
def autocomplete():
    prefix = request.args.get("q", "").strip()
    suggestions = engine.autocomplete(prefix)
    return jsonify({"suggestions": suggestions})


@app.route("/stats")
def stats():
    return jsonify(engine.stats)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
