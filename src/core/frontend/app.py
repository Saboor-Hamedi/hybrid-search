# Flask frontend to interact with FastAPI backend
import requests
from flask import Flask, render_template, request

app = Flask(__name__,template_folder='templates')

API_URL = "http://127.0.0.1:8000"  # your FastAPI backend

@app.route("/", methods=["GET", "POST"])
def home():
    results = []
    query = ""
    use_hybrid = True
    total = 0
    stats = {}
    if request.method == "POST":
        query = request.form.get("query", "").strip()
        # use_hybrid = bool(request.form.get("use_hybrid"))
        use_hybrid = request.form.get("use_hybrid") == 'true'
        payload = {
            "query": query,
            "page": 1,
            "page_size": 100,
            "use_hybrid": use_hybrid
        }
        try:
            r = requests.post(f"{API_URL}/search", json=payload)
            r.raise_for_status()
            data = r.json()
            results = data.get("results", [])
            stats = data.get("stats", {})
            total = len(results)
        except requests.exceptions.RequestException as e:
            error_message = f"⚠️ Backend Request Error: {e}"
            results = []
            stats = {}
            total = 0
            print(error_message)
    else:
        total = 0

    return render_template("index.html", results=results, query=query, use_hybrid=use_hybrid, total=total, stats=stats)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True,reload=True)

