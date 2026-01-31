from flask import Flask, request, jsonify
import subprocess
import requests
import uuid
import os

app = Flask(__name__)

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

    # Instagram uyumlu ffmpeg
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", "scale=1080:1920",
        "-r", "30",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        output_file
    ]

    subprocess.run(cmd, check=True)

    return jsonify({
        "status": "ok",
        "file_path": output_file
    })

app.run(host="0.0.0.0", port=8080)
