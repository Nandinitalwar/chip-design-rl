FROM node:22-bookworm-slim@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5
RUN apt-get update && apt-get install -y --no-install-recommends iverilog bash coreutils curl ca-certificates ripgrep && rm -rf /var/lib/apt/lists/*
RUN npm install -g @openai/codex@0.153.4 && npm cache clean --force
WORKDIR /app
COPY repo/ /app/
