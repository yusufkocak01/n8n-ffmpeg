import os
import uuid
from flask import Flask, request, jsonify
import boto3

app = Flask(__name__)

# -----------------------------
# R2 Client
# -----------------------------
def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ.get('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ.get("R2_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("R2_SECRET_KEY"),
    )

# -----------------------------
# Health Check
# -----------------------------
@app.route("/", methods=["GET"])
def health():
    return "OK", 200

# -----------------------------
# Upload Endpoint (Doğru yöntem)
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "file yok"}), 400

    file = request.files['file']
    uid = str(uuid.uuid4())

    # Dosyayı önce diske yaz (kritik)
    temp_path = f"/tmp/{uid}.mp4"
    file.save(temp_path)

    try:
        s3 = get_s3()
        key = f"videos/{uid}.mp4"

        # Dosyadan yükle (stream değil)
        s3.upload_file(
            temp_path,
            os.environ.get("R2_BUCKET"),
            key,
            ExtraArgs={"ContentType": "video/mp4"}
        )

        os.remove(temp_path)

        url = f"{os.environ.get('R2_PUBLIC_URL')}/{key}"

        return jsonify({
            "status": "ok",
            "url": url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
