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
R2_PUBLIC_URL = os.environ.get("R2_PUBLIC_URL")

 def get_s3():
    R2_ACCOUNT_ID = os.environ.get("R2_ACCOUNT_ID")
    R2_BUCKET = os.environ.get("R2_BUCKET")
    R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY")
    R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY")

    endpoint = f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY
    )

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
        )
    return f"{R2_PUBLIC_URL}/videos/{key}"

@app.route("/upload", methods=["POST"])
def upload():
    if 'file' not in request.files:
        return jsonify({"error": "file yok"}), 400

    file = request.files['file']
    uid = str(uuid.uuid4())

    input_path = f"/tmp/{uid}_in.mp4"
    output_path = f"/tmp/{uid}.mp4"

    file.save(input_path)

    ffmpeg_cmd = [
        "ffmpeg","-y","-i",input_path,
        "-vf","scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v","libx264",
        "-profile:v","high",
        "-level","4.2",
        "-pix_fmt","yuv420p",
        "-movflags","+faststart",
        "-preset","veryfast",
        "-crf","23",
        "-c:a","aac",
        "-b:a","128k",
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
