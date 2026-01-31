import os
import uuid
from flask import Flask, request, jsonify
import boto3
import subprocess

app = Flask(__name__)

# ----------------------
# Cloudflare R2 Ayarları (Railway env değişkenleri ile uyumlu)
# ----------------------
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_BUCKET = os.environ.get("R2_BUCKET")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")

# Endpoint URL Cloudflare R2 formatında
R2_ENDPOINT = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

# boto3 S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY
)

def upload_to_r2(file_path, key_name):
    """
    Cloudflare R2 /videos klasörüne yükleme
    """
    r2_key = key_name  # videos/videos gibi çift path olmaması için sadece dosya adı
    try:
        s3_client.upload_file(file_path, R2_BUCKET, r2_key)
    except Exception as e:
        raise Exception(f"Failed to upload {file_path} to {R2_BUCKET}/{r2_key}: {str(e)}")
    return f"https://{R2_BUCKET}.{R2_ACCOUNT_ID}.r2.cloudflarestorage.com/{r2_key}"

# ----------------------
# Minimal test endpoint
# ----------------------
@app.route("/test", methods=["POST"])
def test():
    return jsonify({"status": "ok"})

# ----------------------
# Ana video işleme endpoint
# ----------------------
@app.route("/process", methods=["POST"])
def process():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Dosya yok"}), 400

    video_file = request.files['file']
    uid = str(uuid.uuid4())
    input_file = f"/tmp/{uid}_in.mp4"
    output_video = f"/tmp/{uid}_out.mp4"
    output_audio = f"/tmp/{uid}_out.mp3"  # Opsiyonel: ses dosyası

    # ----------------------
    # Dosyayı kaydet
    # ----------------------
    video_file.save(input_file)

    try:
        # ----------------------
        # Opsiyonel: FFmpeg video dönüştürme (Instagram formatı)
        # ----------------------
        video_cmd = [
            "ffmpeg", "-y", "-i", input_file,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", output_video
        ]
        
        # Opsiyonel: Ses ayırma
        audio_cmd = ["ffmpeg", "-y", "-i", input_file, "-vn", "-acodec", "libmp3lame", output_audio]

        # FFmpeg işlemleri
        subprocess.run(video_cmd, check=True)
        subprocess.run(audio_cmd, check=True)

        # ----------------------
        # R2 Upload
        # ----------------------
        video_url = upload_to_r2(output_video, f"{uid}.mp4")
        audio_url = upload_to_r2(output_audio, f"{uid}.mp3")  # Opsiyonel

        # ----------------------
        # Geçici dosyaları temizle
        # ----------------------
        for f in [input_file, output_video, output_audio]:
            if os.path.exists(f):
                os.remove(f)

        # ----------------------
        # JSON Response
        # ----------------------
        return jsonify({
            "status": "ok",
            "video_url": video_url,
            "audio_url": audio_url
        })

    except subprocess.CalledProcessError as e:
        return jsonify({"status": "error", "message": f"FFmpeg hatası: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# ----------------------
# Flask production-ready run (lokal test için)
# ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
