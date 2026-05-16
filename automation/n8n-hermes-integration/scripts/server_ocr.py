#!/usr/bin/env python3
"""ddddocr Flask API Server - 验证码识别服务

用法:
    ~/.hermes/venv-ocr/bin/python server_ocr.py

或直接:
    python3 -c "
    from flask import Flask, request, jsonify; import ddddocr, base64, io
    from PIL import Image
    app = Flask(__name__)
    ocr = ddddocr.DdddOcr(show_ad=False)
    @app.route('/ocr', methods=['POST'])
    def solve():
        data = request.get_json()
        img_data = base64.b64decode(data['base64'])
        img = Image.open(io.BytesIO(img_data))
        return jsonify({'result': ocr.classification(img)})
    app.run(host='0.0.0.0', port=9898)
    "
"""

from flask import Flask, request, jsonify
import ddddocr
import base64
import io
from PIL import Image

app = Flask(__name__)
ocr = ddddocr.DdddOcr(show_ad=False)


@app.route("/ocr", methods=["POST"])
def solve():
    data = request.get_json()
    if "base64" not in data:
        return jsonify({"error": "send {'base64': '...'}"}) , 400
    img_data = base64.b64decode(data["base64"])
    img = Image.open(io.BytesIO(img_data))
    res = ocr.classification(img)
    return jsonify({"result": res})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9898)
