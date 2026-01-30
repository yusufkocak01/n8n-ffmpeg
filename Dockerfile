FROM n8nio/n8n:1.33.2

USER root

# ffmpeg + basic tools
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

USER node
