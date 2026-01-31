import os
import uuid
from flask import Flask, request, jsonify
import boto3
import subprocess

app = Flask(__name__)

R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_BUCKET = os.environ.get("R2_BUCKET")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL")  # pub-xxxx.r2.dev

R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

s3 = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY
)

def upload_to_r2(file_path, key):
    with open(file_path, "rb") as f:
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=f"videos/{key}",
            Body=f,
            ContentType="video/mp4",
            ACL="public-read"
        )
    return f"{R2_PUBLIC_URL}/videos/{key}"

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "file yok"}), 400

    file = request.files['file']
    uid = str(uuid.uuid4())

    input_path = f"/tmp/{uid}_in.mp4"
    output_path = f"/tmp/{ui_
