import os
import uuid
import requests
from flask import Flask, request, jsonify
import boto3

app = Flask(__name__)

def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ.get('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ.get("R2_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("R2_SECRET_KEY"),
    )

@app.route("/", methods=["GET"])
def health():
    return "OK", 200

@app.route("/upload-from-url", methods=["POST"])
def upload_from_url():
    data = request.json
    file_url = data.get("file_url")

    if not file_url:
        return jsonify({"error": "file_url yok"}), 400

    uid = str(uuid.uuid4())
    temp_path = f"/tmp/{uid}.mp4"

    # Videoyu Railway indiriyor
    r = requests.get(file_url, stream=True)
    with open(temp_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    s3 = get_s3()
    key = f"videos/{uid}.mp4"

    s3.upload_file(
        temp_path,
        os.environ.get("R2_BUCKET"),
        key,
        ExtraArgs={"ContentType": "video/mp4"}
    )

    os.remove(temp_path)

    url = f"{os.environ.get('R2_PUBLIC_URL')}/{key}"

    return jsonify({"status": "ok", "url": url})

