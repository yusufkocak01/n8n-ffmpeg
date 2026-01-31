import os
import uuid
import subprocess
from flask import Flask, request, jsonify
import boto3

app = Flask(__name__)

# -----------------------------
# R2 client'ı istekte oluştur
# -----------------------------
def get_s3():
    R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
    R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
    R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")

    endpoint = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    )

# -----------------------------
# R2 Upload (Instagram uyumlu)
# -----------------------------
def upload_to_r2(file_path, key):
    s3 = get_s3()
    R2_BUCKET = os.environ.get("R2_BUCKET")
    R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL")

    with open(file_path, "rb") as f:
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=f"videos/{key}",
            Body=f,
            ContentType="video/mp4",
        )

    return f"{R2_PUBLIC_URL}/videos/{key}"

# -----------------------------
# Upload Endpoint
# -----------------------------
@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "file yok"}), 400

    file = request.files['file']
    uid = str(uuid.uuid4())

    input_path = f"/tmp/{uid}_in.mp4"
    output_path = f"/tmp/{uid}.mp4"

    file.save(input_path)

    try:
        # Railway dostu hafif ffmpeg
        ffmpeg_cmd = [
            "ffmpeg","-y","-i",input_path,
            "-vf","scale=720:1280",
            "-c:v","libx264",
            "-pix_fmt","yuv420p",
            "-movflags","+faststart",
            "-preset","ultrafast",
            "-crf","28",
            "-c:a","aac",
            "-b:a","96k",
            output_path
        ]

        subprocess.run(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        video_url = upload_to_r2(output_path, f"{uid}.mp4")

        os.remove(input_path)
        os.remove(output_path)

        return jsonify({
            "status": "ok",
            "url": video_url
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -----------------------------
# Health check (test için)
# -----------------------------
@app.route("/", methods=["GET"])
def health():
    return "OK", 200
 
