import os
import subprocess
import requests
from flask import Flask, request, jsonify
import boto3
import time

app = Flask(__name__)

# R2 ayarları (Railway Environment Variables üzerinden gelir)
R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
R2_ACCESS_KEY = os.environ["R2_ACCESS_KEY"]
R2_SECRET_KEY = os.environ["R2_SECRET_KEY"]
R2_BUCKET = os.environ["R2_BUCKET"]

# Senin paylaştığın sabit logo linkin
LOGO_URL = "https://pub-c84f81986b7843689e2e84205fb8f64c.r2.dev/adana-kanali.png"

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

    # 2️⃣ FFmpeg işlemi: Boyutlandırma ve Orta-Alt Logo Overlay
    # [0:v] ana video, [1:v] logoyu temsil eder. 
    # (W-w)/2 yatayda ortalar, H-h-40 dikeyde alttan 40px boşluk bırakır.
    try:
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i", input_path,
            "-i", LOGO_URL,
            "-filter_complex", "[0:v]scale=1280:-2[v];[v][1:v]overlay=(W-w)/2:H-h-40",
            "-movflags", "+faststart",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            output_path
        ], check=True)
    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    # 3️⃣ R2’ye yükle (Dosya adını her seferinde benzersiz yapıyoruz ki Instagram eski videoyu göstermesin)
    filename = f"video-{int(time.time())}.mp4"
    s3.upload_file(
        output_path,
        R2_BUCKET,
        filename,
        ExtraArgs={"ContentType": "video/mp4"}
    )

    # Senin Public R2 adresin
    public_url = f"https://pub-c84f81986b7843689e2e84205fb8f64c.r2.dev/{filename}"

    return jsonify({
        "status": "ok",
        "video_url": public_url
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
