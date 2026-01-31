import os
import subprocess
import requests
from flask import Flask, request, jsonify
import boto3

app = Flask(__name__)

# R2 ayarları
R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
R2_ACCESS_KEY = os.environ["R2_ACCESS_KEY"]
R2_SECRET_KEY = os.environ["R2_SECRET_KEY"]
R2_BUCKET = os.environ["R2_BUCKET"]

s3 = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)

@app.route("/process", methods=["POST"])
def process_video():
    data = request.json
    video_url = data["video_url"]

    input_path = "/tmp/input.mp4"
    output_path = "/tmp/output.mp4"

    # 1️⃣ Videoyu indir
    r = requests.get(video_url, stream=True)
    with open(input_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    # 2️⃣ FFmpeg işlemi (Logosuz, Sadece Sıkıştırma)
    subprocess.run([
        "ffmpeg",
        "-y",
        "-i", input_path,
        "-movflags", "+faststart",
        "-vf", "scale=1280:-2",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        output_path
    ], check=True)

    # 3️⃣ R2’ye yükle
    filename = "processed-video.mp4"
    s3.upload_file(output_path, R2_BUCKET, filename, ExtraArgs={"ContentType": "video/mp4"})

    public_url = f"https://pub-c84f81986b7843689e2e84205fb8f64c.r2.dev/{filename}"

    return jsonify({"status": "ok", "video_url": public_url})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
