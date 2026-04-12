"""
SlimZero Flask Integration Example

Shows how to integrate SlimZero with a Flask web application.
"""

from flask import Flask, request, jsonify
from slimzero import SlimZero

app = Flask(__name__)

sz = SlimZero(
    model="gpt-4o",
    token_budget=512,
)

print("SlimZero Flask example started!")
print("POST to /compress with {'prompt': 'your prompt', 'system_prompt': 'optional'}")


@app.route("/compress", methods=["POST"])
def compress():
    """Compress a prompt using SlimZero."""
    data = request.get_json()

    if not data or "prompt" not in data:
        return jsonify({"error": "Missing 'prompt' field"}), 400

    prompt = data["prompt"]
    system_prompt = data.get("system_prompt")

    try:
        result = sz.call(prompt=prompt, system_prompt=system_prompt)

        return jsonify({
            "response": result.response,
            "original_tokens": result.original_input_tokens,
            "sent_tokens": result.sent_input_tokens,
            "savings_percent": result.input_token_savings_percent,
            "stages_applied": result.stages_applied,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/stats", methods=["GET"])
def stats():
    """Get cumulative SlimZero statistics."""
    return jsonify(sz.get_stats())


@app.route("/export", methods=["GET"])
def export():
    """Export statistics as JSON."""
    return sz.export_stats_json()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
