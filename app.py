import os
import uuid
from flask import Flask, request, jsonify
import boto3
import subprocess

app = Flask(__name__)

# ----------------------
# Cloudflare R2 Ayarları
# ----------------------
R2_ENDPOINT = os.environ.get("R2_ENDPOINT")         # Örn: https://<account-id>.r2.cloudflarestorage.com
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET")             # Örn: mybucket

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
    r2_key = f"videos/{key_name}"
    s3_client.upload_file(file_path, R2_BUCKET, r2_key)
    return f"https://{R2_BUCKET}.{R2_ENDPOINT.replace('https://','')}/{r2_key}"

# ----------------------
# Flask Endpoint
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
        # 1️⃣ Opsiyonel: FFmpeg video dönüştürme (Instagram, boyut vs.)
        # ----------------------
        video_cmd = [
            "ffmpeg", "-y", "-i", input_file,
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", output_video
        ]
        
        # 2️⃣ Opsiyonel: Ses ayırma
        audio_cmd = ["ffmpeg", "-y", "-i", input_file, "-vn", "-acodec", "libmp3lame", output_audio]

        # Küçük test videoları ile çalıştır
        subprocess.run(video_cmd, check=True)
        subprocess.run(audio_cmd, check=True)

        # ----------------------
        # 3️⃣ R2 Upload (/videos klasörü)
        # ----------------------
        video_url = upload_to_r2(output_video, f"{uid}.mp4")
        audio_url = upload_to_r2(output_audio, f"{uid}.mp3")  # Opsiyonel

        # ----------------------
        # 4️⃣ Geçici dosyaları temizle
        # ----------------------
        for f in [input_file, output_video, output_audio]:
            if os.path.exists(f):
                os.remove(f)

        # ----------------------
        # 5️⃣ JSON Response
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
# Flask production-ready run (Gunicorn için)
# ----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
