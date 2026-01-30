FROM node:20-bookworm

# sistem paketleri
RUN apt-get update && \
    apt-get install -y ffmpeg curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# n8n kur
RUN npm install -g n8n

# n8n port
EXPOSE 5678

# start
CMD ["n8n"]
