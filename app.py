import os, subprocess, requests, boto3
from flask import Flask, request, jsonify

app = Flask(__name__)

R2_ACCOUNT_ID = os.environ["R2_ACCOUNT_ID"]
R2_ACCESS_KEY = os.environ["R2_ACCESS_KEY"]
R2_SECRET_KEY = os.environ["R2_SECRET_KEY"]
R2_BUCKET = os.environ["R2_BUCKET"]

s3 = boto3.client("s3", endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                  aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY)

@app.route("/process", methods=["POST"])
def process_video():
    video_url = request.json["video_url"]
    input_p, output_p = "/tmp/input.mp4", "/tmp/output.mp4"

    # Videoyu indir
    r = requests.get(video_url, stream=True)
    with open(input_p, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192): f.write(chunk)

    # FFmpeg işlemi (LOGO İPTAL - SADECE SIKIŞTIRMA)
    subprocess.run(["ffmpeg", "-y", "-i", input_p, "-movflags", "+faststart", 
                    "-vf", "scale=1280:-2", "-c:v", "libx264", "-preset", "fast", 
                    "-crf", "23", "-c:a", "aac", output_p], check=True)

    # R2’ye yükle
    s3.upload_file(output_p, R2_BUCKET, "processed-video.mp4", ExtraArgs={"ContentType": "video/mp4"})
    
    return jsonify({"status": "ok", "video_url": f"https://pub-c84f81986b7843689e2e84205fb8f64c.r2.dev/processed-video.mp4"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
