import os
import subprocess
from flask import Flask, request, jsonify
import boto3

app = Flask(__name__)

# Değişkenleri Railway Variables'tan çekiyoruz
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

@app.route('/process', methods=['POST'])
def process_video():
    if 'video' not in request.files:
        return "Video bulunamadı", 400
    
    video_file = request.files['video']
    filename = request.form.get("filename", "input_video.mp4")
    input_path = f"/tmp/{filename}"
    output_path = f"/tmp/processed_{filename}"
    
    video_file.save(input_path)

    # FFmpeg işlemi (Örnek: Instagram uyumlu hale getirme)
    try:
        subprocess.run([
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264', '-crf', '23', '-preset', 'veryfast',
            '-c:a', 'aac', '-b:a', '128k',
            '-y', output_path
        ], check=True)
        
        # R2'ye Yükle
        s3.upload_file(output_path, R2_BUCKET, filename, ExtraArgs={'ContentType': 'video/mp4'})
        
        # Geçici dosyaları sil
        os.remove(input_path)
        os.remove(output_path)
        
        # R2 Linkini geri döndür
        public_url = f"https://pub-c84f81986b7843689e2e84205fb8f64c.r2.dev/{filename}"
        return jsonify({"status": "success", "url": public_url})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
