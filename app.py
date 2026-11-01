
from flask import Flask, request, jsonify, render_template
from services.source_fetcher import fetch_sources
from services.ai_analyzer import analyze_sources

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/investigate')
def investigate_page():
    return render_template('investigate.html')


@app.route('/hub')
def intelligence_hub():
    return render_template('hub.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/api/health')
def health():
    return jsonify({
        'status': 'online',
        'project': 'Golden Spy',
        'engine': 'Local Intelligence Engine',
        'api_required': False
    })


@app.route('/api/investigate', methods=['POST'])
def investigate():
    data = request.get_json(silent=True) or {}

    question = data.get('question', '').strip()
    urls = data.get('urls', [])

    if not question:
        return jsonify({
            'success': False,
            'error': 'Research question is required.'
        }), 400

    if not isinstance(urls, list):
        return jsonify({
            'success': False,
            'error': 'URLs must be a list.'
        }), 400

    urls = [
        url.strip() for url in urls
        if isinstance(url, str) and url.strip()
    ]

    if not urls:
        return jsonify({
            'success': False,
            'error': 'Add at least one source URL.'
        }), 400

    if len(urls) > 8:
        return jsonify({
            'success': False,
            'error': 'Maximum 8 URLs allowed.'
        }), 400

    if any(not url.startswith(('https://', 'http://')) for url in urls):
        return jsonify({
            'success': False,
            'error': 'Only HTTP and HTTPS URLs are allowed.'
        }), 400

    sources = fetch_sources(urls)

    if not any(s.get('status') == 'success' for s in sources):
        return jsonify({
            'success': False,
            'error': 'Unable to access the supplied sources.',
            'sources': sources
        }), 400

    try:
        analysis = analyze_sources(question, sources)
    except ValueError as error:
        return jsonify({
            'success': False,
            'error': str(error)
        }), 400

    return jsonify({
        'success': True,
        'question': question,
        'sources': sources,
        'analysis': analysis,
        'analysis_mode': 'Local Rule-Based Intelligence',
        'disclaimer': 'Findings are potential signals. Verify claims using original sources.'
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
