from flask import Flask, jsonify, request
from flask_cors import CORS
from detector import analyze_url

app = Flask(__name__)
CORS(app)


@app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Flask backend is running!"})


@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    url = data.get('url', '').strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    if not url.startswith("http"):
        url = "https://" + url

    result = analyze_url(url)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
