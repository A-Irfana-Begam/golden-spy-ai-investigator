
from flask import Flask, render_template, request, jsonify

from services.source_fetcher import fetch_sources, discover_sources
from services.ai_analyzer import analyze_sources


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/investigate")
def investigate_page():
    return render_template("investigate.html")


@app.route("/hub")
def intelligence_hub():
    return render_template("hub.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/api/health")
def health():
    return jsonify({
        "status": "online",
        "project": "Golden Spy",
        "engine": "Local Rule-Based Intelligence Engine",
        "api_required": False
    })


@app.route("/api/investigate", methods=["POST"])
def investigate():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "success": False,
            "error": "Invalid request."
        }), 400

    question = data.get("question", "")
    urls = data.get("urls", [])

    if not isinstance(question, str) or not question.strip():
        return jsonify({
            "success": False,
            "error": "Enter a research question."
        }), 400

    question = question.strip()

    if len(question) > 1000:
        return jsonify({
            "success": False,
            "error": "Question must not exceed 1000 characters."
        }), 400

    if not isinstance(urls, list):
        return jsonify({
            "success": False,
            "error": "URLs must be provided as a list."
        }), 400

    if len(urls) > 8:
        return jsonify({
            "success": False,
            "error": "Maximum 8 URLs are allowed."
        }), 400

    urls = [
        url.strip()
        for url in urls
        if isinstance(url, str) and url.strip()
    ]

    if any(
        not url.startswith(("https://", "http://"))
        for url in urls
    ):
        return jsonify({
            "success": False,
            "error": "Only HTTP and HTTPS URLs are allowed."
        }), 400

    try:
        discovered_urls = []

        if len(urls) < 8:
            discovered_urls = discover_sources(
                question,
                limit=8 - len(urls)
            ) or []

        combined_urls = list(dict.fromkeys(
            urls + discovered_urls
        ))[:8]

        if not combined_urls:
            return jsonify({
                "success": False,
                "error": (
                    "No sources found. Add webpage URLs and try again."
                )
            }), 400

        sources = fetch_sources(combined_urls)

        usable_sources = [
            source for source in sources
            if source.get("status") == "success"
            and isinstance(source.get("text"), str)
            and source.get("text").strip()
        ]

        if not usable_sources:
            return jsonify({
                "success": False,
                "error": "No readable sources found.",
                "sources": sources
            }), 400

        analysis = analyze_sources(question, usable_sources)

        return jsonify({
            "success": True,
            "question": question,
            "sources": sources,
            "analysis": analysis,
            "analysis_mode": "Local Rule-Based Evidence Analysis",
            "disclaimer": (
                "This tool uses keyword-based analysis, not AI. "
                "Findings are preliminary signals. Verify claims "
                "using original sources."
            )
        })

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception:
        app.logger.exception("Investigation failed")

        return jsonify({
            "success": False,
            "error": "Investigation failed. Please try again."
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
