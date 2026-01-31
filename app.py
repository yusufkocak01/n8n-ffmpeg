from flask import Flask, request, jsonify
import subprocess
import requests
import uuid
import os
import boto3

app = Flask(__name__)

# R2 ayarları
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET")

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)

def upload_to_r2(file_path, filename):
    s3.upload_file(
        file_path,
        R2_BUCKET,
        filename,
        ExtraArgs={
            "ContentType": "video/mp4"
        }
    )

@app.route("/process", methods=["POST"])
def process():
    data = request.json
    video_url = data["video_url"]

    uid = str(uuid.uuid4())
    input_file = f"/tmp/{uid}_in.mp4"
    output_file = f"/tmp/{uid}_out.mp4"

    r = requests.get(video_url)
    with open(input_file, "wb") as f:
        f.write(r.content)

    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", "scale=1080:1920",
        "-r", "30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_file
    ]

    subprocess.run(cmd, check=True)

    filename = f"{uid}.mp4"
    upload_to_r2(output_file, filename)

    public_url = f"https://pub-{R2_ACCOUNT_ID}.r2.dev/{filename}"

    return jsonify({
        "status": "ok",
        "url": public_url
    })

app.run(host="0.0.0.0", port=8080)
