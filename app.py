"""
app.py — Веб-интерфейс для векторного поиска
"""

from flask import Flask, render_template, request
from vector_search import SearchEngine

app = Flask(__name__)
engine = SearchEngine()   # загружается один раз при старте


@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    query   = ""

    if request.method == "POST":
        query   = request.form.get("query", "").strip()
        if query:
            results = engine.search(query, top_n=10)

    return render_template("index.html", query=query, results=results)


if __name__ == "__main__":
    app.run(debug=True)
