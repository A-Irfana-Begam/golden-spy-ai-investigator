
from flask import Flask, render_template, request, jsonify
from urllib.parse import urlparse

from services.source_fetcher import fetch_sources
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
    return jsonify({
        "success": True,
        "status": "Golden Spy is running",
        "ai_engine": "Gemini AI"
    })


@app.route("/api/investigate", methods=["POST"])
def run_investigation():
    try:
        data = request.get_json(silent=True) or {}

        question = data.get("question", "")
        urls = data.get("urls", [])

        if not isinstance(question, str) or not question.strip():
            return jsonify({
                "success": False,
                "error": "Please enter a research question."
            }), 400

        question = question.strip()

        if len(question) > 1000:
            return jsonify({
                "success": False,
                "error": "Question is too long. Maximum 1000 characters."
            }), 400

        if not isinstance(urls, list) or not urls:
            return jsonify({
                "success": False,
                "error": "Please provide at least one source URL."
            }), 400

        if len(urls) > 8:
            return jsonify({
                "success": False,
                "error": "Maximum 8 source URLs are allowed."
            }), 400

        valid_urls = []

        for url in urls:
            if not isinstance(url, str):
                return jsonify({
                    "success": False,
                    "error": "Invalid URL format."
                }), 400

            url = url.strip()
            parsed = urlparse(url)

            if (
                parsed.scheme not in ("http", "https")
                or not parsed.hostname
            ):
                return jsonify({
                    "success": False,
                    "error": f"Invalid URL: {url}"
                }), 400

            valid_urls.append(url)

        sources = fetch_sources(valid_urls)

        if not any(
            source.get("status") == "success"
            and source.get("text", "").strip()
            for source in sources
        ):
            return jsonify({
                "success": False,
                "error": "Unable to read the provided sources. Try different URLs.",
                "sources": sources
            }), 400

        analysis = analyze_sources(question, sources)

        return jsonify({
            "success": True,
            "question": question,
            "sources": sources,
            "analysis": analysis,
            "analysis_mode": "Gemini AI + Source Evidence Analysis",
            "disclaimer": (
                "AI-generated findings require manual verification. "
                "Always check the original sources before relying on claims."
            )
        })

    except ValueError as error:
        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

    except Exception as error:
        app.logger.exception("Investigation failed")

        return jsonify({
            "success": False,
            "error": "Investigation failed. Please try again later."
        }), 500


if __name__ == "__main__":
    app.run(debug=False)
