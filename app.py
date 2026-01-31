from flask import Flask, request, jsonify
import subprocess
import uuid
import os
import boto3

app = Flask(__name__)

# Railway Variables kısmına girdiğin R2 bilgileri
R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")
R2_BUCKET = os.environ.get("R2_BUCKET")

# Cloudflare R2 Bağlantısı
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
        ExtraArgs={"ContentType": "video/mp4"}
    )

@app.route("/process", methods=["POST"])
def process():
    # Make'ten gelen 'file' alanını kontrol et
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Dosya bulunamadı (file missing)"}), 400

    video_file = request.files['file'] # İşte aradığın kısım burası
    
    uid = str(uuid.uuid4())
    input_file = f"/tmp/{uid}_in.mp4"
    output_file = f"/tmp/{uid}_out.mp4"

    # Dosyayı sunucuya geçici olarak kaydet
    video_file.save(input_file)

    # Instagram Reels uyumlu FFmpeg komutu
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_file
    ]

    try:
        subprocess.run(cmd, check=True)
        
        # İşlenen videoyu R2'ye yükle
        filename = f"{uid}.mp4"
        upload_to_r2(output_file, filename)

        # Temizlik: Geçici dosyaları sil
        if os.path.exists(input_file): os.remove(input_file)
        if os.path.exists(output_file): os.remove(output_file)

        public_url = f"https://pub-{R2_ACCOUNT_ID}.r2.dev/{filename}"
        
        return jsonify({
            "status": "ok",
            "public_url": public_url
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
