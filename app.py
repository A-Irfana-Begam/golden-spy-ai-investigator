
from flask import Flask, render_template, request, jsonify

from services.source_fetcher import fetch_sources, discover_sources
from services.ai_analyzer import analyze_sources


app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/investigate")
def investigate():
    return render_template("investigate.html")


@app.route("/hub")
def hub():
    return render_template("hub.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/investigate", methods=["POST"])
def run_investigation():
    try:
        data = request.get_json(silent=True)

        if not isinstance(data, dict):
            return jsonify({
                "success": False,
                "error": "Invalid request. Please try again."
            }), 400

        question = data.get("question", "")
        user_urls = data.get("urls", [])

        if not isinstance(question, str) or not question.strip():
            return jsonify({
                "success": False,
                "error": "Enter a research question."
            }), 400

        question = question.strip()

        if len(question) > 1000:
            return jsonify({
                "success": False,
                "error": "Research question is too long. Maximum 1000 characters."
            }), 400

        if not isinstance(user_urls, list):
            return jsonify({
                "success": False,
                "error": "URLs must be provided as a list."
            }), 400

        user_urls = [
            url.strip()
            for url in user_urls
            if isinstance(url, str) and url.strip()
        ]

        if len(user_urls) > 8:
            return jsonify({
                "success": False,
                "error": "Maximum 8 URLs are allowed."
            }), 400

        discovered_urls = []

        if len(user_urls) < 8:
            try:
                discovered_urls = discover_sources(
                    question,
                    limit=8 - len(user_urls)
                ) or []
            except Exception:
                app.logger.warning(
                    "Automatic source discovery failed.",
                    exc_info=True
                )

        combined_urls = list(dict.fromkeys(
            user_urls + discovered_urls
        ))[:8]

        if not combined_urls:
            return jsonify({
                "success": False,
                "error": "No sources found. Try again or provide webpage URLs."
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
                "error": "No readable sources found. Try different URLs.",
                "sources": sources
            }), 400

        analysis = analyze_sources(question, usable_sources)

        return jsonify({
            "success": True,
            "question": question,
            "sources": sources,
            "analysis": analysis,
            "analysis_mode": (
                "Gemini AI + Automatic Source Discovery + Evidence Analysis"
                if discovered_urls
                else "Gemini AI + Evidence Analysis"
            ),
            "disclaimer": (
                "AI-generated findings require manual verification. "
                "Check original sources before relying on claims."
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
            "error": (
                "Investigation could not be completed. "
                "Please try again later."
            )
        }), 500


if __name__ == "__main__":
    app.run(debug=False)
