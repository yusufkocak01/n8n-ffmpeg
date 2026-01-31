# ... (önceki importlar aynı kalacak)

@app.route("/process", methods=["POST"])
def process():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Dosya yok"}), 400

    video_file = request.files['file']
    uid = str(uuid.uuid4())
    input_file = f"/tmp/{uid}_in.mp4"
    output_video = f"/tmp/{uid}_out.mp4"
    output_audio = f"/tmp/{uid}_out.mp3" # Ses dosyası yolu

    video_file.save(input_file)

    # 1. Instagram için Videoyu İşle
    video_cmd = [
        "ffmpeg", "-y", "-i", input_file,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", output_video
    ]
    
    # 2. Ses Dosyasını Ayır (Sadece Ses)
    audio_cmd = ["ffmpeg", "-y", "-i", input_file, "-vn", "-acodec", "libmp3lame", output_audio]

    try:
        subprocess.run(video_cmd, check=True)
        subprocess.run(audio_cmd, check=True)
        
        # R2'ye ikisini de yükle
        upload_to_r2(output_video, f"{uid}.mp4")
        upload_to_r2(output_audio, f"{uid}.mp3")

        # Temizlik
        os.remove(input_file); os.remove(output_video); os.remove(output_audio)

        return jsonify({
            "status": "ok",
            "video_url": f"https://pub-{R2_ACCOUNT_ID}.r2.dev/{uid}.mp4",
            "audio_url": f"https://pub-{R2_ACCOUNT_ID}.r2.dev/{uid}.mp3" # Yeni ses linki
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
